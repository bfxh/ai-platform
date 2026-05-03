# MCP Core - 技能集成指南

> 本指南说明如何将新的 MCP 技能、工作流集成到 MCP Core 系统中

---

## 目录结构规范

```
\python\MCP_Core\
├── server.py                    # MCP Server主入口（无需修改）
├── config.py                    # 配置中心（无需修改）
├── event_bus.py                 # 事件总线（无需修改）
│
├── skills\                      # 【技能目录】- 所有新技能放在这里
│   ├── base.py                 # 技能基类（无需修改）
│   ├── __init__.py
│   │
│   ├── network_transfer\        # 示例：网络传输技能
│   │   ├── __init__.py
│   │   └── skill.py            # 【必须】技能实现文件
│   │
│   ├── exo_cluster\             # 示例：EXo集群技能
│   │   ├── __init__.py
│   │   └── skill.py
│   │
│   └── YOUR_NEW_SKILL\          # 【新技能】在此创建文件夹
│       ├── __init__.py
│       └── skill.py            # 【必须】技能实现文件
│
├── workflow\                    # 【工作流目录】
│   ├── engine.py               # 工作流引擎（无需修改）
│   ├── __init__.py
│   │
│   ├── templates\              # 【工作流模板目录】- 所有新工作流放在这里
│   │   ├── dual_pc_setup.json # 示例：双电脑集群搭建
│   │   ├── transfer.json      # 示例：文件传输
│   │   └── YOUR_WORKFLOW.json # 【新工作流】在此创建文件
│   │
│   └── plugins\                # 【工作流插件目录】
│       ├── __init__.py
│       └── YOUR_PLUGIN.py     # 【新插件】在此创建文件
│
└── tools\                       # 【工具目录】- 基础工具
    ├── da.py                   # 桌面自动化
    ├── ai_memory.py            # 记忆系统
    └── YOUR_TOOL.py           # 【新工具】在此创建文件
```

---

## 一、添加新技能

### 1. 创建技能目录

在 `\python\MCP_Core\skills\` 下创建新文件夹：

```bash
mkdir "\python\MCP_Core\skills\my_skill"
```

### 2. 创建 `__init__.py`

```python
# \python\MCP_Core\skills\my_skill\__init__.py
"""My Skill - 我的技能描述"""

from .skill import MySkill

__all__ = ['MySkill']
```

### 3. 创建 `skill.py`

```python
# \python\MCP_Core\skills\my_skill\skill.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
My Skill - 我的技能

功能:
- 功能1
- 功能2

用法:
    skill.execute({'action': 'do_something'})
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base import Skill
from event_bus import get_event_bus


class MySkill(Skill):
    """我的技能"""
    
    # 【必须】技能元数据
    name = "my_skill"                    # 【必须】技能唯一标识（小写+下划线）
    description = "我的技能描述"          # 【必须】技能描述
    version = "1.0.0"                    # 【必须】版本号
    author = "Your Name"                 # 作者
    config_prefix = "my_skill"           # 配置前缀
    
    def __init__(self, config=None):
        super().__init__(config)
        self.event_bus = get_event_bus()
        
        # 从配置读取参数
        self.my_param = self.get_config('param_name', 'default_value')
    
    def get_parameters(self):
        """【必须】定义技能参数"""
        return {
            'action': {
                'type': 'string',
                'required': True,
                'enum': ['action1', 'action2'],  # 可选值
                'description': '操作类型'
            },
            'param1': {
                'type': 'string',
                'required': False,
                'default': 'default',
                'description': '参数1'
            }
        }
    
    def execute(self, params):
        """【必须】执行技能"""
        action = params.get('action')
        
        if action == 'action1':
            return self._do_action1(params)
        elif action == 'action2':
            return self._do_action2(params)
        else:
            return {'success': False, 'error': f'未知操作: {action}'}
    
    def _do_action1(self, params):
        """执行操作1"""
        try:
            # 发布事件
            self.event_bus.publish('my_skill_action1_started', {}, source=self.name)
            
            # 执行业务逻辑
            result = {'data': 'result'}
            
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _do_action2(self, params):
        """执行操作2"""
        pass


