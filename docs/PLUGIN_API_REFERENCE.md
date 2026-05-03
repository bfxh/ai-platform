# AI 插件系统 API 参考文档

## 1. 核心模块

### 1.1 `core.ai_plugin_system`

该模块包含插件系统的核心类和功能。

#### 1.1.1 导入方式

```python
from core.ai_plugin_system import (
    BasePlugin, ToolPlugin, ConnectorPlugin, EnhancerPlugin,
    PluginMetadata, PluginConfig, PluginManager,
    create_plugin_manager, get_plugin_manager
)
```

## 2. 数据类

### 2.1 `PluginMetadata`

插件元数据类，定义插件的基本信息。

#### 2.1.1 字段

| 字段名 | 类型 | 描述 | 默认值 |
|-------|------|------|--------|
| `name` | `str` | 插件名称 | 必填 |
| `version` | `str` | 插件版本 | 必填 |
| `description` | `str` | 插件描述 | 必填 |
| `author` | `str` | 作者 | 必填 |
| `dependencies` | `List[str]` | 依赖的其他插件 | `[]` |
| `ai_enhanced` | `bool` | 是否使用 AI 增强 | `False` |
| `supported_providers` | `List[str]` | 支持的 AI 提供商 | `[]` |
| `category` | `str` | 插件类别 | `"general"` |

#### 2.1.2 使用示例

```python
metadata = PluginMetadata(
    name="my_plugin",
    version="1.0.0",
    description="我的插件",
    author="开发者",
    dependencies=["other_plugin"],
    ai_enhanced=True,
    supported_providers=["openai", "claude"],
    category="tool"
)
```

### 2.2 `PluginConfig`

插件配置类，定义插件的配置选项。

#### 2.2.1 字段

| 字段名 | 类型 | 描述 | 默认值 |
|-------|------|------|--------|
| `enabled` | `bool` | 是否启用 | `True` |
| `settings` | `Dict` | 自定义设置 | `{}` |
| `ai_provider` | `str` | AI 提供商 | `None` |
| `ai_model` | `str` | AI 模型 | `None` |

#### 2.2.2 使用示例

```python
config = PluginConfig(
    enabled=True,
    settings={"api_key": "your_api_key"},
    ai_provider="openai",
    ai_model="gpt-4"
)
```

## 3. 插件基类

### 3.1 `BasePlugin`

所有插件的基类，提供通用功能。

#### 3.1.1 属性

| 属性名 | 类型 | 描述 |
|-------|------|------|
| `metadata` | `PluginMetadata` | 插件元数据 |
| `config` | `PluginConfig` | 插件配置 |
| `ai_client` | `UnifiedAI` | AI 客户端 |
| `initialized` | `bool` | 初始化状态 |

#### 3.1.2 方法

| 方法名 | 参数 | 返回值 | 描述 |
|-------|------|--------|------|
| `initialize(config: Dict = None)` | `config`: 配置字典 | 无 | 初始化插件 |
| `execute(input_data: Any, **kwargs)` | `input_data`: 输入数据<br>`**kwargs`: 额外参数 | `Any` | 执行插件功能 |
| `shutdown()` | 无 | 无 | 关闭插件 |
| `set_ai_client(client: UnifiedAI)` | `client`: AI 客户端 | 无 | 设置 AI 客户端 |
| `enhance_with_ai(prompt: str, **kwargs)` | `prompt`: 提示词<br>`**kwargs`: 额外参数 | `str` | 使用 AI 增强功能 |

### 3.2 `ToolPlugin`

工具插件基类，支持 function calling。

#### 3.2.1 继承关系

`BasePlugin` → `ToolPlugin`

#### 3.2.2 方法

| 方法名 | 参数 | 返回值 | 描述 |
|-------|------|--------|------|
| `get_tools()` | 无 | `List[Dict]` | 返回工具定义（用于 function calling） |

### 3.3 `ConnectorPlugin`

连接器插件基类，用于连接外部服务。

#### 3.3.1 继承关系

`BasePlugin` → `ConnectorPlugin`

#### 3.3.2 方法

| 方法名 | 参数 | 返回值 | 描述 |
|-------|------|--------|------|
| `connect(**kwargs)` | `**kwargs`: 连接参数 | `bool` | 建立连接 |
| `disconnect()` | 无 | 无 | 断开连接 |
| `is_connected()` | 无 | `bool` | 检查连接状态 |

### 3.4 `EnhancerPlugin`

增强器插件基类，用于增强 AI 能力。

#### 3.4.1 继承关系

`BasePlugin` → `EnhancerPlugin`

#### 3.4.2 方法

