---
name: "trai-error-recovery"
description: "错误恢复系统。捕获并分类错误，自动尝试修复，提供降级方案，确保系统稳定运行。Invoke when errors occur, skills fail to load, or system exceptions happen."
---

# 错误恢复系统

## 错误分类

### 1. 技能加载错误
```python
class SkillLoadError(Exception):
    """技能加载错误"""
    def __init__(self, skill_name, error_type, message):
        self.skill_name = skill_name
        self.error_type = error_type  # 'import', 'syntax', 'attribute', 'config'
        self.message = message
        super().__init__(f"[{error_type}] 技能 {skill_name} 加载失败: {message}")
```

### 2. GSTACK 错误
```python
class GSTACKError(Exception):
    """GSTACK 错误"""
    def __init__(self, command, error_code, message):
        self.command = command
        self.error_code = error_code  # 'UNAVAILABLE', 'UNKNOWN_COMMAND', 'EXECUTION_FAILED'
        self.message = message
        super().__init__(f"[{error_code}] GSTACK 命令 {command} 失败: {message}")
```

### 3. 架构错误
```python
class ArchitectureError(Exception):
    """架构错误"""
    def __init__(self, file_path, error_type, message):
        self.file_path = file_path
        self.error_type = error_type  # 'PROTECTED', 'MISSING', 'CORRUPTED', 'MISCLASSIFIED'
        self.message = message
        super().__init__(f"[{error_type}] 架构错误 {file_path}: {message}")
```

## 自动修复策略

### 1. 技能加载错误修复
```python
def fix_skill_load_error(error: SkillLoadError) -> dict:
    """修复技能加载错误"""
    
    fixes = {
        'import': lambda: fix_import_error(error.skill_name),
        'syntax': lambda: fix_syntax_error(error.skill_name),
        'attribute': lambda: fix_attribute_error(error.skill_name),
        'config': lambda: fix_config_error(error.skill_name)
    }
    
    if error.error_type in fixes:
        return fixes[error.error_type]()
    
    return {'success': False, 'error': f'未知错误类型: {error.error_type}'}

def fix_import_error(skill_name: str):
    """修复导入错误"""
    skill_file = Path(f"/python/MCP_Core/skills/{skill_name}/skill.py")
    content = skill_file.read_text(encoding='utf-8')
    
    # 修复常见的导入错误
    replacements = [
        ('from MCP_Core.skills.base import', 'from skills.base import'),
        ('from MCP_Core.skills.base import SkillBase', 'from skills.base import SkillBase'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    skill_file.write_text(content, encoding='utf-8')
    return {'success': True, 'fixed': 'import'}

def fix_attribute_error(skill_name: str):
    """修复属性错误"""
    skill_file = Path(f"/python/MCP_Core/skills/{skill_name}/skill.py")
    content = skill_file.read_text(encoding='utf-8')
    
    # 添加缺失的类级属性
    if 'name =' not in content:
        class_name = skill_name.title().replace('_', '') + 'Skill'
        content = content.replace(
            f'class {class_name}(SkillBase):',
            f'class {class_name}(SkillBase):\n    name = "{skill_name}"\n    description = "自动修复的技能"\n    version = "1.0.0"\n    author = "MCP Core Team"'
        )
    
    skill_file.write_text(content, encoding='utf-8')
    return {'success': True, 'fixed': 'attribute'}
```

### 2. GSTACK 错误修复
```python
def fix_gstack_error(error: GSTACKError) -> dict:
    """修复 GSTACK 错误"""
    
    if error.error_code == 'UNAVAILABLE':
        # 尝试重新加载 GSTACK
        try:
            import sys
            sys.path.insert(0, "/python/gstack_core")
            from gstack_core import GStackCore
            gstack = GStackCore()
            return {'success': True, 'fixed': 'reloaded'}
        except:
            return {'success': False, 'fallback': 'legacy_mode'}
    
    elif error.error_code == 'UNKNOWN_COMMAND':
        # 提供相似命令建议
        available_commands = ['review', 'ship', 'qa', 'lint', 'investigate']
        similar = find_similar_command(error.command, available_commands)
        return {
            'success': False,
            'suggestion': f'您是否想执行: {similar}?',
            'available_commands': available_commands
        }
    
    elif error.error_code == 'EXECUTION_FAILED':
        # 尝试使用备选方案
        return try_fallback_command(error.command)
    
    return {'success': False, 'error': '无法修复'}
```

### 3. 架构错误修复
```python
def fix_architecture_error(error: ArchitectureError) -> dict:
    """修复架构错误"""
    
    if error.error_type == 'PROTECTED':
        return {
            'success': False,
            'error': '受保护文件无法自动修复',
            'action': '请手动备份后修改'
        }
    
    elif error.error_type == 'MISSING':
        # 尝试从 CC/2_Old 恢复
        backup_dir = Path("/python/CC/2_Old")
        file_name = Path(error.file_path).name
        
        for backup in backup_dir.glob(f"{file_name}_*"):
            shutil.copy2(backup, error.file_path)
            return {'success': True, 'fixed': 'restored_from_backup'}
        
        return {'success': False, 'error': '未找到备份'}
    
    elif error.error_type == 'MISCLASSIFIED':
        # 自动移动到正确目录
        validation = validate_classification(file_name, target_dir)
        if not validation['is_correct']:
            correct_dir = f"/python/MCP/{validation['correct_category']}"
            shutil.move(error.file_path, correct_dir)
            return {'success': True, 'fixed': 'reclassified', 'new_path': correct_dir}
    
    return {'success': False, 'error': '无法自动修复'}
```

## 降级方案

### 1. GSTACK 降级
```python
def gstack_fallback(command: str, params: dict = None):
    """GSTACK 降级方案"""
    
    # 命令映射
    command_map = {
        'review': {'script': '/python/MCP/BC/code_quality.py', 'type': 'python'},
        'ship': {'script': '/python/scripts/deploy.py', 'type': 'python'},
        'qa': {'script': '/python/MCP/BC/verify_one.py', 'type': 'python'},
        'git:status': {'command': 'git status', 'type': 'shell'}
    }
    
    if command in command_map:
        fallback = command_map[command]
        
        if fallback['type'] == 'python':
            return execute_python_script(fallback['script'], params)
        elif fallback['type'] == 'shell':
            return execute_shell_command(fallback['command'])
    
    return {
        'success': False,
        'error': f'无降级方案 for {command}',
        'suggestion': '请手动执行或使用其他工具'
    }
```

### 2. 技能降级
```python
def skill_fallback(skill_name: str, action: str, params: dict = None):
    """技能降级方案"""
    
    # 尝试使用相似技能
    similar_skills = find_similar_skills(skill_name)
    
    for similar in similar_skills:
        try:
            registry = get_registry()
            result = registry.execute(similar, {
                'action': action,
                **(params or {})
            })
            if result.get('success'):
                return {
                    'success': True,
                    'data': result,
                    'note': f'使用备选技能: {similar}'
                }
        except:
            continue
    
    return {
        'success': False,
        'error': f'技能 {skill_name} 及其备选均不可用'
    }
```

## 错误日志

```python
def log_error(error, context: dict = None):
    """记录错误日志"""
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {},
        'traceback': traceback.format_exc()
    }
    
    log_file = Path(f"/python/logs/error_{datetime.now().strftime('%Y%m%d')}.json")
    
    # 追加到日志文件
    logs = []
    if log_file.exists():
        logs = json.loads(log_file.read_text())
    
    logs.append(log_entry)
    log_file.write_text(json.dumps(logs, indent=2, ensure_ascii=False))
    
    return log_entry
```