if __name__ == '__main__':
    # 测试代码
    skill = MySkill()
    print(f"技能: {skill.name}")
    print(f"描述: {skill.description}")
```

### 4. 注册技能

编辑 `\python\MCP_Core\server.py`，在 `_load_skills()` 方法中添加：

```python
def _load_skills(self):
    """加载技能"""
    if self._skills_loaded:
        return
    
    from skills.network_transfer.skill import NetworkTransferSkill
    from skills.exo_cluster.skill import ExoClusterSkill
    from skills.notification.skill import NotificationSkill
    from skills.system_config.skill import SystemConfigSkill
    
    # 【添加新技能】
    from skills.my_skill.skill import MySkill
    
    skills_config = self.config.get('skills', {})
    
    # 注册已有技能...
    
    # 【注册新技能】
    if self.config.is_skill_enabled('my_skill'):
        skill = MySkill(skills_config.get('my_skill'))
        self.skill_registry.register(skill)
    
    self._skills_loaded = True
```

### 5. 添加配置

编辑 `\python\MCP_Core\config.py` 中的 `DEFAULT_CONFIG`，添加技能配置：

```python
DEFAULT_CONFIG = {
    # ... 其他配置 ...
    
    'skills': {
        # ... 已有技能配置 ...
        
        # 【新技能配置】
        'my_skill': {
            'enabled': True,           # 是否启用
            'param_name': 'value',     # 自定义参数
            'timeout': 300
        }
    }
}
```

---

## 二、添加新工作流

### 1. 创建工作流文件

在 `\python\MCP_Core\workflow\templates\` 下创建 JSON 文件：

```json
{
  "name": "我的工作流",
  "version": "1.0",
  "description": "工作流描述",
  "steps": [
    {
      "id": "step1",
      "name": "步骤1",
      "description": "步骤描述",
      "skill": "skill_name",       // 【必须】使用哪个技能
      "action": "action_name",     // 【必须】调用技能的哪个动作
      "params": {                  // 【可选】传递给技能的参数
        "param1": "value1"
      },
      "depends_on": [],            // 【可选】依赖的步骤ID列表
      "retry": 3,                  // 【可选】重试次数
      "timeout": 300,              // 【可选】超时时间（秒）
      "parallel": false,           // 【可选】是否并行执行
      "target": "local"            // 【可选】执行目标：local/remote/both
    },
    {
      "id": "step2",
      "name": "步骤2",
      "description": "步骤2描述",
      "skill": "another_skill",
      "action": "do_something",
      "depends_on": ["step1"],     // 依赖 step1 完成
      "params": {
        // 可以使用上下文变量
        "input": "$step1_output"   // $ 前缀表示引用上下文
      }
    }
  ],
  "config": {
    "timeout": 600,                // 工作流总超时
    "auto_retry": true             // 自动重试
  }
}
```

### 2. 工作流步骤参数说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | string | 是 | 步骤唯一标识 |
| name | string | 是 | 步骤名称 |
| description | string | 否 | 步骤描述 |
| skill | string | 是 | 调用的技能名称 |
| action | string | 是 | 技能的动作名称 |
| params | object | 否 | 传递给技能的参数 |
| depends_on | array | 否 | 依赖的步骤ID列表 |
| retry | int | 否 | 重试次数（默认3） |
| timeout | int | 否 | 超时时间（秒） |
| parallel | bool | 否 | 是否并行执行 |
| target | string | 否 | 执行目标 |

### 3. 运行工作流

```bash
# 列出所有工作流
python \python\MCP_Core\server.py --list-workflows

# 运行工作流
python \python\MCP_Core\server.py --workflow my_workflow
```

---

## 三、添加工作流插件

### 1. 创建插件文件

在 `\python\MCP_Core\workflow\plugins\` 下创建 Python 文件：

```python
# \python\MCP_Core\workflow\plugins\my_plugin.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
My Plugin - 我的工作流插件

