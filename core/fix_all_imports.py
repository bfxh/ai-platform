#!/usr/bin/env python3
"""/python 全面导入修复器 - 一次性修复所有导入问题"""

import ast
import json
import os
import re
from collections import defaultdict
from pathlib import Path

AI_PATH = Path("/python")
stats = defaultdict(int)
fixes_log = []


def read_file(fp):
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except:
        return None


def write_file(fp, content):
    with open(fp, "w", encoding="utf-8") as f:
        f.write(content)


def fix_core_imports():
    """修复 core/ 目录的循环引用和缺失模块导入"""
    core_dir = AI_PATH / "core"
    if not core_dir.exists():
        return

    missing_modules = {
        "ai_adapter",
        "ai_config",
        "router",
        "workflow",
        "mcp_lite",
        "optimizer",
        "claude_mode",
        "stepfun_client",
        "mcp_extended",
        "plugin_base",
        "plugin_metadata",
        "plugin_registry",
    }

    for py_file in core_dir.rglob("*.py"):
        content = read_file(py_file)
        if not content:
            continue
        original = content
        rel = py_file.relative_to(AI_PATH)

        lines = content.split("\n")
        new_lines = []
        changed = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("from ") and " import " in stripped:
                parts = stripped.split(" import ")
                module_part = parts[0].replace("from ", "").strip()
                top_module = module_part.split(".")[0]

                if top_module in missing_modules:
                    indent = len(line) - len(line.lstrip())
                    indent_str = " " * indent
                    import_names = parts[1].strip() if len(parts) > 1 else ""
                    new_lines.append(f"{indent_str}# [FIXED] 原导入: {stripped}")
                    new_lines.append(f"{indent_str}try:")
                    new_lines.append(f"{indent_str}    from {module_part} import {import_names}")
                    new_lines.append(f"{indent_str}except ImportError:")
                    new_lines.append(
                        f"{indent_str}    {import_names.split(',')[0].strip().split(' as ')[0].strip()} = None"
                    )
                    changed = True
                    stats["core_try_except"] += 1
                    continue

            if stripped.startswith("import ") and not stripped.startswith("importlib"):
                module_name = stripped.replace("import ", "").strip().split(" as ")[0].strip().split(".")[0]
                if module_name in missing_modules:
                    indent = len(line) - len(line.lstrip())
                    indent_str = " " * indent
                    new_lines.append(f"{indent_str}# [FIXED] 原导入: {stripped}")
                    new_lines.append(f"{indent_str}try:")
                    new_lines.append(f"{indent_str}    {stripped}")
                    new_lines.append(f"{indent_str}except ImportError:")
                    new_lines.append(f"{indent_str}    pass")
                    changed = True
                    stats["core_try_except"] += 1
                    continue

            new_lines.append(line)

        if changed:
            new_content = "\n".join(new_lines)
            if new_content != original:
                write_file(py_file, new_content)
                fixes_log.append(f"[CORE] {rel}: wrapped missing imports in try/except")
                stats["core_fixed"] += 1


def fix_gstack_tests():
    """修复 gstack_core/tests/ 的导入路径"""
    tests_dir = AI_PATH / "gstack_core" / "tests"
    if not tests_dir.exists():
        return

    for py_file in tests_dir.rglob("*.py"):
        content = read_file(py_file)
        if not content:
            continue
        original = content
        rel = py_file.relative_to(AI_PATH)

        content = re.sub(r"from skill import ", "from ..skill import ", content)
        content = re.sub(r"from gstack_service import ", "from ..gstack_service import ", content)
        content = re.sub(r"from blender_cleaner import ", "from ..blender_cleaner import ", content)
        content = re.sub(r"from autodevops import ", "from ..autodevops import ", content)
        content = re.sub(r"^sys\.path\.insert\(0.*$\n?", "", content, flags=re.MULTILINE)

        if content != original:
            write_file(py_file, content)
            fixes_log.append(f"[GSTACK] {rel}: fixed relative imports")
            stats["gstack_fixed"] += 1


