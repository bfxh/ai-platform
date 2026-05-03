#!/usr/bin/env python3
"""修复被上一轮脚本破坏的文件 + 修复剩余转义序列"""

import re
from pathlib import Path

import os
AI_PATH = Path(os.environ.get("AI_BASE_DIR", Path(__file__).resolve().parent.parent))
fixed = []


def fix_multiline_try_except(filepath):
    """修复被错误拆分的 try/except 多行导入"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except:
        return False

    original = content

    # 修复模式: # [FIXED] 原导入: from xxx import (\ntry:\n    from xxx import (\nexcept ImportError:\n    ( = None\n    items,\n)
    pattern = r"# \[FIXED\] 原导入: from (\w+) import \(\ntry:\n    from \1 import \(\nexcept ImportError:\n    \( = None\n(.*?)\)"

    def replacer(m):
        module = m.group(1)
        items = m.group(2).strip()
        return f"""try:
    from {module} import (
        {items}
    )
except ImportError:
    {module} = None"""

    content = re.sub(pattern, replacer, content, flags=re.DOTALL)

    # 修复嵌套 try/except
    content = re.sub(
        r"try:\n    # \[FIXED\] 原导入: from (\w+) import ([^\n]+)\n    try:\n    from \1 import \2\n    except ImportError:\n    \w+ = None",
        r"try:\n    from \1 import \2\nexcept ImportError:\n    \1 = None",
        content,
    )

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def fix_escape_sequences(filepath):
    """修复所有无效转义序列"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except:
        return False

    original = content

    # 在普通字符串中替换 \python -> /python 或 /python
    # 但不要修改 raw string (r"...") 和 f-string 中的正确内容
    lines = content.split("\n")
    new_lines = []

    for line in lines:
        stripped = line.strip()

        # 跳过已经是 raw string 或正则的行
        if stripped.startswith('r"') or stripped.startswith("r'"):
            new_lines.append(line)
            continue

        # 在 Path() 调用中用正斜杠
        if 'Path("D:' in line or "Path('D:" in line:
            line = line.replace('Path("/python', 'Path("/python')
            line = line.replace("Path('/python", "Path('/python")
            line = line.replace('Path("D:\\rj', 'Path("D:/rj')
            line = line.replace("Path('D:\\rj", "Path('D:/rj")
            line = line.replace('Path("D:\\Dev', 'Path("%DEVTOOLS_DIR%')
            line = line.replace("Path('D:\\Dev", "Path('%DEVTOOLS_DIR%")
            line = line.replace('Path("/python\\gstack_core', 'Path("/python/gstack_core')
            line = line.replace('Path("/python\\MCP', 'Path("/python/MCP')

        # 在普通字符串中修复转义
        if '"/python' in line and "Path(" not in line:
            line = line.replace('"/python', '"D:\\\\AI')
        if "'/python" in line and "Path(" not in line:
            line = line.replace("'/python", "'D:\\\\AI")
        if '"D:\\rj' in line and "Path(" not in line:
            line = line.replace('"D:\\rj', '"D:\\\\rj')
        if '"D:\\Dev' in line and "Path(" not in line:
            line = line.replace('"D:\\Dev', '"D:\\\\Dev')
        if '"C:\\Program Files' in line:
            line = line.replace('"C:\\Program Files', '"C:\\\\Program Files')
        if '"C:\\Users' in line:
            line = line.replace('"C:\\Users', '"C:\\\\Users')

        # 修复 docstring 中的转义
        if '"""' in line or "'''" in line:
            line = line.replace("/python", "/python")
            line = line.replace("D:\\Dev", "%DEVTOOLS_DIR%")
            line = line.replace("D:\\rj", "D:/rj")
            line = line.replace("C:\\Program Files", "C:/Program Files")
            line = line.replace("\\*", "*")

        new_lines.append(line)

    content = "\n".join(new_lines)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


# 修复被破坏的多行导入
broken_files = [
    AI_PATH / "core/ai_unified.py",
    AI_PATH / "core/ai.py",
    AI_PATH / "core/ai_agent.py",
    AI_PATH / "core/ai_collaboration.py",
    AI_PATH / "core/ai_config.py",
    AI_PATH / "core/ai_new.py",
    AI_PATH / "core/ai_plugin_system.py",
    AI_PATH / "core/claude_integration.py",
    AI_PATH / "core/claude_mode.py",
    AI_PATH / "core/mcp_lite.py",
    AI_PATH / "core/router.py",
    AI_PATH / "core/workflow.py",
    AI_PATH / "core/workflow_advanced.py",
]

print("Fixing broken multi-line imports...")
for fp in broken_files:
    if fp.exists() and fix_multiline_try_except(fp):
        fixed.append(str(fp.relative_to(AI_PATH)))
        print(f"  Fixed: {fp.relative_to(AI_PATH)}")

# 修复转义序列
print("\nFixing escape sequences...")
scan_dirs = [
    AI_PATH / "core",
    AI_PATH / "MCP_Core",
    AI_PATH / "storage/mcp",
    AI_PATH / "gstack_core",
]

for scan_dir in scan_dirs:
    if not scan_dir.exists():
        continue
    for py_file in scan_dir.rglob("*.py"):
        if fix_escape_sequences(py_file):
            rel = str(py_file.relative_to(AI_PATH))
            if rel not in fixed:
                fixed.append(rel)
                print(f"  Fixed: {rel}")

# 修复 tencent_mcp.py 的 try/except 语法
fp = AI_PATH / "storage/mcp/Tools/tencent_mcp.py"
if fp.exists():
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # 检查是否有未闭合的 try
        if "try:" in content and content.count("try:") > content.count("except"):
            # 重新生成正确的导入结构
            lines = content.split("\n")
            new_lines = []
            in_tc_block = False
            tc_lines = []

            for line in lines:
                stripped = line.strip()
                if stripped.startswith("from tencentcloud") or stripped.startswith("from qcloud_cos"):
                    if not in_tc_block:
                        new_lines.append("try:")
                        in_tc_block = True
                    new_lines.append(f"    {line}")
                elif (
                    in_tc_block
                    and stripped
                    and not stripped.startswith("from tencentcloud")
                    and not stripped.startswith("from qcloud_cos")
                ):
                    new_lines.append("except ImportError:")
                    new_lines.append("    pass  # pip install tencentcloud-sdk-python qcloud-cos-sdk")
                    new_lines.append("")
                    in_tc_block = False
                    new_lines.append(line)
                else:
                    new_lines.append(line)

            if in_tc_block:
                new_lines.append("except ImportError:")
                new_lines.append("    pass")

            content = "\n".join(new_lines)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Fixed: tencent_mcp.py try/except structure")
    except:
        pass

# 修复 test_ai_3d_modeling_v3.py 的 try/except 语法
fp = AI_PATH / "storage/mcp/JM/test_ai_3d_modeling_v3.py"
if fp.exists():
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # 修复被破坏的 try/except
        content = content.replace(
            "try:\n    from .gpu_config import\nexcept ImportError:\n    gpu_config = None\n# from gpu_config import",
            "try:\n    from gpu_config import GPUConfig\nexcept ImportError:\n    GPUConfig = None  # pip install torch",
        )
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Fixed: test_ai_3d_modeling_v3.py")
    except:
        pass

print(f"\nTotal fixed: {len(fixed)} files")
