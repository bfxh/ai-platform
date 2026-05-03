---
name: "trai-ai-os"
description: "\python AI操作系统适配器。在每次对话开始时自动检查GSTACK状态、加载技能、验证架构完整性。Invoke when conversation starts or when user mentions \python, GSTACK, MCP, or skills."
---

# \python AI 操作系统适配器

## 核心职责

在每次对话开始时，自动执行以下检查：

### 1. GSTACK 状态检查
```python
# 必须执行
import sys
sys.path.insert(0, "/python")
sys.path.insert(0, "/python/gstack_core")
sys.path.insert(0, "/python/MCP_Core")

try:
    from gstack_core import GStackCore
    gstack = GStackCore()
    print("[OK] GSTACK 可用")
except ImportError:
    print("[FAIL] GSTACK 不可用 - 进入降级模式")
```

### 2. 技能系统自动加载
```python
# 自动加载所有已注册技能
from skills.base import get_registry
registry = get_registry()
skills = registry.list()
print(f"[OK] 已加载 {len(skills)} 个技能")
```

### 3. 架构完整性验证
检查以下核心路径是否存在：
- `/python/gstack_core`
- `/python/MCP/JM`
- `/python/MCP/BC`
- `/python/MCP/Tools`
- `/python/MCP_Core`
- `/python/CC/1_Raw`
- `/python/CC/2_Old`
- `/python/CC/3_Unused`

### 4. 受保护文件检查
```python
protected_files = [
    "/python/.gstack_protected",
    "/python/AGENTS.md",
    "/python/index.json",
    "/python/ai_architecture.json"
]
for f in protected_files:
    if Path(f).exists():
        print(f"[OK] {f}")
    else:
        print(f"[WARN] {f} 缺失")
```

## 工作流程优先级

1. **GSTACK 优先**: 所有任务优先使用 GSTACK 工作流
2. **ASK 技能系统**: 次选，通用技能调用
3. **Python 脚本**: 直接调用已验证脚本
4. **PowerShell 脚本**: 系统级操作
5. **MCP 服务器**: 外部工具集成

## 文件分类规则

- **JM (建模)**: Blender, 3D, UE5, Unity, Godot → `/python/MCP/JM/`
- **BC (代码)**: GitHub, 代码分析, 搜索修复 → `/python/MCP/BC/`
- **Tools (工具)**: 下载, 监控, 配置 → `/python/MCP/Tools/`

## 错误处理

### GSTACK 不可用
```
[FAIL] GSTACK 不可用
进入降级模式 (strict)
仅提供只读服务
```

### 技能加载失败
```
[FAIL] 技能 {name} 加载失败: {error}
跳过该技能，继续加载其他
```

## 上下文维护

在对话过程中维护以下上下文：
- `gstack_available`: GSTACK 是否可用
- `skills_loaded`: 已加载的技能列表
- `current_mode`: 当前模式 (normal/strict/legacy)
- `protected_paths`: 受保护文件路径列表

## 用户规则集成

严格遵守 `/python/.trae/user_rules.md` 中的规则：
1. 严禁简化架构
2. 禁止直接修改 \python\*.json
3. 禁止跳过 GSTACK 直接给 PowerShell 命令
4. 每次对话必须检查 GSTACK 可用性
