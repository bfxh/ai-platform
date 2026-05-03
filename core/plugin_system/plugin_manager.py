#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件管理器 - 核心功能实现
"""

import importlib
import importlib.util
import os
import shutil
import sys
import tempfile
import threading
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from .plugin_base import BasePlugin, ConnectorPlugin, EnhancerPlugin, ToolPlugin
from .plugin_metadata import PluginConfig, PluginMetadata
from .plugin_registry import PluginRegistry


@dataclass
class PluginInstance:
    """插件实例"""

    plugin: BasePlugin
    loaded: bool = False
    load_time: Optional[datetime] = None
    last_used: Optional[datetime] = None
    call_count: int = 0
    total_execution_time: float = 0.0
    memory_usage: float = 0.0  # MB


class PluginManager:
    """插件管理器"""

    def __init__(self, plugin_dir: str = None, ai_client=None):
        self.plugin_dir = plugin_dir or os.path.join(os.path.dirname(__file__), "..", "..", "plugins")
        self.ai_client = ai_client
        self.plugin_instances: Dict[str, PluginInstance] = {}
        self.plugin_registry = PluginRegistry()
        self._lock = threading.RLock()
        self._gc_interval = 300  # 5分钟自动清理
        self._max_idle_time = 1800  # 30分钟未使用自动卸载
        self._max_plugins = 100  # 最大插件数量限制

        # 确保插件目录存在
        os.makedirs(self.plugin_dir, exist_ok=True)

        # 启动垃圾回收线程
        self._gc_thread = threading.Thread(target=self._gc_loop, daemon=True)
        self._gc_thread.start()

    def _gc_loop(self):
        """垃圾回收循环"""
        while True:
            time.sleep(self._gc_interval)
            self._cleanup_idle_plugins()

    def _cleanup_idle_plugins(self):
        """清理长时间未使用的插件"""
        with self._lock:
            now = datetime.now()
            for plugin_name, instance in list(self.plugin_instances.items()):
                if instance.loaded and instance.last_used:
                    idle_time = (now - instance.last_used).total_seconds()
                    if idle_time > self._max_idle_time:
                        self.unload_plugin(plugin_name)
                        print(f"[插件管理器] 自动卸载空闲插件: {plugin_name}")

    def install_plugin(self, plugin_path: str) -> bool:
        """安装插件

        Args:
            plugin_path: 插件文件路径（支持.py文件或.zip包）

        Returns:
            bool: 安装是否成功
        """
        try:
            if plugin_path.endswith(".zip"):
                # 解压插件包
                with tempfile.TemporaryDirectory() as temp_dir:
                    with zipfile.ZipFile(plugin_path, "r") as zip_ref:
                        zip_ref.extractall(temp_dir)

                    # 查找插件元数据
                    plugin_info = self._detect_plugin(temp_dir)
                    if not plugin_info:
                        print("[插件管理器] 未找到有效的插件")
                        return False

                    # 复制到插件目录
                    plugin_name = plugin_info["metadata"].name
                    target_dir = os.path.join(self.plugin_dir, plugin_name)
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir)
                    shutil.copytree(temp_dir, target_dir)

                    # 注册插件
                    self.register_plugin(plugin_name, target_dir, plugin_info["metadata"], plugin_info["config"])

            elif plugin_path.endswith(".py"):
                # 单个插件文件
                plugin_name = os.path.basename(plugin_path).replace(".py", "")
                target_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
                shutil.copy2(plugin_path, target_path)

                # 加载并注册
                plugin_info = self._detect_plugin(target_path)
                if plugin_info:
                    self.register_plugin(plugin_name, target_path, plugin_info["metadata"], plugin_info["config"])
                else:
                    print("[插件管理器] 无效的插件文件")
                    return False

            else:
                print("[插件管理器] 不支持的插件格式")
                return False

            print(f"[插件管理器] 插件安装成功: {plugin_name}")
            return True
        except Exception as e:
            print(f"[插件管理器] 安装插件失败: {e}")
            return False

    def uninstall_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        with self._lock:
            if plugin_name in self.plugin_instances:
                # 先卸载
                self.unload_plugin(plugin_name)
                # 从注册表移除
                self.plugin_registry.unregister(plugin_name)
                # 删除文件
                plugin_path = self.plugin_instances[plugin_name].plugin.metadata.entry_point
                if os.path.isdir(plugin_path):
                    shutil.rmtree(plugin_path)
                elif os.path.isfile(plugin_path):
                    os.remove(plugin_path)
                # 从实例列表移除
                del self.plugin_instances[plugin_name]
                print(f"[插件管理器] 插件卸载成功: {plugin_name}")
                return True
            return False

    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        with self._lock:
            if plugin_name in self.plugin_instances:
                instance = self.plugin_instances[plugin_name]
                instance.plugin.config.enabled = True
                self.plugin_registry.update_config(plugin_name, instance.plugin.config)
                print(f"[插件管理器] 插件已启用: {plugin_name}")
                return True
            return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        with self._lock:
            if plugin_name in self.plugin_instances:
                instance = self.plugin_instances[plugin_name]
                instance.plugin.config.enabled = False
                # 如果已加载，卸载它
                if instance.loaded:
                    self.unload_plugin(plugin_name)
                self.plugin_registry.update_config(plugin_name, instance.plugin.config)
                print(f"[插件管理器] 插件已禁用: {plugin_name}")
                return True
            return False

    def register_plugin(self, plugin_name: str, path: str, metadata: PluginMetadata, config: PluginConfig):
        """注册插件"""
        with self._lock:
            if len(self.plugin_instances) >= self._max_plugins:
                print(f"[插件管理器] 插件数量已达上限 ({self._max_plugins})")
                return

            # 创建插件实例
            plugin = self._load_plugin_class(path, metadata)
            if plugin:
                plugin.metadata = metadata
                plugin.config = config
                if self.ai_client and metadata.ai_enhanced:
                    plugin.set_ai_client(self.ai_client)

                self.plugin_instances[plugin_name] = PluginInstance(plugin=plugin, loaded=False)

                # 注册到注册表
                self.plugin_registry.register(plugin_name, metadata, config)
                print(f"[插件管理器] 插件注册成功: {plugin_name}")

    def load_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """加载插件"""
        with self._lock:
            if plugin_name not in self.plugin_instances:
                print(f"[插件管理器] 插件不存在: {plugin_name}")
                return None

            instance = self.plugin_instances[plugin_name]

            if instance.loaded:
                instance.last_used = datetime.now()
                return instance.plugin

            # 检查是否启用
            if not instance.plugin.config.enabled:
                print(f"[插件管理器] 插件已禁用: {plugin_name}")
                return None

            # 初始化插件
            try:
                instance.plugin.initialize(instance.plugin.config.settings)
                instance.loaded = True
                instance.load_time = datetime.now()
                instance.last_used = datetime.now()
                print(f"[插件管理器] 插件加载成功: {plugin_name}")
                return instance.plugin
            except Exception as e:
                print(f"[插件管理器] 加载插件失败 {plugin_name}: {e}")
                return None

    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        with self._lock:
            if plugin_name not in self.plugin_instances:
                return False

            instance = self.plugin_instances[plugin_name]

            if not instance.loaded:
                return True

            # 清理资源
            try:
                instance.plugin.shutdown()
            except Exception as e:
                print(f"[插件管理器] 关闭插件失败 {plugin_name}: {e}")

            instance.loaded = False
            instance.load_time = None
            instance.last_used = None
            print(f"[插件管理器] 插件已卸载: {plugin_name}")
            return True

    def execute_plugin(self, plugin_name: str, input_data: Any, **kwargs) -> Dict[str, Any]:
        """执行插件"""
        start_time = time.time()

        try:
            plugin = self.load_plugin(plugin_name)

            if not plugin:
                return {"success": False, "error": f"插件加载失败: {plugin_name}"}

            # 执行
            result = plugin.execute(input_data, **kwargs)

            # 更新统计信息
            with self._lock:
                instance = self.plugin_instances[plugin_name]
                instance.call_count += 1
                instance.total_execution_time += time.time() - start_time
                instance.last_used = datetime.now()

            return {"success": True, "result": result, "execution_time": time.time() - start_time}
        except Exception as e:
            return {"success": False, "error": str(e), "execution_time": time.time() - start_time}

    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        result = []

        with self._lock:
            for plugin_name, instance in self.plugin_instances.items():
                plugin = instance.plugin
                result.append(
                    {
                        "name": plugin.metadata.name,
                        "version": plugin.metadata.version,
                        "description": plugin.metadata.description,
                        "category": plugin.metadata.category,
                        "enabled": plugin.config.enabled,
                        "loaded": instance.loaded,
                        "ai_enhanced": plugin.metadata.ai_enhanced,
                        "priority": plugin.config.priority,
                        "call_count": instance.call_count,
                        "total_execution_time": round(instance.total_execution_time, 2),
                        "last_used": instance.last_used.isoformat() if instance.last_used else None,
                        "load_time": instance.load_time.isoformat() if instance.load_time else None,
                    }
                )

        return result

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        with self._lock:
            instance = self.plugin_instances.get(plugin_name)
            return instance.plugin if instance else None

    def get_performance_report(self) -> Dict:
        """获取性能报告"""
        with self._lock:
            loaded_count = sum(1 for instance in self.plugin_instances.values() if instance.loaded)
            enabled_count = sum(1 for instance in self.plugin_instances.values() if instance.plugin.config.enabled)
            total_calls = sum(instance.call_count for instance in self.plugin_instances.values())
            total_time = sum(instance.total_execution_time for instance in self.plugin_instances.values())

            # 找出最慢的插件
            slowest_plugins = sorted(
                self.plugin_instances.values(), key=lambda x: x.total_execution_time, reverse=True
            )[:5]

            # 找出调用最频繁的插件
            busiest_plugins = sorted(self.plugin_instances.values(), key=lambda x: x.call_count, reverse=True)[:5]

        return {
            "total_plugins": len(self.plugin_instances),
            "enabled_plugins": enabled_count,
            "loaded_plugins": loaded_count,
            "total_calls": total_calls,
            "total_execution_time": round(total_time, 2),
            "slowest_plugins": [
                {"name": p.plugin.metadata.name, "total_time": round(p.total_execution_time, 2), "calls": p.call_count}
                for p in slowest_plugins
            ],
            "busiest_plugins": [
                {
                    "name": p.plugin.metadata.name,
                    "calls": p.call_count,
                    "avg_time": round(p.total_execution_time / max(p.call_count, 1), 4),
                }
                for p in busiest_plugins
            ],
        }

    def _detect_plugin(self, path: str) -> Optional[Dict]:
        """检测插件信息"""
        try:
            if os.path.isdir(path):
                # 目录插件
                init_file = os.path.join(path, "__init__.py")
                if not os.path.exists(init_file):
                    return None
                spec = importlib.util.spec_from_file_location("plugin", init_file)
            else:
                # 单个文件插件
                spec = importlib.util.spec_from_file_location("plugin", path)

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
                    if plugin.metadata:
                        return {"metadata": plugin.metadata, "config": plugin.config}

            return None
        except Exception as e:
            print(f"[插件管理器] 检测插件失败: {e}")
            return None

    def _load_plugin_class(self, path: str, metadata: PluginMetadata) -> Optional[BasePlugin]:
        """加载插件类"""
        try:
            if os.path.isdir(path):
                init_file = os.path.join(path, metadata.entry_point)
                spec = importlib.util.spec_from_file_location("plugin", init_file)
            else:
                spec = importlib.util.spec_from_file_location("plugin", path)

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
                    return attr()

            return None
        except Exception as e:
            print(f"[插件管理器] 加载插件类失败: {e}")
            return None

    def shutdown(self):
        """关闭插件管理器"""
        with self._lock:
            # 卸载所有插件
            for plugin_name in list(self.plugin_instances.keys()):
                self.unload_plugin(plugin_name)

    def scan_plugins(self):
        """扫描插件目录并注册插件"""
        for item in os.listdir(self.plugin_dir):
            item_path = os.path.join(self.plugin_dir, item)
            if os.path.isdir(item_path) or item.endswith(".py"):
                plugin_info = self._detect_plugin(item_path)
                if plugin_info:
                    plugin_name = plugin_info["metadata"].name
                    if not self.plugin_registry.is_registered(plugin_name):
                        self.register_plugin(plugin_name, item_path, plugin_info["metadata"], plugin_info["config"])