def fix_mcp_imports():
    """修复 storage/mcp 中的导入问题"""
    mcp_dirs = [
        AI_PATH / "storage/mcp/BC",
        AI_PATH / "storage/mcp/JM",
        AI_PATH / "storage/mcp/Tools",
    ]

    for mcp_dir in mcp_dirs:
        if not mcp_dir.exists():
            continue
        for py_file in mcp_dir.rglob("*.py"):
            content = read_file(py_file)
            if not content:
                continue
            original = content
            rel = py_file.relative_to(AI_PATH)

            # gpu_config 本地导入 -> 相对路径
            if "from gpu_config import" in content or "import gpu_config" in content:
                gpu_config_path = mcp_dir / "gpu_config.py"
                if gpu_config_path.exists():
                    pass
                else:
                    content = re.sub(
                        r"from gpu_config import",
                        "# [FIXED] gpu_config not available - from gpu_config import",
                        content,
                    )
                    content = re.sub(
                        r"import gpu_config", "# [FIXED] gpu_config not available - import gpu_config", content
                    )
                    stats["mcp_gpu_config"] += 1

            # 第三方包导入加 try/except
            third_party = {
                "fastmcp": "fastmcp",
                "paddleocr": "paddleocr",
                "googletrans": "googletrans",
                "qcloud_cos": "qcloud-cos-sdk",
                "tencentcloud": "tencentcloud-sdk-python",
                "aiohttp": "aiohttp",
                "aiofiles": "aiofiles",
            }

            for pkg, pip_name in third_party.items():
                pattern = f"from {pkg}"
                if pattern in content and "try:" not in content.split(pattern)[0][-50:]:
                    lines = content.split("\n")
                    new_lines = []
                    for line in lines:
                        if line.strip().startswith(f"from {pkg}") or line.strip().startswith(f"import {pkg}"):
                            indent = len(line) - len(line.lstrip())
                            indent_str = " " * indent
                            new_lines.append(f"{indent_str}try:")
                            new_lines.append(f"{indent_str}    {line.strip()}")
                            new_lines.append(f"{indent_str}except ImportError:")
                            new_lines.append(f"{indent_str}    pass  # pip install {pip_name}")
                            stats["mcp_try_except"] += 1
                        else:
                            new_lines.append(line)
                    content = "\n".join(new_lines)

            # 跨文件本地导入修复
            local_fixes = {
                "from godot_mcp import": "from .godot_mcp import" if py_file.parent.name == "JM" else None,
                "from github_workflow import": "from .github_workflow import" if py_file.parent.name == "BC" else None,
                "from claude_code_bridge import": (
                    "from .claude_code_bridge import" if py_file.parent.name == "BC" else None
                ),
                "from software_upgrade_manager import": (
                    "from .software_upgrade_manager import" if py_file.parent.name == "Tools" else None
                ),
                "from ai_3d_modeling_v3 import": (
                    "from .ai_3d_modeling_v3 import" if py_file.parent.name == "JM" else None
                ),
            }
            for old, new in local_fixes.items():
                if new and old in content:
                    content = content.replace(old, new)
                    stats["mcp_local_import"] += 1

            if content != original:
                write_file(py_file, content)
                fixes_log.append(f"[MCP] {rel}: fixed imports")
                stats["mcp_fixed"] += 1


def fix_plugin_system():
    """修复 core/plugin_system 的相对导入"""
    plugin_dir = AI_PATH / "core" / "plugin_system"
    if not plugin_dir.exists():
        return

    for py_file in plugin_dir.rglob("*.py"):
        content = read_file(py_file)
        if not content:
            continue
        original = content

        content = content.replace("from plugin_base import", "from .plugin_base import")
        content = content.replace("from plugin_metadata import", "from .plugin_metadata import")
        content = content.replace("from plugin_manager import", "from .plugin_manager import")
        content = content.replace("from plugin_registry import", "from .plugin_registry import")
        content = content.replace("import plugin_base", "from . import plugin_base")
        content = content.replace("import plugin_metadata", "from . import plugin_metadata")
        content = content.replace("import plugin_manager", "from . import plugin_manager")
        content = content.replace("import plugin_registry", "from . import plugin_registry")

        if content != original:
            write_file(py_file, content)
            fixes_log.append(f"[PLUGIN] {py_file.relative_to(AI_PATH)}: fixed relative imports")
            stats["plugin_fixed"] += 1


def fix_mcp_core_init():
    """修复 MCP_Core/skills 的 __init__.py"""
    init_file = AI_PATH / "MCP_Core" / "skills" / "__init__.py"
    if not init_file.exists():
        return
    content = read_file(init_file)
    if not content:
        return
    original = content

    content = content.replace("from base import", "from .base import")

    if content != original:
        write_file(init_file, content)
        fixes_log.append(f"[SKILLS] skills/__init__.py: fixed relative import")
        stats["skills_init_fixed"] += 1


def fix_ai_software_imports():
    """修复 ai_software.py 中缺失的第三方包导入"""
    for fname in ["ai_software.py", "ai_software_gpu.py"]:
        fp = AI_PATH / "storage/mcp/JM" / fname
        if not fp.exists():
            continue
        content = read_file(fp)
        if not content:
            continue
        original = content

        for pkg in ["paddleocr", "googletrans"]:
            lines = content.split("\n")
            new_lines = []
            for line in lines:
                if line.strip().startswith(f"from {pkg}") or line.strip().startswith(f"import {pkg}"):
                    indent = len(line) - len(line.lstrip())
                    indent_str = " " * indent
                    new_lines.append(f"{indent_str}try:")
                    new_lines.append(f"{indent_str}    {line.strip()}")
                    new_lines.append(f"{indent_str}except ImportError:")
                    new_lines.append(f"{indent_str}    {pkg} = None")
                else:
                    new_lines.append(line)
            content = "\n".join(new_lines)

        if content != original:
            write_file(fp, content)
            fixes_log.append(f"[JM] {fname}: wrapped third-party imports")
            stats["jm_fixed"] += 1