| 方法名 | 参数 | 返回值 | 描述 |
|-------|------|--------|------|
| `enhance_prompt(prompt: str, context: Dict = None)` | `prompt`: 提示词<br>`context`: 上下文 | `str` | 增强提示词 |
| `enhance_response(response: str, context: Dict = None)` | `response`: 响应<br>`context`: 上下文 | `str` | 增强响应 |

## 4. 插件管理器

### 4.1 `PluginManager`

插件管理器，负责插件的注册、加载和执行。

#### 4.1.1 构造函数

```python
PluginManager(plugin_dir: str = None)
```

- `plugin_dir`: 插件目录路径，默认为 `\python\plugins`

#### 4.1.2 方法

| 方法名 | 参数 | 返回值 | 描述 |
|-------|------|--------|------|
| `register_plugin(plugin: BasePlugin, config: Dict = None)` | `plugin`: 插件实例<br>`config`: 配置字典 | 无 | 注册插件 |
| `unregister_plugin(name: str)` | `name`: 插件名称 | 无 | 注销插件 |
| `load_builtin_plugins()` | 无 | 无 | 加载内置插件 |
| `load_plugin_from_file(filepath: str)` | `filepath`: 插件文件路径 | `bool` | 从文件加载插件 |
| `get_plugin(name: str)` | `name`: 插件名称 | `Optional[BasePlugin]` | 获取插件 |
| `execute(plugin_name: str, input_data: Any, **kwargs)` | `plugin_name`: 插件名称<br>`input_data`: 输入数据<br>`**kwargs`: 额外参数 | `Any` | 执行插件 |
| `list_plugins()` | 无 | `List[Dict]` | 列出所有插件 |
| `get_ai_tools()` | 无 | `List[Dict]` | 获取所有 AI 工具定义 |
| `get_ai_enhanced_plugins()` | 无 | `List[BasePlugin]` | 获取 AI 增强的插件 |
| `set_plugin_ai_provider(plugin_name: str, provider: str, model: str = None)` | `plugin_name`: 插件名称<br>`provider`: AI 提供商<br>`model`: AI 模型 | 无 | 设置插件的 AI 提供商 |
| `enable_plugin(name: str)` | `name`: 插件名称 | 无 | 启用插件 |
| `disable_plugin(name: str)` | `name`: 插件名称 | 无 | 禁用插件 |

## 5. 便捷函数

### 5.1 `create_plugin_manager()`

创建插件管理器并加载内置插件。

#### 5.1.1 签名

```python
def create_plugin_manager() -> PluginManager:
    """创建插件管理器并加载内置插件"""
```

#### 5.1.2 返回值

`PluginManager`: 插件管理器实例

### 5.2 `get_plugin_manager()`

获取全局插件管理器实例。

#### 5.2.1 签名

```python
def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器"""
```

#### 5.2.2 返回值

`PluginManager`: 全局插件管理器实例

## 6. 工具定义格式

工具插件的 `get_tools()` 方法返回的工具定义遵循 OpenAI 的 function calling 格式。

### 6.1 工具定义结构

```python
[
    {
        "type": "function",
        "function": {
            "name": "工具名称",
            "description": "工具描述",
            "parameters": {
                "type": "object",
                "properties": {
                    "参数名": {
                        "type": "参数类型",
                        "description": "参数描述"
                    }
                },
                "required": ["必填参数1", "必填参数2"]
            }
        }
    }
]
```

### 6.2 示例

```python
def get_tools(self) -> List[Dict]:
    return [{
        "type": "function",
        "function": {
            "name": "generate_code",
            "description": "生成指定语言的代码",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {"type": "string", "description": "编程语言"},
                    "description": {"type": "string", "description": "代码功能描述"},
                    "requirements": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["language", "description"]
            }
        }
    }]
```

## 7. 内置插件

### 7.1 `CodeGeneratorPlugin`

代码生成插件，使用 AI 生成各种编程语言的代码。

#### 7.1.1 元数据

- 名称: `code_generator`
- 版本: `1.0.0`
- 描述: 生成各种编程语言的代码
- 类别: `tool`
- AI 增强: `True`

#### 7.1.2 工具定义

- 名称: `generate_code`
- 描述: 生成指定语言的代码
- 参数:
  - `language`: 编程语言（必填）
  - `description`: 代码功能描述（必填）
  - `requirements`: 要求列表（可选）

### 7.2 `DocumentAnalyzerPlugin`

文档分析插件，分析文档内容并提取关键信息。

#### 7.2.1 元数据

- 名称: `document_analyzer`
- 版本: `1.0.0`
- 描述: 分析文档内容，提取关键信息
- 类别: `tool`
- AI 增强: `True`

#### 7.2.2 工具定义

- 名称: `analyze_document`
- 描述: 分析文档内容
- 参数:
  - `document`: 文档内容（必填）
  - `type`: 分析类型（可选，取值：summary, keywords, sentiment, entities）

