---
name: "trai-skill-loader"
description: "技能自动加载器。扫描并加载\python\MCP_Core\skills目录下所有技能，自动修复导入错误，确保所有技能可用。Invoke when skills need to be loaded, refreshed, or when skill errors occur."
---

# 技能自动加载器

## 加载流程

### 1. 扫描技能目录
```python
def scan_skills():
    """扫描所有可用技能"""
    skills_dir = Path("/python/MCP_Core/skills")
    skills = []
    
    for item in skills_dir.iterdir():
        if item.is_dir() and item.name not in ['__pycache__']:
            skill_file = item / "skill.py"
            if skill_file.exists():
                skills.append(item.name)
    
    return skills
```

### 2. 自动修复导入
```python
def fix_imports(skill_name: str):
    """自动修复技能的导入语句"""
    skill_file = Path(f"/python/MCP_Core/skills/{skill_name}/skill.py")
    
    if not skill_file.exists():
        return False
    
    content = skill_file.read_text(encoding='utf-8')
    
    # 修复常见的导入错误
    fixes = [
        ('from MCP_Core.skills.base import', 'from skills.base import'),
        ('from MCP_Core.skills.base import SkillBase', 'from skills.base import SkillBase'),
        ('import fnmatch\n# 导入fnmatch模块', 'import fnmatch'),
    ]
    
    for old, new in fixes:
        content = content.replace(old, new)
    
    skill_file.write_text(content, encoding='utf-8')
    return True
```

### 3. 添加缺失属性
```python
def add_missing_attributes(skill_name: str):
    """为技能添加缺失的类级属性"""
    skill_file = Path(f"/python/MCP_Core/skills/{skill_name}/skill.py")
    
    content = skill_file.read_text(encoding='utf-8')
    
    # 检查是否有 name 属性
    if 'name =' not in content and 'name=' not in content:
        # 在 class 定义后添加属性
        content = content.replace(
            f"class {skill_name.title().replace('_', '')}Skill(SkillBase):",
            f"class {skill_name.title().replace('_', '')}Skill(SkillBase):\n    name = \"{skill_name}\"\n    description = \"自动生成的描述\"\n    version = \"1.0.0\"\n    author = \"MCP Core Team\""
        )
    
    skill_file.write_text(content, encoding='utf-8')
```

### 4. 批量加载
```python
def load_all_skills():
    """加载所有技能"""
    from skills.base import get_registry
    registry = get_registry()
    
    skill_names = scan_skills()
    loaded = []
    failed = []
    
    for name in skill_names:
        try:
            # 先尝试修复
            fix_imports(name)
            add_missing_attributes(name)
            
            # 然后加载
            module = importlib.import_module(f"skills.{name}.skill")
            for attr in dir(module):
                obj = getattr(module, attr)
                if (isinstance(obj, type) and 
                    issubclass(obj, Skill) and 
                    obj != Skill and
                    getattr(obj, 'name', '')):
                    registry.register(obj)
                    loaded.append(name)
                    break
        except Exception as e:
            failed.append((name, str(e)))
    
    return {
        'loaded': loaded,
        'failed': failed,
        'total': len(skill_names)
    }
```

## 技能状态监控

### 实时监控
```python
def monitor_skills():
    """监控技能状态"""
    registry = get_registry()
    skills = registry.list()
    
    status = {
        'total': len(skills),
        'loaded': sum(1 for s in skills if s['is_loaded']),
        'failed': [],
        'actions': sum(len(s['actions']) for s in skills)
    }
    
    for skill in skills:
        if not skill['is_loaded']:
            status['failed'].append(skill['name'])
    
    return status
```

### 自动恢复
```python
def auto_recover():
    """自动恢复失败的技能"""
    status = monitor_skills()
    recovered = []
    
    for name in status['failed']:
        try:
            fix_imports(name)
            add_missing_attributes(name)
            
            registry = get_registry()
            skill = registry.get(name)
            if skill:
                recovered.append(name)
        except Exception as e:
            print(f"[FAIL] 无法恢复 {name}: {e}")
    
    return recovered
```

## 技能分类

### 按功能分类
```python
skill_categories = {
    'github': ['github_api_manager', 'github_project_search', 'github_actions_manager'],
    'system': ['system_optimizer', 'background_process_manager', 'software_location_manager'],
    'automation': ['automated_workflow', 'automated_testing', 'continuous_integration'],
    'ai': ['claude_code', 'mempalace', 'open_webui'],
    'platform': ['dify_platform', 'n8n_workflow', 'java_guide']
}
```

### 按优先级分类
```python
skill_priority = {
    'P0': ['github_api_manager', 'automated_testing', 'system_optimizer'],
    'P1': ['github_project_search', 'automated_workflow', 'continuous_integration'],
    'P2': ['claude_code', 'mempalace', 'open_webui'],
    'P3': ['dify_platform', 'n8n_workflow', 'java_guide']
}
```
