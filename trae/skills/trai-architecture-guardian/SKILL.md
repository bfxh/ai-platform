---
name: "trai-architecture-guardian"
description: "架构守护者。保护\python核心架构文件，自动备份修改前的文件到CC/2_Old，验证JM/BC/Tools分类规则。Invoke when files need to be modified, created, or moved in \python."
---

# 架构守护者

## 核心职责

### 1. 受保护文件监控
```python
PROTECTED_FILES = [
    "/python/.gstack_protected",      # 极高保护
    "/python/AGENTS.md",              # 高保护
    "/python/index.json",             # 高保护
    "/python/ai_architecture.json",   # 高保护
    "/python/GStack_Project.json",    # 高保护
    "/python/.trae/project_rules.md", # 中保护
    "/python/.trae/user_rules.md",    # 中保护
]
```

### 2. 修改前自动备份
```python
def backup_before_modify(file_path: str, reason: str = "manual"):
    """修改前自动备份到 CC/2_Old"""
    from datetime import datetime
    import shutil
    
    source = Path(file_path)
    if not source.exists():
        return {'success': False, 'error': '文件不存在'}
    
    # 构建备份路径
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{source.stem}_{timestamp}{source.suffix}"
    backup_dir = Path("/python/CC/2_Old")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    backup_path = backup_dir / backup_name
    
    # 复制文件
    shutil.copy2(source, backup_path)
    
    # 更新索引
    index_path = backup_dir / "INDEX.md"
    with open(index_path, "a", encoding="utf-8") as f:
        f.write(f"\n- [{timestamp}] {backup_name} (原因: {reason}, 原路径: {file_path})")
    
    return {
        'success': True,
        'backup_path': str(backup_path),
        'timestamp': timestamp
    }
```

### 3. 文件分类验证
```python
def validate_classification(filename: str, target_dir: str) -> dict:
    """验证文件分类是否正确"""
    
    filename_lower = filename.lower()
    
    # JM 关键词
    jm_keywords = ["blender", "3d", "model", "mesh", "texture", "animation",
                   "scene", "character", "ue", "unity", "godot", "vision"]
    
    # BC 关键词
    bc_keywords = ["code", "github", "git", "find", "fix", "patch",
                   "verify", "search", "workflow", "dev", "lint"]
    
    # 判断正确分类
    correct_category = "Tools"  # 默认
    for kw in jm_keywords:
        if kw in filename_lower:
            correct_category = "JM"
            break
    for kw in bc_keywords:
        if kw in filename_lower:
            correct_category = "BC"
            break
    
    # 验证目标目录
    target_category = None
    if "MCP/JM" in target_dir or "MCP\\JM" in target_dir:
        target_category = "JM"
    elif "MCP/BC" in target_dir or "MCP\\BC" in target_dir:
        target_category = "BC"
    elif "MCP/Tools" in target_dir or "MCP\\Tools" in target_dir:
        target_category = "Tools"
    
    is_correct = correct_category == target_category
    
    return {
        'filename': filename,
        'correct_category': correct_category,
        'target_category': target_category,
        'is_correct': is_correct,
        'suggestion': f"建议移动到 /python/MCP/{correct_category}/" if not is_correct else "分类正确"
    }
```

### 4. 架构完整性检查
```python
def check_architecture_integrity():
    """检查架构完整性"""
    
    required_dirs = [
        "/python/gstack_core",
        "/python/MCP/JM",
        "/python/MCP/BC",
        "/python/MCP/Tools",
        "/python/MCP_Core",
        "/python/CC/1_Raw",
        "/python/CC/2_Old",
        "/python/CC/3_Unused",
        "/python/CLL_Projects",
        "/python/scripts",
        "/python/logs"
    ]
    
    required_files = [
        "/python/.gstack_protected",
        "/python/AGENTS.md",
        "/python/index.json",
        "/python/ai_architecture.json"
    ]
    
    results = {
        'dirs': {},
        'files': {},
        'overall': True
    }
    
    for d in required_dirs:
        exists = Path(d).exists()
        results['dirs'][d] = exists
        if not exists:
            results['overall'] = False
    
    for f in required_files:
        exists = Path(f).exists()
        results['files'][f] = exists
        if not exists:
            results['overall'] = False
    
    return results
```

## 保护规则

### 必须遵守 (MUST)
1. **必须**在修改受保护文件前备份到 CC/2_Old
2. **必须**将新 MCP 文件按 JM/BC/Tools 分类存放
3. **必须**更新 CC 索引文件当移动文件时
4. **必须**使用环境变量存储敏感信息

### 禁止 (MUST NOT)
1. **禁止**修改 `.gstack_protected` 文件
2. **禁止**直接删除 CC 目录中的文件
3. **禁止**在 JM 目录存放代码类文件
4. **禁止**在 BC 目录存放建模类文件

## 自动修复

### 目录缺失
```python
def fix_missing_dirs():
    """自动创建缺失的目录"""
    required_dirs = [
        "/python/gstack_core",
        "/python/MCP/JM",
        "/python/MCP/BC",
        "/python/MCP/Tools",
        "/python/MCP_Core",
        "/python/CC/1_Raw",
        "/python/CC/2_Old",
        "/python/CC/3_Unused",
        "/python/CLL_Projects",
        "/python/scripts",
        "/python/logs"
    ]
    
    created = []
    for d in required_dirs:
        path = Path(d)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(d)
    
    return created
```

### 保护文件缺失
```python
def fix_protected_files():
    """自动创建缺失的保护文件"""
    
    # .gstack_protected
    protected = Path("/python/.gstack_protected")
    if not protected.exists():
        protected.write_text("GSTACK_ARCHITECTURE_PROTECTED=true\nPROTECTION_VERSION=1.0\n")
    
    # index.json
    index = Path("/python/index.json")
    if not index.exists():
        index.write_text(json.dumps({
            "version": "2.1",
            "structure": {
                "MCP": {"JM": "建模", "BC": "代码", "Tools": "工具"},
                "CLL_Projects": "44个开源项目",
                "Skills": "工作流和技能",
                "gstack_core": "GSTACK 核心",
                "MCP_Core": "MCP 核心系统"
            }
        }, indent=2, ensure_ascii=False))
```
