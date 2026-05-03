#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置管理模块
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """
    统一配置管理
    - 支持环境变量
    - 支持配置文件
    - 支持默认值
    - 动态配置加载
    """

    def __init__(self):
        self._config = {}
        self._config_files = []
        self._base_dir = self._get_base_dir()
        self._load_configs()

    def _get_base_dir(self) -> Path:
        """获取项目根目录"""
        # 尝试从环境变量获取
        if "AI_BASE_DIR" in os.environ:
            return Path(os.environ["AI_BASE_DIR"])

        # 从当前文件路径推断
        current_file = Path(__file__)
        # 找到项目根目录（python/ 目录或包含 ai_architecture.json 的目录）
        for parent in current_file.parents:
            if parent.name == "python" or (parent / "ai_architecture.json").exists():
                return parent

        # 默认返回当前目录
        return Path.cwd()

    def _load_configs(self):
        """加载所有配置文件"""
        # 加载默认配置
        self._load_default_config()

        # 加载配置文件
        config_paths = [
            self._base_dir / "config" / "master_config.json",
            self._base_dir / "config.json",
            self._base_dir / "test_config.json",
        ]

        for config_path in config_paths:
            if config_path.exists():
                self._load_config_file(config_path)

        # 加载环境变量配置
        self._load_env_config()

    def _load_default_config(self):
        """加载默认配置"""
        self._config.update(
            {
                "base_dir": str(self._base_dir),
                "core_dir": str(self._base_dir / "core"),
                "tools_dir": str(self._base_dir / "tools"),
                "plugins_dir": str(self._base_dir / "plugins"),
                "config_dir": str(self._base_dir / "config"),
                "ai": {"default_provider": "stepfun", "timeout": 120, "max_tokens": 2000, "temperature": 0.7},
                "workflow": {"timeout": 300, "max_retries": 3},
                "logging": {"level": "INFO", "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
            }
        )

    def _load_config_file(self, config_path: Path):
        """加载配置文件"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self._merge_config(self._config, config)
                self._config_files.append(str(config_path))
        except Exception as e:
            print(f"[警告] 加载配置文件失败: {config_path}, 错误: {e}")

    def _load_env_config(self):
        """加载环境变量配置"""
        # 加载AI相关环境变量
        if "AI_PROVIDER" in os.environ:
            self._config["ai"]["default_provider"] = os.environ["AI_PROVIDER"]

        if "AI_TIMEOUT" in os.environ:
            try:
                self._config["ai"]["timeout"] = int(os.environ["AI_TIMEOUT"])
            except ValueError:
                pass

        # 加载路径相关环境变量
        for key in ["AI_BASE_DIR", "AI_CORE_DIR", "AI_TOOLS_DIR", "AI_PLUGINS_DIR"]:
            if key in os.environ:
                config_key = key.lower().replace("ai_", "").replace("_dir", "")
                if config_key in self._config:
                    self._config[config_key] = os.environ[key]

    def _merge_config(self, target: Dict, source: Dict):
        """合并配置"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split(".")
        config = self._config

        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_base_dir(self) -> Path:
        """获取项目根目录"""
        return Path(self._config["base_dir"])

    def get_core_dir(self) -> Path:
        """获取核心目录"""
        return Path(self._config["core_dir"])

    def get_tools_dir(self) -> Path:
        """获取工具目录"""
        return Path(self._config["tools_dir"])

    def get_plugins_dir(self) -> Path:
        """获取插件目录"""
        return Path(self._config["plugins_dir"])

    def get_config_dir(self) -> Path:
        """获取配置目录"""
        return Path(self._config["config_dir"])

    def add_sys_path(self):
        """添加系统路径"""
        core_dir = self.get_core_dir()
        tools_dir = self.get_tools_dir()

        if str(core_dir) not in sys.path:
            sys.path.insert(0, str(core_dir))

        if str(tools_dir) not in sys.path:
            sys.path.insert(1, str(tools_dir))

    def print_status(self):
        """打印配置状态"""
        print("=" * 60)
        print("配置管理状态")
        print("=" * 60)
        print(f"项目根目录: {self._base_dir}")
        print(f"加载的配置文件: {len(self._config_files)}")
        for config_file in self._config_files:
            print(f"  - {config_file}")
        print(f"默认AI提供商: {self.get('ai.default_provider')}")
        print(f"AI超时设置: {self.get('ai.timeout')}秒")
        print("=" * 60)

    def get_available_providers(self) -> list:
        """获取可用的AI提供商"""
        return ["stepfun", "openai", "anthropic", "gemini", "ollama", "deepseek", "qwen", "doubao", "xiaolongxia"]


# 全局配置管理器实例
config_manager = ConfigManager()

# 导出常用函数
get_config = config_manager.get
set_config = config_manager.set
get_base_dir = config_manager.get_base_dir
get_core_dir = config_manager.get_core_dir
get_tools_dir = config_manager.get_tools_dir
get_plugins_dir = config_manager.get_plugins_dir
get_config_dir = config_manager.get_config_dir
add_sys_path = config_manager.add_sys_path
print_status = config_manager.print_status
get_available_providers = config_manager.get_available_providers

# 自动添加系统路径
add_sys_path()


if __name__ == "__main__":
    # 测试配置管理器
    print("配置管理器测试")
    print(f"项目根目录: {get_base_dir()}")
    print(f"核心目录: {get_core_dir()}")
    print(f"工具目录: {get_tools_dir()}")
    print(f"默认AI提供商: {get_config('ai.default_provider')}")
    print(f"AI超时设置: {get_config('ai.timeout')}")
    print(f"可用的AI提供商: {get_available_providers()}")
    print_status()