功能:
- 在工作流执行前后添加自定义逻辑
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from event_bus import get_event_bus


class MyWorkflowPlugin:
    """工作流插件"""
    
    def __init__(self):
        self.event_bus = get_event_bus()
        self.name = "my_plugin"
    
    def on_workflow_start(self, workflow_name, context):
        """工作流开始时调用"""
        print(f"[Plugin:{self.name}] 工作流 {workflow_name} 开始")
        # 自定义逻辑
    
    def on_workflow_complete(self, workflow_name, result):
        """工作流完成时调用"""
        print(f"[Plugin:{self.name}] 工作流 {workflow_name} 完成")
        # 自定义逻辑
    
    def on_step_start(self, workflow_name, step_id, params):
        """步骤开始时调用"""
        print(f"[Plugin:{self.name}] 步骤 {step_id} 开始")
    
    def on_step_complete(self, workflow_name, step_id, result):
        """步骤完成时调用"""
        print(f"[Plugin:{self.name}] 步骤 {step_id} 完成")
    
    def on_step_error(self, workflow_name, step_id, error):
        """步骤出错时调用"""
        print(f"[Plugin:{self.name}] 步骤 {step_id} 错误: {error}")
    
    def register(self, engine):
        """注册到引擎"""
        engine.add_plugin(self)
        print(f"[Plugin:{self.name}] 已注册")
```

### 2. 注册插件

编辑 `\python\MCP_Core\workflow\engine.py`，在 `__init__` 中添加：

```python
def __init__(self):
    # ... 现有代码 ...
    
    # 加载插件
    self._load_plugins()

def _load_plugins(self):
    """加载插件"""
    try:
        from workflow.plugins.my_plugin import MyWorkflowPlugin
        plugin = MyWorkflowPlugin()
        plugin.register(self)
    except Exception as e:
        print(f"[WorkflowEngine] 加载插件失败: {e}")
```

---

## 四、添加基础工具

### 1. 创建工具文件

在 `\python\MCP_Core\tools\` 下创建 Python 文件：

```python
# \python\MCP_Core\tools\my_tool.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
My Tool - 我的工具

用法:
    python my_tool.py <action> [args...]
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from event_bus import get_event_bus


class MyTool:
    """我的工具"""
    
    def __init__(self):
        self.event_bus = get_event_bus()
    
    def do_something(self, params):
        """执行操作"""
        # 业务逻辑
        return {'success': True, 'result': 'done'}


def main():
    tool = MyTool()
    
    if len(sys.argv) < 2:
        print("用法: python my_tool.py <action>")
        return
    
    action = sys.argv[1]
    
    if action == 'do_something':
        result = tool.do_something({})
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"未知操作: {action}")


if __name__ == '__main__':
    main()
```

---

## 五、完整示例：添加新技能

假设要添加一个 "文件备份" 技能：

### 步骤1：创建目录结构

```bash
mkdir "\python\MCP_Core\skills\file_backup"
```

### 步骤2：创建 `__init__.py`

```python
# \python\MCP_Core\skills\file_backup\__init__.py
"""File Backup Skill - 文件备份技能"""

from .skill import FileBackupSkill

__all__ = ['FileBackupSkill']
```

### 步骤3：创建 `skill.py`

```python
# \python\MCP_Core\skills\file_backup\skill.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Backup Skill - 文件备份技能

功能:
- 备份文件到指定目录
- 支持压缩
- 支持增量备份
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base import Skill
from event_bus import get_event_bus


