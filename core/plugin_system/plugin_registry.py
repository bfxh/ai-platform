#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件注册表 - 管理插件元数据和状态
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from .plugin_metadata import PluginConfig, PluginMetadata


class PluginRegistry:
    """插件注册表"""

    def __init__(self, registry_file: str = None):
        self.registry_file = registry_file or os.path.join(
            os.path.dirname(__file__), "..", "..", ".plugin_registry.json"
        )
        self.plugins: Dict[str, Dict] = {}
        self._load_registry()

    def _load_registry(self):
        """加载注册表"""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self.plugins = json.load(f)
            except Exception as e:
                print(f"[插件注册表] 加载失败: {e}")
                self.plugins = {}

    def _save_registry(self):
        """保存注册表"""
        try:
            os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self.plugins, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[插件注册表] 保存失败: {e}")

    def register(self, plugin_name: str, metadata: PluginMetadata, config: PluginConfig):
        """注册插件"""
        self.plugins[plugin_name] = {
            "metadata": {
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "author": metadata.author,
                "dependencies": metadata.dependencies,
                "ai_enhanced": metadata.ai_enhanced,
                "supported_providers": metadata.supported_providers,
                "category": metadata.category,
                "entry_point": metadata.entry_point,
                "homepage": metadata.homepage,
                "license": metadata.license,
            },
            "config": {
                "enabled": config.enabled,
                "settings": config.settings,
                "ai_provider": config.ai_provider,
                "ai_model": config.ai_model,
                "priority": config.priority,
            },
        }
        self._save_registry()

    def unregister(self, plugin_name: str):
        """注销插件"""
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            self._save_registry()

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict]:
        """获取插件信息"""
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        return list(self.plugins.values())

    def update_config(self, plugin_name: str, config: PluginConfig):
        """更新插件配置"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name]["config"] = {
                "enabled": config.enabled,
                "settings": config.settings,
                "ai_provider": config.ai_provider,
                "ai_model": config.ai_model,
                "priority": config.priority,
            }
            self._save_registry()

    def is_registered(self, plugin_name: str) -> bool:
        """检查插件是否已注册"""
        return plugin_name in self.plugins
