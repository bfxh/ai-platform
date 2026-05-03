---
name: "trai-gstack-executor"
description: "GSTACK工作流执行器。自动检查GSTACK可用性，执行工作流命令，处理降级模式。Invoke when user mentions GSTACK, gstack, or any GSTACK command like review, ship, qa, etc."
---

# GSTACK 工作流执行器

## 执行流程

### 1. 前置检查
```python
def pre_check():
    """执行前的必要检查"""
    checks = {
        'gstack_available': False,
        'protected_intact': False,
        'skills_ready': False
    }
    
    # 检查 GSTACK
    try:
        from gstack_core import GStackCore
        gstack = GStackCore()
        checks['gstack_available'] = True
    except:
        pass
    
    # 检查保护文件
    protected = Path("/python/.gstack_protected")
    checks['protected_intact'] = protected.exists()
    
    # 检查技能
    try:
        from skills.base import get_registry
        registry = get_registry()
        checks['skills_ready'] = len(registry.list()) > 0
    except:
        pass
    
    return checks
```

### 2. 命令执行
```python
def execute_gstack(command: str, params: dict = None):
    """执行 GSTACK 命令"""
    checks = pre_check()
    
    if not checks['gstack_available']:
        return {
            'success': False,
            'error': 'GSTACK 不可用',
            'fallback': '使用 legacy 模式',
            'checks': checks
        }
    
    try:
        from gstack_core import GStackCore
        gstack = GStackCore()
        result = gstack.execute(command, params or {})
        return {
            'success': True,
            'data': result,
            'checks': checks
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
            'checks': checks
        }
```

### 3. 降级处理
```python
def handle_fallback(command: str, params: dict = None):
    """GSTACK 不可用时的降级处理"""
    
    # 尝试使用 Python 脚本
    script_map = {
        'review': '/python/MCP/BC/code_quality.py',
        'ship': '/python/scripts/deploy.py',
        'qa': '/python/MCP/BC/verify_one.py'
    }
    
    if command in script_map:
        script = script_map[command]
        if Path(script).exists():
            return execute_script(script, params)
    
    # 尝试使用 PowerShell
    ps_map = {
        'git:status': 'git status',
        'cc_cleanup': '/python/scripts/cleanup.ps1'
    }
    
    if command in ps_map:
        return execute_powershell(ps_map[command])
    
    # 最终降级：返回错误信息
    return {
        'success': False,
        'error': f'GSTACK 命令 "{command}" 无法执行',
        'suggestion': '请检查 GSTACK 安装或手动执行'
    }
```

## 支持的命令

### 产品验证类
- `office_hours` - YC 风格产品验证
- `plan_ceo_review` - CEO 视角评审
- `plan_eng_review` - 工程架构评审

### 代码质量类
- `review` - 代码审查
- `investigate` - 根因分析
- `qa` - 测试+自动修复
- `lint` - 代码质量检查

### 部署发布类
- `ship` - 自动化部署
- `document_release` - 更新文档

### 安全保护类
- `careful` - 危险警告
- `freeze` - 文件锁定
- `guard` - 完全安全模式

### 系统维护类
- `skill_doctor` - Skills 自检
- `cc_cleanup` - CC 缓存清理
- `git:status` - Git 状态检查

## 错误处理

### GSTACK 不可用
```
[FAIL] GSTACK 不可用
[CHECK] 保护文件: OK
[CHECK] 技能系统: OK
[FALLBACK] 使用 Python 脚本替代
```

### 命令不存在
```
[FAIL] 未知命令: {command}
[HELP] 可用命令: review, ship, qa, lint, ...
[SUGGEST] 您是否想执行: {similar_command}
```

### 执行失败
```
[FAIL] 命令执行失败
[ERROR] {error_message}
[TRACE] {traceback}
[RECOVER] 尝试恢复...
```
