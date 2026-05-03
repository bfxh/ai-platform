#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置中心

集中管理所有MCP工具的配置

用法:
    from config_center import config
    
    # 获取配置
    api_key = config.get("meshy", "api_key")
    
    # 设置配置
    config.set("meshy", "api_key", "new_key")
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
import threading

# 配置目录
CONFIG_DIR = Path("/python/Config")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class ServiceConfig:
    """服务配置数据类"""
    name: str
    enabled: bool = True
    timeout: int = 30
    retry_count: int = 3
    
    # API配置
    api_key: str = ""
    base_url: str = ""
    
    # GPU配置
    use_gpu: bool = True
    gpu_memory_threshold: float = 7.0  # GB
    
    # 其他配置
    custom: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom is None:
            self.custom = {}

class ConfigCenter:
    """配置中心"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._configs: Dict[str, Dict] = {}
        self._load_all()
    
    def _get_config_file(self, service: str) -> Path:
        """获取配置文件路径"""
        return CONFIG_DIR / f"{service}.json"
    
    def _load_all(self):
        """加载所有配置"""
        for config_file in CONFIG_DIR.glob("*.json"):
            service = config_file.stem
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._configs[service] = json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to load config {service}: {e}")
                self._configs[service] = {}
    
    def get(self, service: str, key: str = None, default: Any = None) -> Any:
        """
        获取配置
        
        Args:
            service: 服务名称
            key: 配置键，None返回整个配置
            default: 默认值
        
        Returns:
            配置值
        """
        # 首先检查环境变量
        env_key = f"{service.upper()}_{key.upper()}" if key else None
        if env_key and env_key in os.environ:
            return os.environ[env_key]
        
        # 然后检查配置文件
        config = self._configs.get(service, {})
        
        if key is None:
            return config
        
        return config.get(key, default)
    
    def set(self, service: str, key: str, value: Any):
        """
        设置配置
        
        Args:
            service: 服务名称
            key: 配置键
            value: 配置值
        """
        if service not in self._configs:
            self._configs[service] = {}
        
        self._configs[service][key] = value
        self._save(service)
    
    def set_multi(self, service: str, config: Dict[str, Any]):
        """
        批量设置配置
        
        Args:
            service: 服务名称
            config: 配置字典
        """
        self._configs[service] = config
        self._save(service)
    
    def _save(self, service: str):
        """保存配置到文件"""
        config_file = self._get_config_file(service)
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self._configs[service], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save config {service}: {e}")
    
    def get_service_config(self, service: str) -> ServiceConfig:
        """
        获取服务配置对象
        
        Args:
            service: 服务名称
        
        Returns:
            ServiceConfig对象
        """
        config = self._configs.get(service, {})
        return ServiceConfig(
            name=service,
            enabled=config.get("enabled", True),
            timeout=config.get("timeout", 30),
            retry_count=config.get("retry_count", 3),
            api_key=config.get("api_key", ""),
            base_url=config.get("base_url", ""),
            use_gpu=config.get("use_gpu", True),
            gpu_memory_threshold=config.get("gpu_memory_threshold", 7.0),
            custom=config.get("custom", {})
        )
    
    def list_services(self) -> list:
        """列出所有服务"""
        return list(self._configs.keys())
    
    def reload(self):
        """重新加载所有配置"""
        self._configs.clear()
        self._load_all()

# 全局配置实例
config = ConfigCenter()

# 使用示例
if __name__ == "__main__":
    # 设置配置
    config.set("meshy", "api_key", "test_key")
    config.set("meshy", "timeout", 60)
    
    # 获取配置
    api_key = config.get("meshy", "api_key")
    timeout = config.get("meshy", "timeout", 30)
    
    print(f"API Key: {api_key}")
    print(f"Timeout: {timeout}")
    
    # 获取整个配置
    meshy_config = config.get("meshy")
    print(f"Full config: {meshy_config}")
    
    # 列出所有服务
    services = config.list_services()
    print(f"Services: {services}")