class FileBackupSkill(Skill):
    """文件备份技能"""
    
    name = "file_backup"
    description = "文件备份与恢复"
    version = "1.0.0"
    author = "MCP Core"
    config_prefix = "file_backup"
    
    def __init__(self, config=None):
        super().__init__(config)
        self.event_bus = get_event_bus()
        self.backup_dir = Path(self.get_config('backup_dir', '/python/Backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_parameters(self):
        return {
            'action': {
                'type': 'string',
                'required': True,
                'enum': ['backup', 'restore', 'list'],
                'description': '操作类型'
            },
            'source': {
                'type': 'string',
                'required': False,
                'description': '源文件/目录路径'
            },
            'destination': {
                'type': 'string',
                'required': False,
                'description': '目标路径'
            },
            'compress': {
                'type': 'boolean',
                'required': False,
                'default': True,
                'description': '是否压缩'
            }
        }
    
    def execute(self, params):
        action = params.get('action')
        
        if action == 'backup':
            return self._backup(params)
        elif action == 'restore':
            return self._restore(params)
        elif action == 'list':
            return self._list_backups(params)
        else:
            return {'success': False, 'error': f'未知操作: {action}'}
    
    def _backup(self, params):
        """备份文件"""
        source = Path(params.get('source'))
        compress = params.get('compress', True)
        
        if not source.exists():
            return {'success': False, 'error': f'源路径不存在: {source}'}
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{source.name}_{timestamp}"
            
            if compress:
                backup_path = self.backup_dir / f"{backup_name}.zip"
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    if source.is_file():
                        zf.write(source, source.name)
                    else:
                        for file_path in source.rglob('*'):
                            if file_path.is_file():
                                zf.write(file_path, file_path.relative_to(source))
            else:
                backup_path = self.backup_dir / backup_name
                if source.is_file():
                    shutil.copy2(source, backup_path)
                else:
                    shutil.copytree(source, backup_path)
            
            self.event_bus.publish('backup_complete', {
                'source': str(source),
                'backup': str(backup_path)
            }, source=self.name)
            
            return {
                'success': True,
                'backup_path': str(backup_path),
                'size': backup_path.stat().st_size if backup_path.exists() else 0
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _restore(self, params):
        """恢复备份"""
        # 实现恢复逻辑
        pass
    
    def _list_backups(self, params):
        """列出备份"""
        try:
            backups = []
            for item in self.backup_dir.iterdir():
                if item.is_file() or item.is_dir():
                    stat = item.stat()
                    backups.append({
                        'name': item.name,
                        'path': str(item),
                        'size': stat.st_size,
                        'created': stat.st_mtime
                    })
            
            return {
                'success': True,
                'backups': backups,
                'count': len(backups)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    skill = FileBackupSkill()
    print(f"技能: {skill.name}")
    print(f"描述: {skill.description}")
```

### 步骤4：注册技能

编辑 `\python\MCP_Core\server.py`：

```python
def _load_skills(self):
    # ... 已有导入 ...
    from skills.file_backup.skill import FileBackupSkill
    
    # ... 已有注册 ...
    
    if self.config.is_skill_enabled('file_backup'):
        skill = FileBackupSkill(skills_config.get('file_backup'))
        self.skill_registry.register(skill)
```

### 步骤5：添加配置

编辑 `\python\MCP_Core\config.py`：

```python
'skills': {
    # ... 已有技能 ...
    'file_backup': {
        'enabled': True,
        'backup_dir': '/python/Backups'
    }
}
```

### 步骤6：测试

```bash
python \python\MCP_Core\server.py --call file_backup --params {"action":"list"}
```

---

## 六、快速检查清单

添加新技能/工作流时，请确认：

- [ ] 目录结构符合规范
- [ ] 包含 `__init__.py` 文件
- [ ] 技能类继承自 `Skill` 基类
- [ ] 定义了 `name`, `description`, `version`
- [ ] 实现了 `get_parameters()` 方法
- [ ] 实现了 `execute()` 方法
- [ ] 在 `server.py` 中注册
- [ ] 在 `config.py` 中添加配置
- [ ] 测试通过

---

## 七、常见问题

### Q: 技能名称有什么规范？
A: 使用小写字母和下划线，如 `my_skill`, `file_backup`

### Q: 如何引用其他技能的输出？
A: 在工作流中使用 `$step_id_output` 格式

### Q: 技能可以依赖其他技能吗？
A: 可以，在 `dependencies` 列表中声明

### Q: 如何调试技能？
A: 直接运行技能文件：`python \python\MCP_Core\skills\my_skill\skill.py`
