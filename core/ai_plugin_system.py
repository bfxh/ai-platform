#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI插件系统 - 可扩展的工具和连接器
支持: 独立插件、AI增强插件、第三方服务集成
"""

import importlib
import importlib.util
import json
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

sys.path.insert(0, r"\python\core")
sys.path.insert(0, r"\python\tools")
try:
    from ai_adapter import UnifiedAI
except ImportError:
    UnifiedAI = None
from ai_collaboration import AICollaborator, CollaborationMode


@dataclass
class PluginMetadata:
    """插件元数据"""

    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = field(default_factory=list)
    ai_enhanced: bool = False  # 是否使用AI增强
    supported_providers: List[str] = field(default_factory=list)
    category: str = "general"  # general, tool, connector, enhancer


@dataclass
class PluginConfig:
    """插件配置"""

    enabled: bool = True
    settings: Dict = field(default_factory=dict)
    ai_provider: str = None  # 用于AI增强的提供商
    ai_model: str = None


class BasePlugin(ABC):
    """插件基类"""

    def __init__(self):
        self.metadata: PluginMetadata = None
        self.config: PluginConfig = PluginConfig()
        self.ai_client: UnifiedAI = None
        self.initialized = False

    @abstractmethod
    def initialize(self, config: Dict = None):
        """初始化插件"""
        pass

    @abstractmethod
    def execute(self, input_data: Any, **kwargs) -> Any:
        """执行插件功能"""
        pass

    def shutdown(self):
        """关闭插件"""
        self.initialized = False

    def set_ai_client(self, client: UnifiedAI):
        """设置AI客户端"""
        self.ai_client = client

    def enhance_with_ai(self, prompt: str, **kwargs) -> str:
        """使用AI增强功能"""
        if not self.ai_client:
            return prompt
        try:
            return self.ai_client.chat(prompt, **kwargs)
        except Exception as e:
            return f"[AI增强失败] {e}\n原始内容: {prompt}"


class ToolPlugin(BasePlugin):
    """工具插件基类"""

    def __init__(self):
        super().__init__()
        self.metadata.category = "tool"

    @abstractmethod
    def get_tools(self) -> List[Dict]:
        """返回工具定义（用于function calling）"""
        pass


class ConnectorPlugin(BasePlugin):
    """连接器插件基类 - 连接外部服务"""

    def __init__(self):
        super().__init__()
        self.metadata.category = "connector"

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """建立连接"""
        pass

    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """检查连接状态"""
        pass


class EnhancerPlugin(BasePlugin):
    """增强器插件基类 - 增强AI能力"""

    def __init__(self):
        super().__init__()
        self.metadata.category = "enhancer"

    @abstractmethod
    def enhance_prompt(self, prompt: str, context: Dict = None) -> str:
        """增强提示词"""
        pass

    @abstractmethod
    def enhance_response(self, response: str, context: Dict = None) -> str:
        """增强响应"""
        pass


# ============ 内置插件示例 ============


class CodeGeneratorPlugin(ToolPlugin):
    """代码生成插件 - AI增强版"""

    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="code_generator",
            version="1.0.0",
            description="生成各种编程语言的代码",
            author="AI System",
            ai_enhanced=True,
            supported_providers=["openai", "claude", "deepseek", "stepfun"],
        )

    def initialize(self, config: Dict = None):
        if config:
            self.config = PluginConfig(**config)
        if self.config.ai_provider:
            self.ai_client = UnifiedAI(provider=self.config.ai_provider)
        self.initialized = True

    def execute(self, input_data: Any, **kwargs) -> Any:
        """生成代码"""
        if not self.initialized:
            return "[错误] 插件未初始化"

        # 解析输入
        if isinstance(input_data, dict):
            language = input_data.get("language", "python")
            description = input_data.get("description", "")
            requirements = input_data.get("requirements", [])
        else:
            language = kwargs.get("language", "python")
            description = str(input_data)
            requirements = []

        # 构建提示词
        prompt = f"请用{language}编写代码:\n{description}\n"
        if requirements:
            prompt += f"\n要求:\n" + "\n".join(f"- {r}" for r in requirements)

        # AI增强生成
        if self.ai_client and self.metadata.ai_enhanced:
            return self.enhance_with_ai(prompt)

        return f"[代码生成] {language}\n{description}"

    def get_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_code",
                    "description": "生成指定语言的代码",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "language": {"type": "string", "description": "编程语言"},
                            "description": {"type": "string", "description": "代码功能描述"},
                            "requirements": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["language", "description"],
                    },
                },
            }
        ]


class DocumentAnalyzerPlugin(ToolPlugin):
    """文档分析插件"""

    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="document_analyzer",
            version="1.0.0",
            description="分析文档内容，提取关键信息",
            author="AI System",
            ai_enhanced=True,
        )

    def initialize(self, config: Dict = None):
        if config:
            self.config = PluginConfig(**config)
        if self.config.ai_provider:
            self.ai_client = UnifiedAI(provider=self.config.ai_provider)
        self.initialized = True

    def execute(self, input_data: Any, **kwargs) -> Any:
        """分析文档"""
        if not self.initialized:
            return "[错误] 插件未初始化"

        document = str(input_data)
        analysis_type = kwargs.get("type", "summary")

        prompts = {
            "summary": f"请总结以下文档:\n{document[:3000]}",
            "keywords": f"请提取以下文档的关键词:\n{document[:3000]}",
            "sentiment": f"请分析以下文档的情感倾向:\n{document[:3000]}",
            "entities": f"请识别以下文档中的命名实体:\n{document[:3000]}",
        }

        prompt = prompts.get(analysis_type, prompts["summary"])

        if self.ai_client:
            return self.enhance_with_ai(prompt)

        return f"[文档分析] {analysis_type}\n{document[:500]}..."

    def get_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_document",
                    "description": "分析文档内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "document": {"type": "string"},
                            "type": {"type": "string", "enum": ["summary", "keywords", "sentiment", "entities"]},
                        },
                        "required": ["document"],
                    },
                },
            }
        ]


class DatabaseConnectorPlugin(ConnectorPlugin):
    """数据库连接器插件"""

    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="database_connector", version="1.0.0", description="连接各种数据库", author="AI System"
        )
        self.connection = None

    def initialize(self, config: Dict = None):
        if config:
            self.config = PluginConfig(**config)
        self.initialized = True

    def connect(self, **kwargs) -> bool:
        """连接数据库"""
        db_type = kwargs.get("type", "sqlite")
        connection_string = kwargs.get("connection_string", "")

        try:
            if db_type == "sqlite":
                import sqlite3

                self.connection = sqlite3.connect(connection_string or ":memory:")
            elif db_type == "mysql":
                import pymysql

                self.connection = pymysql.connect(**kwargs)
            elif db_type == "postgresql":
                import psycopg2

                self.connection = psycopg2.connect(connection_string)

            return True
        except Exception as e:
            print(f"[数据库连接失败] {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connection is not None

    def execute(self, input_data: Any, **kwargs) -> Any:
        if not self.is_connected():
            if not self.connect(**kwargs):
                return "[错误] 无法连接数据库"

        sql = str(input_data)
        dangerous = ["DROP", "DELETE FROM", "TRUNCATE", "ALTER", "GRANT", "REVOKE"]
        sql_upper = sql.strip().upper()
        if any(sql_upper.startswith(d) for d in dangerous):
            return "[错误] 危险SQL操作被阻止"

        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)

            if sql.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                return results
            else:
                self.connection.commit()
                return f"[成功] 影响行数: {cursor.rowcount}"
        except Exception as e:
            return f"[错误] {e}"


class PromptEnhancerPlugin(EnhancerPlugin):
    """提示词增强器插件"""

    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="prompt_enhancer",
            version="1.0.0",
            description="自动优化提示词以获得更好的结果",
            author="AI System",
            ai_enhanced=True,
        )

    def initialize(self, config: Dict = None):
        if config:
            self.config = PluginConfig(**config)
        if self.config.ai_provider:
            self.ai_client = UnifiedAI(provider=self.config.ai_provider)
        self.initialized = True

    def enhance_prompt(self, prompt: str, context: Dict = None) -> str:
        """增强提示词"""
        if not self.ai_client:
            return prompt

        enhancement_prompt = f"""请优化以下提示词，使其更清晰、更具体、更容易获得好的回答。

