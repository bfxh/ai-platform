---
name: "trai-context-router"
description: "智能上下文路由器。根据用户输入自动识别意图，路由到正确的技能或工作流。Invoke when user asks for any task that could be handled by \python skills or GSTACK workflows."
---

# 智能上下文路由器

## 路由规则

### 1. 代码相关任务 → BC 技能
```
用户输入包含: code, github, git, find, fix, patch, verify, search, workflow, dev, lint
路由到: /python/MCP/BC/ 或 skills.github_*, skills.code_*
```

### 2. 3D/建模相关任务 → JM 技能
```
用户输入包含: blender, 3d, model, mesh, texture, animation, scene, character, ue, unity, godot
路由到: /python/MCP/JM/ 或 skills.blender_*
```

### 3. 系统/工具相关任务 → Tools 技能
```
用户输入包含: download, network, system, monitor, automation, config, memory, cache
路由到: /python/MCP/Tools/ 或 skills.system_*
```

### 4. 工作流相关任务 → GSTACK
```
用户输入包含: review, ship, deploy, test, qa, lint, investigate
路由到: gstack_core.execute(command, params)
```

## 自动技能发现

```python
def auto_discover_skills(user_input: str) -> list:
    """根据用户输入自动发现相关技能"""
    from skills.base import get_registry
    registry = get_registry()
    all_skills = registry.list()
    
    matched = []
    keywords = user_input.lower().split()
    
    for skill in all_skills:
        score = 0
        skill_text = (skill['name'] + ' ' + skill['description']).lower()
        for kw in keywords:
            if kw in skill_text:
                score += 1
        if score > 0:
            matched.append((skill, score))
    
    # 按匹配度排序
    matched.sort(key=lambda x: x[1], reverse=True)
    return matched[:3]  # 返回前3个最匹配的技能
```

## 上下文感知

维护对话上下文：
- `last_skill`: 上次使用的技能
- `last_category`: 上次处理的分类 (JM/BC/Tools)
- `task_history`: 任务历史记录
- `user_preferences`: 用户偏好设置

## 智能建议

当用户输入模糊时，提供智能建议：
```
用户: "帮我处理一下这个文件"
系统: "检测到模糊请求。请选择：
1. 代码审查 (gstack review)
2. 文件分类 (auto_classify)
3. 备份到CC (backup_file)
"
```

## 错误恢复

当技能调用失败时，自动尝试备选方案：
1. 尝试使用相似技能
2. 降级到 Python 脚本
3. 降级到 PowerShell 脚本
4. 请求用户确认
