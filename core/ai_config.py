#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI配置管理 - 集中管理所有AI提供商的配置
支持: 环境变量、配置文件、运行时切换
"""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AIProviderConfig:
    """AI提供商配置"""

    name: str
    api_key: str = ""
    base_url: str = ""
    default_model: str = ""
    enabled: bool = True
    priority: int = 0  # 优先级，数字越小优先级越高
    extra_headers: Dict = None

    def __post_init__(self):
        if self.extra_headers is None:
            self.extra_headers = {}


class AIConfig:
    """
    AI配置管理器

    配置优先级:
    1. 运行时参数
    2. 环境变量
    3. 配置文件
    4. 默认值
    """

    # 默认配置
    DEFAULT_CONFIGS = {
        "stepfun": AIProviderConfig(
            name="stepfun", api_key="", base_url="https://api.stepfun.com/v1", default_model="step-1-8k", priority=1
        ),
        "openai": AIProviderConfig(
            name="openai", api_key="", base_url="https://api.openai.com/v1", default_model="gpt-4o-mini", priority=2
        ),
        "anthropic": AIProviderConfig(
            name="anthropic",
            api_key="",
            base_url="https://api.anthropic.com/v1",
            default_model="claude-3-5-sonnet-20241022",
            priority=3,
        ),
        "gemini": AIProviderConfig(
            name="gemini",
            api_key="",
            base_url="https://generativelanguage.googleapis.com/v1beta",
            default_model="gemini-2.0-flash",
            priority=4,
        ),
        "ollama": AIProviderConfig(
            name="ollama", api_key="", base_url="http://localhost:11434", default_model="llama3.2", priority=5
        ),
        "deepseek": AIProviderConfig(
            name="deepseek",
            api_key="",
            base_url="https://api.deepseek.com/v1",
            default_model="deepseek-chat",
            priority=6,
        ),
        "qwen": AIProviderConfig(
            name="qwen",
            api_key="",
            base_url="https://dashscope.aliyuncs.com/api/v1",
            default_model="qwen-max",
            priority=7,
        ),
        "doubao": AIProviderConfig(
            name="doubao",
            api_key="",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            default_model="doubao-pro-32k",
            priority=8,
        ),
        "xiaolongxia": AIProviderConfig(
            name="xiaolongxia",
            api_key="",
            base_url="https://api.crawdad.ai/v1",
            default_model="crawdad-chat",
            priority=9,
        ),
        "local_claude": AIProviderConfig(
            name="local_claude", api_key="", base_url="D:\\Claude_Extracted", default_model="claude-local", priority=10
        ),
    }

    # 环境变量映射
    ENV_MAPPING = {
        "stepfun": {
            "api_key": ["STEPFUN_API_KEY", "STEPFUN_KEY"],
            "base_url": ["STEPFUN_BASE_URL"],
            "default_model": ["STEPFUN_MODEL"],
        },
        "openai": {
            "api_key": ["OPENAI_API_KEY", "OPENAI_KEY"],
            "base_url": ["OPENAI_BASE_URL"],
            "default_model": ["OPENAI_MODEL"],
        },
        "anthropic": {
            "api_key": ["ANTHROPIC_API_KEY", "ANTHROPIC_KEY", "CLAUDE_API_KEY"],
            "base_url": ["ANTHROPIC_BASE_URL"],
            "default_model": ["ANTHROPIC_MODEL", "CLAUDE_MODEL"],
        },
        "gemini": {
            "api_key": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "base_url": ["GEMINI_BASE_URL"],
            "default_model": ["GEMINI_MODEL"],
        },
        "ollama": {
            "api_key": ["OLLAMA_API_KEY"],
            "base_url": ["OLLAMA_HOST", "OLLAMA_BASE_URL"],
            "default_model": ["OLLAMA_MODEL"],
        },
        "deepseek": {
            "api_key": ["DEEPSEEK_API_KEY", "DEEPSEEK_KEY"],
            "base_url": ["DEEPSEEK_BASE_URL"],
            "default_model": ["DEEPSEEK_MODEL"],
        },
        "qwen": {
            "api_key": ["QWEN_API_KEY", "DASHSCOPE_API_KEY"],
            "base_url": ["QWEN_BASE_URL", "DASHSCOPE_BASE_URL"],
            "default_model": ["QWEN_MODEL"],
        },
        "doubao": {
            "api_key": ["DOUBAO_API_KEY", "ARK_API_KEY"],
            "base_url": ["DOUBAO_BASE_URL", "ARK_BASE_URL"],
            "default_model": ["DOUBAO_MODEL"],
        },
        "xiaolongxia": {
            "api_key": ["XIAOLONGXIA_API_KEY", "CRAWDAD_API_KEY"],
            "base_url": ["XIAOLONGXIA_BASE_URL", "CRAWDAD_BASE_URL"],
            "default_model": ["XIAOLONGXIA_MODEL", "CRAWDAD_MODEL"],
        },
    }

    def __init__(self, config_path: str = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认 ~/.ai_config.json
        """
        self.config_path = config_path or self._get_default_config_path()
        self.providers: Dict[str, AIProviderConfig] = {}
        self.default_provider: str = "stepfun"
        self._load_all_configs()

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        home = Path.home()
        return str(home / ".ai_config.json")

    def _load_all_configs(self):
        """加载所有配置"""
        # 1. 加载默认配置
        for name, config in self.DEFAULT_CONFIGS.items():
            self.providers[name] = config

        # 2. 从环境变量加载
        self._load_from_env()

        # 3. 从配置文件加载
        self._load_from_file()

        # 4. 加载默认提供商设置
        self.default_provider = os.getenv("AI_PROVIDER", "stepfun")

    def _load_from_env(self):
        """从环境变量加载配置"""
        for provider_name, mappings in self.ENV_MAPPING.items():
            if provider_name not in self.providers:
                continue

            config = self.providers[provider_name]

            # API Key
            for env_var in mappings.get("api_key", []):
                value = os.getenv(env_var)
                if value:
                    config.api_key = value
                    break

            # Base URL
            for env_var in mappings.get("base_url", []):
                value = os.getenv(env_var)
                if value:
                    config.base_url = value
                    break

            # Default Model
            for env_var in mappings.get("default_model", []):
                value = os.getenv(env_var)
                if value:
                    config.default_model = value
                    break

    def _load_from_file(self):
        """从配置文件加载"""
        if not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 加载默认提供商
            if "default_provider" in data:
                self.default_provider = data["default_provider"]

            # 加载提供商配置
            for name, config_data in data.get("providers", {}).items():
                if name in self.providers:
                    # 更新现有配置
                    for key, value in config_data.items():
                        if hasattr(self.providers[name], key):
                            setattr(self.providers[name], key, value)
                else:
                    # 创建新配置
                    self.providers[name] = AIProviderConfig(name=name, **config_data)
        except Exception as e:
            print(f"[警告] 加载配置文件失败: {e}")

    def save_to_file(self, path: str = None):
        """保存配置到文件"""
        path = path or self.config_path

        data = {"default_provider": self.default_provider, "providers": {}}

        for name, config in self.providers.items():
            data["providers"][name] = {
                k: v for k, v in asdict(config).items() if k != "name"  # name作为key，不需要重复
            }

        # 确保目录存在
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 配置已保存到: {path}")

    def get_config(self, provider: str = None) -> AIProviderConfig:
        """获取指定提供商的配置"""
        provider = provider or self.default_provider
        if provider not in self.providers:
            raise ValueError(f"未知的AI提供商: {provider}")
        return self.providers[provider]

    def set_config(self, provider: str, **kwargs):
        """设置提供商配置"""
        if provider not in self.providers:
            # 创建新配置
            self.providers[provider] = AIProviderConfig(name=provider, **kwargs)
        else:
            # 更新现有配置
            for key, value in kwargs.items():
                if hasattr(self.providers[provider], key):
                    setattr(self.providers[provider], key, value)

    def set_default_provider(self, provider: str):
        """设置默认提供商"""
        if provider not in self.providers:
            raise ValueError(f"未知的AI提供商: {provider}")
        self.default_provider = provider
        os.environ["AI_PROVIDER"] = provider

    def list_providers(self) -> List[str]:
        """列出所有支持的提供商"""
        return list(self.providers.keys())

    def list_enabled_providers(self) -> List[str]:
        """列出已启用的提供商"""
        return [name for name, config in self.providers.items() if config.enabled]

    def get_available_providers(self) -> List[str]:
        """获取可用的提供商（有API Key的）"""
        available = []
        for name, config in self.providers.items():
            if config.enabled and (config.api_key or name in ["ollama", "xiaolongxia"]):
                available.append(name)
        return available

    def test_provider(self, provider: str = None) -> bool:
        """测试提供商连接"""
        provider = provider or self.default_provider
        config = self.get_config(provider)

        if not config.api_key and provider not in ["ollama", "xiaolongxia"]:
            print(f"❌ {provider}: 未配置API Key")
            return False

        try:
            # 根据提供商类型测试
            if provider == "ollama":
                import urllib.request

                req = urllib.request.Request(f"{config.base_url}/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.status == 200
            else:
                # 其他提供商通过实际请求测试
                from ai_adapter import AIClientFactory

                client = AIClientFactory.create(provider)
                response = client.chat(
                    type(
                        "Request",
                        (),
                        {
                            "messages": [type("Msg", (), {"role": "user", "content": "Hi"})],
                            "model": config.default_model,
                            "temperature": 0.7,
                            "max_tokens": 10,
                            "stream": False,
                            "tools": None,
                            "extra_params": {},
                        },
                    )()
                )
                return bool(response.content)
        except Exception as e:
            print(f"❌ {provider}: 连接失败 - {e}")
            return False

    def print_status(self):
        """打印配置状态"""
        print("\n" + "=" * 60)
        print("AI配置状态")
        print("=" * 60)
        print(f"默认提供商: {self.default_provider}")
        print(f"配置文件: {self.config_path}")
        print("\n提供商状态:")
        print("-" * 60)

        for name, config in sorted(self.providers.items(), key=lambda x: x[1].priority):
            status = "✅" if config.enabled else "❌"
            has_key = "🔑" if config.api_key or name == "ollama" else "  "
            print(f"{status} {has_key} {name:12} | 模型: {config.default_model:25} | 优先级: {config.priority}")

        print("\n可用提供商:", ", ".join(self.get_available_providers()))
        print("=" * 60)


# 全局配置实例
_config: Optional[AIConfig] = None


def get_config() -> AIConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = AIConfig()
    return _config


def set_default_provider(provider: str):
    """设置默认提供商"""
    get_config().set_default_provider(provider)


def get_provider_config(provider: str = None) -> AIProviderConfig:
    """获取提供商配置"""
    return get_config().get_config(provider)


# ============ 快捷命令 ============


def setup_provider(provider: str, api_key: str = None, base_url: str = None, model: str = None):
    """
    设置AI提供商

    Args:
        provider: 提供商名称
        api_key: API密钥
        base_url: 基础URL（可选）
        model: 默认模型（可选）
    """
    config = get_config()

    kwargs = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    if model:
        kwargs["default_model"] = model

    config.set_config(provider, **kwargs)
    config.save_to_file()

    print(f"✅ 已配置 {provider}")
    if api_key:
        print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
    if base_url:
        print(f"   Base URL: {base_url}")
    if model:
        print(f"   模型: {model}")


def switch_to(provider: str):
    """切换到指定提供商"""
    config = get_config()
    config.set_default_provider(provider)
    config.save_to_file()
    print(f"✅ 已切换到 {provider}")


def show_config():
    """显示当前配置"""
    get_config().print_status()


def init_config():
    """初始化配置向导"""
    print("\n" + "=" * 60)
    print("AI配置初始化向导")
    print("=" * 60)

    config = get_config()

    # 选择默认提供商
    print("\n支持的AI提供商:")
    for i, name in enumerate(config.list_providers(), 1):
        print(f"  {i}. {name}")

    choice = input("\n选择默认提供商 (输入序号或名称): ").strip()

    # 处理选择
    if choice.isdigit():
        idx = int(choice) - 1
        providers = config.list_providers()
        if 0 <= idx < len(providers):
            provider = providers[idx]
        else:
            print("❌ 无效选择")
            return
    else:
        provider = choice.lower()

    if provider not in config.providers:
        print(f"❌ 不支持的提供商: {provider}")
        return

    # 配置API Key
    print(f"\n配置 {provider}")
    api_key = input(f"请输入 {provider} 的API Key (直接回车跳过): ").strip()

    # 可选配置
    base_url = input(f"Base URL (直接回车使用默认): ").strip()
    model = input(f"默认模型 (直接回车使用默认): ").strip()

    # 保存配置
    setup_provider(provider=provider, api_key=api_key or None, base_url=base_url or None, model=model or None)

    switch_to(provider)

    print("\n✅ 配置完成!")
    config.print_status()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "init":
            init_config()
        elif command == "status":
            show_config()
        elif command == "switch" and len(sys.argv) > 2:
            switch_to(sys.argv[2])
        elif command == "set" and len(sys.argv) > 3:
            setup_provider(sys.argv[2], api_key=sys.argv[3])
        else:
            print("用法:")
            print("  python ai_config.py init           # 初始化配置")
            print("  python ai_config.py status         # 显示配置状态")
            print("  python ai_config.py switch <name>  # 切换提供商")
            print("  python ai_config.py set <name> <key> # 设置API Key")
    else:
        show_config()