### 7.3 `DatabaseConnectorPlugin`

数据库连接器插件，连接各种数据库并执行 SQL。

#### 7.3.1 元数据

- 名称: `database_connector`
- 版本: `1.0.0`
- 描述: 连接各种数据库
- 类别: `connector`
- AI 增强: `False`

### 7.4 `PromptEnhancerPlugin`

提示词增强器插件，自动优化提示词以获得更好的结果。

#### 7.4.1 元数据

- 名称: `prompt_enhancer`
- 版本: `1.0.0`
- 描述: 自动优化提示词以获得更好的结果
- 类别: `enhancer`
- AI 增强: `True`

## 8. 配置文件

插件系统使用 JSON 格式的配置文件存储插件配置。

### 8.1 配置文件路径

配置文件位于用户主目录下：`~/.ai_plugins.json`

### 8.2 配置文件结构

```json
{
  "plugins": {
    "plugin_name": {
      "enabled": true,
      "settings": {},
      "ai_provider": "openai",
      "ai_model": "gpt-4"
    }
  }
}
```

## 9. 错误处理

### 9.1 常见错误

| 错误信息 | 可能原因 |
|---------|---------|
| `[错误] 插件不存在: {plugin_name}` | 插件未注册或名称错误 |
| `[错误] 插件已禁用: {plugin_name}` | 插件已被禁用 |
| `[错误] 插件未初始化` | 插件未调用 `initialize()` 方法 |
| `[AI增强失败] {e}` | AI 调用失败 |

### 9.2 错误处理建议

1. **捕获异常**：在插件中捕获并处理所有可能的异常
2. **返回清晰的错误信息**：使用友好的错误信息
3. **日志记录**：记录详细的错误信息以便调试

## 10. 性能优化

### 10.1 插件性能优化

1. **延迟初始化**：只在需要时初始化插件
2. **缓存**：缓存重复计算的结果
3. **异步执行**：对于耗时操作，考虑使用异步执行
4. **资源管理**：及时释放不需要的资源

### 10.2 插件管理器性能

1. **插件加载**：按需加载插件，避免一次性加载所有插件
2. **配置缓存**：缓存插件配置，减少文件 I/O
3. **批量操作**：支持批量执行插件操作

## 11. 安全考虑

### 11.1 插件安全

1. **权限控制**：限制插件的权限范围
2. **输入验证**：验证所有输入参数
3. **异常处理**：妥善处理所有异常，避免暴露敏感信息
4. **依赖检查**：检查插件依赖的安全性

### 11.2 AI 安全

1. **API 密钥保护**：安全存储 AI API 密钥
2. **请求限制**：限制 AI 请求频率，避免滥用
3. **内容过滤**：过滤敏感内容，避免生成有害内容

## 12. 版本兼容性

### 12.1 版本号格式

插件版本号遵循语义化版本规范：`MAJOR.MINOR.PATCH`

- `MAJOR`：不兼容的 API 变更
- `MINOR`：向后兼容的功能添加
- `PATCH`：向后兼容的 bug 修复

### 12.2 兼容性检查

插件系统会检查插件版本与系统版本的兼容性，确保插件能够正常运行。

## 13. 扩展 API

### 13.1 自定义插件类型

开发者可以通过继承 `BasePlugin` 创建自定义插件类型：

```python
class CustomPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.metadata.category = "custom"
    
    def custom_method(self):
        """自定义方法"""
        pass
```

### 13.2 扩展插件管理器

开发者可以通过继承 `PluginManager` 扩展插件管理器功能：

```python
class CustomPluginManager(PluginManager):
    def custom_method(self):
        """自定义方法"""
        pass
```

## 14. 插件测试

### 14.1 测试方法

1. **单元测试**：测试插件的各个方法
2. **集成测试**：测试插件与系统的集成
3. **性能测试**：测试插件的性能
4. **安全测试**：测试插件的安全性

### 14.2 测试工具

插件系统提供了测试工具，用于测试插件的功能：

```python
from core.ai_plugin_system import create_plugin_manager

# 创建插件管理器
manager = create_plugin_manager()

# 测试插件
result = manager.execute("plugin_name", input_data, **kwargs)
print(result)
```

## 15. 插件文档

### 15.1 文档格式

插件文档应包含以下内容：

1. **插件概述**：插件的功能和用途
2. **安装说明**：如何安装和配置插件
3. **使用示例**：如何使用插件
4. **API 参考**：插件的 API 文档
5. **常见问题**：常见问题和解决方案

### 15.2 文档位置

插件文档应放置在插件文件的头部注释中，或单独的 README.md 文件中。

---

**文档版本**: 1.0.0
**最后更新**: 2026-04-24
**适用系统**: AI 插件系统 v1.0+
