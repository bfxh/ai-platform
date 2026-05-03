# MCP Core 使用指南

## 目录

1. [快速开始](#快速开始)
2. [配置管理系统](#配置管理系统)
3. [日志系统](#日志系统)
4. [性能监控](#性能监控)
5. [技能开发](#技能开发)
6. [最佳实践](#最佳实践)

---

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from skills.ai_toolkit_ecosystem.skill import AIToolkitEcosystem

# 创建技能实例
skill = AIToolkitEcosystem()

# 执行技能
result = skill.execute({
    'action': 'list'
})

print(result)
```

---

## 配置管理系统

### 概述

MCP Core 提供了统一的配置管理系统，支持配置的加载、保存、验证和热重载。

### 基本用法

```python
from config_manager import get_config_manager

# 获取配置管理器实例
config_manager = get_config_manager()

# 加载配置
config = config_manager.load_config('my_skill')

# 获取配置值
value = config_manager.get_config('my_skill', 'key', 'default_value')

# 设置配置值
config_manager.set_config('my_skill', 'key', 'new_value')

# 保存配置
config_manager.save_config('my_skill')
```

### 配置文件格式

配置文件使用 JSON 格式，存储在 `config/` 目录下：

```json
{
  "key1": "value1",
  "key2": 123,
  "nested": {
    "key3": "value3"
  }
}
```

### 在技能中使用配置

```python
from skills.base import Skill

class MySkill(Skill):
    name = "my_skill"
    config_prefix = "my_skill"
    
    def __init__(self, config=None):
        super().__init__(config)
        # 获取配置值
        self.timeout = self.get_config('timeout', 30)
        self.max_retries = self.get_config('max_retries', 3)
```

---

## 日志系统

### 概述

MCP Core 使用 Python 标准日志模块，提供统一的日志记录功能。

### 日志级别

- `DEBUG`: 调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 在技能中使用日志

```python
from skills.base import Skill

class MySkill(Skill):
    name = "my_skill"
    
    def execute(self, params):
        # 记录信息日志
        self.logger.info("开始执行任务")
        
        # 记录调试日志
        self.logger.debug(f"参数: {params}")
        
        try:
            # 执行业务逻辑
            result = self.do_something()
            self.logger.info("任务执行成功")
            return {'success': True, 'result': result}
        except Exception as e:
            # 记录错误日志
            self.logger.error(f"任务执行失败: {e}")
            return {'success': False, 'error': str(e)}
```

### 日志配置

日志文件存储在 `logs/` 目录下：

- `skill.log`: 技能日志
- `performance.log`: 性能日志

---

## 性能监控

### 概述

MCP Core 提供了性能监控模块，用于监控技能执行性能和分析瓶颈。

### 使用性能监控装饰器

```python
from performance_monitor import monitor_performance
from skills.base import Skill

class MySkill(Skill):
    name = "my_skill"
    
    @monitor_performance()
    def execute(self, params):
        # 执行业务逻辑
        return {'success': True}
```

### 查看性能报告

```python
from performance_monitor import PerformanceProfiler

profiler = PerformanceProfiler()

# 生成性能报告
report = profiler.generate_report()
print(report)

# 分析性能瓶颈
bottlenecks = profiler.analyze_bottlenecks()
for bottleneck in bottlenecks:
    print(f"瓶颈: {bottleneck}")
```

### 导出性能指标

```python
from performance_monitor import get_performance_monitor

monitor = get_performance_monitor()

# 导出到文件
monitor.export_metrics('performance_report.json')
```

---

## 技能开发

### 创建新技能

1. 创建技能目录

```bash
mkdir skills/my_skill
touch skills/my_skill/__init__.py
touch skills/my_skill/skill.py
```

2. 实现技能类

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
My Skill - 我的技能
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base import Skill, handle_errors


class MySkill(Skill):
    """我的技能"""
    
    name = "my_skill"
    description = "我的技能描述"
    version = "1.0.0"
    author = "Your Name"
    config_prefix = "my_skill"
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        # 初始化配置
        self.timeout = self.get_config('timeout', 30)
    
    def get_parameters(self) -> Dict[str, Any]:
        """定义参数"""
        return {
            'action': {
                'type': 'string',
                'required': True,
                'enum': ['do_something', 'do_another'],
                'description': '操作类型'
            },
            'param1': {
                'type': 'string',
                'required': False,
                'description': '参数1'
            }
        }
    
    @handle_errors
    def execute(self, params: Dict) -> Dict:
        """执行技能"""
        action = params.get('action')
        
        if action == 'do_something':
            return self._do_something(params)
        elif action == 'do_another':
            return self._do_another(params)
        else:
            return {'success': False, 'error': f'未知操作: {action}'}
    
    def _do_something(self, params: Dict) -> Dict:
        """执行某个操作"""
        self.logger.info("执行 do_something")
        
        # 业务逻辑
        result = "操作结果"
        
        return {
            'success': True,
            'result': result
        }
    
    def _do_another(self, params: Dict) -> Dict:
        """执行另一个操作"""
        self.logger.info("执行 do_another")
        
        return {
            'success': True,
            'result': "另一个结果"
        }
```

3. 创建技能元数据文件

```json
{
  "name": "my_skill",
  "version": "1.0.0",
  "description": "我的技能描述",
  "author": "Your Name",
  "dependencies": [],
  "tags": ["utility"]
}
```

### 技能基类方法

#### 初始化方法

- `__init__(config)`: 初始化技能
- `_do_initialize()`: 执行初始化逻辑
- `_do_shutdown()`: 执行关闭逻辑

#### 配置管理

- `get_config(key, default)`: 获取配置值
- `set_config(key, value)`: 设置配置值
- `get_all_config()`: 获取所有配置

#### 状态管理

- `get_status()`: 获取技能状态
- `update_status(status)`: 更新技能状态

#### 执行方法

- `execute(params)`: 执行技能
- `validate_params(params)`: 验证参数
- `get_parameters()`: 获取参数定义

---

## 最佳实践

### 1. 错误处理

始终使用 `@handle_errors` 装饰器包装 `execute` 方法：

```python
from skills.base import handle_errors

@handle_errors
def execute(self, params):
    # 业务逻辑
    pass
```

### 2. 日志记录

使用技能内置的 logger 记录日志：

```python
def execute(self, params):
    self.logger.info("开始执行")
    self.logger.debug(f"参数: {params}")
    
    try:
        result = self.do_work()
        self.logger.info("执行成功")
        return {'success': True, 'result': result}
    except Exception as e:
        self.logger.error(f"执行失败: {e}")
        return {'success': False, 'error': str(e)}
```

### 3. 参数验证

在 `execute` 方法中验证参数：

```python
def execute(self, params):
    # 验证必需参数
    if 'required_param' not in params:
        return {'success': False, 'error': '缺少必需参数: required_param'}
    
    # 验证参数类型
    if not isinstance(params['required_param'], str):
        return {'success': False, 'error': '参数类型错误'}
    
    # 执行业务逻辑
    pass
```

### 4. 配置管理

使用配置管理器管理配置：

```python
def __init__(self, config=None):
    super().__init__(config)
    # 从配置获取值，使用默认值
    self.timeout = self.get_config('timeout', 30)
    self.max_retries = self.get_config('max_retries', 3)
```

### 5. 性能监控

对耗时操作使用性能监控：

```python
from performance_monitor import monitor_performance

@monitor_performance()
def heavy_operation(self):
    # 耗时操作
    pass
```

### 6. 事件发布

如果 event_bus 可用，发布事件：

```python
def execute(self, params):
    result = self.do_work()
    
    # 发布事件
    if self.event_bus:
        self.event_bus.publish('my_event', {
            'result': result
        }, source=self.name)
    
    return result
```

### 7. 返回值格式

统一返回值格式：

```python
# 成功
return {
    'success': True,
    'result': result_data,
    'message': '可选的成功消息'
}

# 失败
return {
    'success': False,
    'error': '错误描述'
}
```

---

## 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_skills/test_my_skill.py

# 运行集成测试
pytest tests/integration/
```

### 编写测试

```python
import pytest
from skills.my_skill.skill import MySkill

class TestMySkill:
    @pytest.fixture
    def skill(self):
        return MySkill()
    
    def test_skill_initialization(self, skill):
        assert skill.name == "my_skill"
        assert skill.version == "1.0.0"
    
    def test_execute_success(self, skill):
        result = skill.execute({'action': 'do_something'})
        assert result['success'] is True
    
    def test_execute_failure(self, skill):
        result = skill.execute({'action': 'invalid_action'})
        assert result['success'] is False
```

---

## 故障排除

### 常见问题

1. **技能无法加载**
   - 检查技能文件是否存在
   - 检查技能类名是否正确
   - 检查导入路径是否正确

2. **配置无法读取**
   - 检查配置文件格式是否正确
   - 检查配置文件路径是否正确
   - 检查配置键名是否正确

3. **日志不输出**
   - 检查日志级别设置
   - 检查日志目录是否存在
   - 检查日志文件权限

4. **性能监控不工作**
   - 检查是否正确使用装饰器
   - 检查性能监控器是否启用
   - 检查指标数量是否超过限制

---

## 更多信息

- [API 文档](api.md)
- [开发指南](development.md)
- [贡献指南](contributing.md)