原始提示词:
{prompt}

请输出优化后的提示词，直接给出优化版本，不需要解释:"""

        try:
            enhanced = self.ai_client.chat(enhancement_prompt, keep_history=False)
            return enhanced
        except Exception:
            return prompt

    def enhance_response(self, response: str, context: Dict = None) -> str:
        """增强响应"""
        return response

    def execute(self, input_data: Any, **kwargs) -> Any:
        """执行增强"""
        prompt = str(input_data)
        return self.enhance_prompt(prompt, kwargs.get("context"))


# ============ 插件管理器 ============


class PluginManager:
    """
    插件管理器 - 管理所有插件

    用法:
        manager = PluginManager()

        # 加载内置插件
        manager.load_builtin_plugins()

        # 加载外部插件
        manager.load_plugin_from_file("path/to/plugin.py")

        # 使用插件
        result = manager.execute("code_generator", {"language": "python", "description": "快速排序"})

        # 获取AI增强工具
        tools = manager.get_ai_tools()
    """

    def __init__(self, plugin_dir: str = None):
        self.plugin_dir = plugin_dir or os.path.join(os.path.dirname(__file__), "..", "plugins")
        self.plugins: Dict[str, BasePlugin] = {}
        self.config_file = Path.home() / ".ai_plugins.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"plugins": {}}

    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except (OSError, IOError) as e:
            print(f"[WARNING] Failed to save config: {e}")

    def register_plugin(self, plugin: BasePlugin, config: Dict = None):
        """注册插件"""
        name = plugin.metadata.name

        # 加载配置
        plugin_config = self.config.get("plugins", {}).get(name, {})
        if config:
            plugin_config.update(config)

        # 初始化
        plugin.initialize(plugin_config)

        self.plugins[name] = plugin
        print(f"✅ 插件已注册: {name} v{plugin.metadata.version}")

    def unregister_plugin(self, name: str):
        """注销插件"""
        if name in self.plugins:
            self.plugins[name].shutdown()
            del self.plugins[name]
            print(f"✅ 插件已注销: {name}")

    def load_builtin_plugins(self):
        """加载内置插件"""
        builtins = [CodeGeneratorPlugin(), DocumentAnalyzerPlugin(), DatabaseConnectorPlugin(), PromptEnhancerPlugin()]

        for plugin in builtins:
            self.register_plugin(plugin)

    def load_plugin_from_file(self, filepath: str) -> bool:
        """从文件加载插件"""
        try:
            spec = importlib.util.spec_from_file_location("plugin", filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找插件类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr != BasePlugin
                    and attr not in [ToolPlugin, ConnectorPlugin, EnhancerPlugin]
                ):

                    plugin = attr()
                    self.register_plugin(plugin)
                    return True

            return False
        except Exception as e:
            print(f"[错误] 加载插件失败: {e}")
            return False

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """获取插件"""
        return self.plugins.get(name)

    def execute(self, plugin_name: str, input_data: Any, **kwargs) -> Any:
        """执行插件"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return f"[错误] 插件不存在: {plugin_name}"

        if not plugin.config.enabled:
            return f"[错误] 插件已禁用: {plugin_name}"

        return plugin.execute(input_data, **kwargs)

    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        return [
            {
                "name": p.metadata.name,
                "version": p.metadata.version,
                "description": p.metadata.description,
                "category": p.metadata.category,
                "enabled": p.config.enabled,
                "ai_enhanced": p.metadata.ai_enhanced,
            }
            for p in self.plugins.values()
        ]

    def get_ai_tools(self) -> List[Dict]:
        """获取所有AI工具定义"""
        tools = []
        for plugin in self.plugins.values():
            if isinstance(plugin, ToolPlugin) and plugin.config.enabled:
                tools.extend(plugin.get_tools())
        return tools

    def get_ai_enhanced_plugins(self) -> List[BasePlugin]:
        """获取AI增强的插件"""
        return [p for p in self.plugins.values() if p.metadata.ai_enhanced]

    def set_plugin_ai_provider(self, plugin_name: str, provider: str, model: str = None):
        """设置插件的AI提供商"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.config.ai_provider = provider
            plugin.config.ai_model = model
            plugin.ai_client = UnifiedAI(provider=provider, model=model)

            # 保存配置
            if "plugins" not in self.config:
                self.config["plugins"] = {}
            if plugin_name not in self.config["plugins"]:
                self.config["plugins"][plugin_name] = {}
            self.config["plugins"][plugin_name]["ai_provider"] = provider
            if model:
                self.config["plugins"][plugin_name]["ai_model"] = model
            self._save_config()

            print(f"✅ {plugin_name} 的AI提供商已设置为 {provider}")

    def enable_plugin(self, name: str):
        """启用插件"""
        if name in self.plugins:
            self.plugins[name].config.enabled = True
            print(f"✅ 插件已启用: {name}")

    def disable_plugin(self, name: str):
        """禁用插件"""
        if name in self.plugins:
            self.plugins[name].config.enabled = False
            print(f"⏸️ 插件已禁用: {name}")


# ============ 便捷函数 ============


def create_plugin_manager() -> PluginManager:
    """创建插件管理器并加载内置插件"""
    manager = PluginManager()
    manager.load_builtin_plugins()
    return manager


# 全局插件管理器实例
_plugin_manager: PluginManager = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = create_plugin_manager()
    return _plugin_manager


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("AI插件系统测试")
    print("=" * 60)

    manager = create_plugin_manager()

    print("\n已加载插件:")
    for plugin_info in manager.list_plugins():
        ai_tag = "[AI]" if plugin_info["ai_enhanced"] else ""
        print(f"  - {plugin_info['name']} v{plugin_info['version']} {ai_tag}")
        print(f"    {plugin_info['description']}")

    print("\nAI工具定义:")
    tools = manager.get_ai_tools()
    for tool in tools:
        print(f"  - {tool['function']['name']}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