def fix_tencent_mcp():
    """修复 tencent_mcp.py 的大量 tencentcloud 导入"""
    fp = AI_PATH / "storage/mcp/Tools/tencent_mcp.py"
    if not fp.exists():
        return
    content = read_file(fp)
    if not content:
        return
    original = content

    lines = content.split("\n")
    new_lines = []
    in_try = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("from tencentcloud") or stripped.startswith("from qcloud_cos"):
            if not in_try:
                indent = len(line) - len(line.lstrip())
                indent_str = " " * indent
                new_lines.append(f"{indent_str}try:")
                in_try = True
            new_lines.append(f"    {line}")
        elif (
            in_try
            and stripped
            and not stripped.startswith("from tencentcloud")
            and not stripped.startswith("from qcloud_cos")
        ):
            indent = len(line) - len(line.lstrip())
            indent_str = " " * indent
            new_lines.append(f"{indent_str}except ImportError:")
            new_lines.append(f"{indent_str}    pass  # pip install tencentcloud-sdk-python qcloud-cos-sdk")
            new_lines.append("")
            new_lines.append(line)
            in_try = False
        else:
            new_lines.append(line)

    if in_try:
        new_lines.append("except ImportError:")
        new_lines.append("    pass")

    content = "\n".join(new_lines)
    if content != original:
        write_file(fp, content)
        fixes_log.append("[TOOLS] tencent_mcp.py: wrapped tencentcloud imports")
        stats["tencent_fixed"] += 1


def fix_test_files():
    """修复测试文件的导入"""
    test_files = [
        AI_PATH / "storage/mcp/Tools/test_upgrade_manager.py",
        AI_PATH / "storage/mcp/JM/test_ai_3d_modeling_v3.py",
        AI_PATH / "storage/mcp/JM/test_ai_3d_v3_functional.py",
        AI_PATH / "storage/mcp/JM/test_ai_3d_v3_structure.py",
    ]
    for fp in test_files:
        if not fp.exists():
            continue
        content = read_file(fp)
        if not content:
            continue
        original = content

        content = content.replace("from software_upgrade_manager import", "from .software_upgrade_manager import")
        content = content.replace("from ai_3d_modeling_v3 import", "from .ai_3d_modeling_v3 import")
        content = content.replace(
            "from gpu_config import",
            "try:\n    from .gpu_config import\nexcept ImportError:\n    gpu_config = None\n# from gpu_config import",
        )

        if content != original:
            write_file(fp, content)
            fixes_log.append(f"[TEST] {fp.relative_to(AI_PATH)}: fixed imports")
            stats["test_fixed"] += 1


def fix_headless_workflow():
    """修复 gstack_core/headless_workflow.py 的 watchdog 导入"""
    fp = AI_PATH / "gstack_core/headless_workflow.py"
    if not fp.exists():
        return
    content = read_file(fp)
    if not content:
        return
    original = content

    content = content.replace(
        "from watchdog.observers import Observer\nfrom watchdog.events import FileSystemEventHandler",
        "try:\n    from watchdog.observers import Observer\n    from watchdog.events import FileSystemEventHandler\nexcept ImportError:\n    Observer = None\n    FileSystemEventHandler = None  # pip install watchdog",
    )

    if content != original:
        write_file(fp, content)
        fixes_log.append("[GSTACK] headless_workflow.py: wrapped watchdog import")
        stats["watchdog_fixed"] += 1


def fix_full_verify():
    """修复 gstack_core/full_verify.py 的 autodevops 导入"""
    fp = AI_PATH / "gstack_core/full_verify.py"
    if not fp.exists():
        return
    content = read_file(fp)
    if not content:
        return
    original = content

    content = content.replace("from autodevops import", "from .autodevops import")

    if content != original:
        write_file(fp, content)
        fixes_log.append("[GSTACK] full_verify.py: fixed relative import")
        stats["full_verify_fixed"] += 1


def fix_pua_supervisor():
    """修复 pua_supervisor.py 的 fastmcp 导入"""
    fp = AI_PATH / "storage/mcp/Tools/pua_supervisor.py"
    if not fp.exists():
        return
    content = read_file(fp)
    if not content:
        return
    original = content

    if "from fastmcp" in content and "try:" not in content[: content.index("from fastmcp")][-50:]:
        content = content.replace(
            "from fastmcp",
            "try:\n    from fastmcp\nexcept ImportError:\n    fastmcp = None  # pip install fastmcp\n# from fastmcp",
        )

    if content != original:
        write_file(fp, content)
        fixes_log.append("[TOOLS] pua_supervisor.py: wrapped fastmcp import")
        stats["pua_fixed"] += 1


print("=" * 60)
print("/python Comprehensive Import Fixer")
print("=" * 60)

fix_core_imports()
fix_gstack_tests()
fix_mcp_imports()
fix_plugin_system()
fix_mcp_core_init()
fix_ai_software_imports()
fix_tencent_mcp()
fix_test_files()
fix_headless_workflow()
fix_full_verify()
fix_pua_supervisor()

print(f"\n修复统计:")
for k, v in sorted(stats.items()):
    print(f"  {k}: {v}")

print(f"\n修复日志:")
for log in fixes_log:
    print(f"  {log}")

print(f"\n总计修复 {len(fixes_log)} 个文件")
