# AI插件系统

## 架构概览

AI插件系统是一个可扩展的插件管理框架，支持插件的安装、卸载、启用、禁用等核心功能。

### 核心组件

1. **PluginMetadata** - 插件元数据，包含插件的基本信息
2. **PluginConfig** - 插件配置，控制插件的行为
3. **BasePlugin** - 插件基类，定义插件的基本接口
4. **PluginRegistry** - 插件注册表，管理插件元数据和配置
5. **PluginManager** - 插件管理器，核心功能实现

### 插件类型

- **BasePlugin** - 基础插件类型
- **ToolPlugin** - 工具插件，提供function calling功能
- **ConnectorPlugin** - 连接器插件，连接外部服务
- **EnhancerPlugin** - 增强器插件，增强AI能力

## 安装插件

```python
from core.plugin_system import PluginManager

manager = PluginManager()

# 安装单个插件文件
manager.install_plugin("path/to/plugin.py")

# 安装插件包
manager.install_plugin("path/to/plugin.zip")
```

## 管理插件

```python
# 启用插件
manager.enable_plugin("plugin_name")

# 禁用插件
manager.disable_plugin("plugin_name")

# 卸载插件
manager.uninstall_plugin("plugin_name")

# 列出所有插件
plugins = manager.list_plugins()

# 获取性能报告
report = manager.get_performance_report()
```

## 执行插件

```python
# 执行插件
result = manager.execute_plugin(
    "plugin_name",
    input_data="Hello",
    action="greet"
)

# 结果格式
{
    "success": True,
    "result": "插件执行结果",
    "execution_time": 0.1
}
```

## 开发插件

### 基本插件

```python
from core.plugin_system.plugin_base import BasePlugin
from core.plugin_system.plugin_metadata import PluginMetadata

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            description="我的插件",
            author="Author"
        )
    
    def initialize(self, config=None):
        # 初始化逻辑
        self.initialized = True
    
    def execute(self, input_data, **kwargs):
        # 执行逻辑
        return f"处理结果: {input_data}"
```

### 工具插件

```python
from core.plugin_system.plugin_base import ToolPlugin
from core.plugin_system.plugin_metadata import PluginMetadata

class MyToolPlugin(ToolPlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="my_tool",
            version="1.0.0",
            description="我的工具插件",
            author="Author"
        )
    
    def initialize(self, config=None):
        self.initialized = True
    
    def execute(self, input_data, **kwargs):
        # 执行逻辑
        pass
    
    def get_tools(self):
        # 返回工具定义
        return [{
            "type": "function",
            "function": {
                "name": "my_tool_function",
                "description": "工具功能描述",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"}
                    },
                    "required": ["param1"]
                }
            }
        }]
```

## 配置文件

插件注册表保存在 `.plugin_registry.json` 文件中，包含所有插件的元数据和配置。

## 性能优化

- **懒加载** - 插件仅在需要时加载
- **自动清理** - 长时间未使用的插件会被自动卸载
- **线程安全** - 使用锁机制确保线程安全
- **资源监控** - 跟踪插件的执行时间和调用次数

## 错误处理

插件执行失败时会返回错误信息，不会影响整个系统的运行。

## 安全注意事项

- 只安装来自可信来源的插件
- 插件执行在隔离环境中，不会影响主系统
- 定期检查插件的执行情况，防止恶意插件
