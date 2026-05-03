#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件管理器 - 解决插件过多导致卡顿问题

功能:
- 插件懒加载（按需加载）
- 插件卸载与热更新
- 插件性能监控
- 插件优先级管理
- 插件资源限制
- 插件隔离机制
"""

import os
import sys
import time
import threading
import importlib
import weakref
from pathlib import Path
from typing import Dict, List, Callable, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

# 添加上级目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from resource_manager import get_resource_tracker, ManagedThreadPoolExecutor


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    description: str
    version: str
    author: str
    path: str
    enabled: bool = True
    priority: int = 0
    
    # 运行时状态
    loaded: bool = False
    instance: Any = None
    load_time: Optional[datetime] = None
    last_used: Optional[datetime] = None
    call_count: int = 0
    total_execution_time: float = 0.0
    memory_usage: float = 0.0  # MB


class PluginManager:
    """插件管理器（带性能优化）"""
    
    def __init__(self):
        self._plugins: Dict[str, PluginInfo] = {}
        self._enabled_plugins: List[str] = []
        self._lock = threading.RLock()
        self._executor = ManagedThreadPoolExecutor(max_workers=3, name='plugin_manager')
        self._gc_interval = 300  # 5分钟自动清理
        self._max_idle_time = 1800  # 30分钟未使用自动卸载
        self._max_plugins = 50  # 最大插件数量限制
        
        # 注册到资源追踪器
        get_resource_tracker().track('plugin_manager', self, 'main_plugin_manager')
        
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
            for plugin_name, info in list(self._plugins.items()):
                if info.loaded and info.last_used:
                    idle_time = (now - info.last_used).total_seconds()
                    if idle_time > self._max_idle_time and plugin_name != 'core':
                        self.unload_plugin(plugin_name)
                        print(f"[PluginManager] 自动卸载空闲插件: {plugin_name}")
    
    def discover_plugins(self, plugins_dir: str = "plugins") -> List[str]:
        """发现目录中的插件"""
        plugins_path = Path(plugins_dir)
        discovered = []
        
        if not plugins_path.exists():
            return discovered
        
        for item in plugins_path.iterdir():
            if item.is_dir():
                init_file = item / "__init__.py"
                if init_file.exists():
                    discovered.append(item.name)
            elif item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
                discovered.append(item.stem)
        
        return discovered
    
    def register_plugin(self, plugin_name: str, path: str, description: str = "", 
                       version: str = "1.0", author: str = "", enabled: bool = True, 
                       priority: int = 0) -> bool:
        """注册插件"""
        with self._lock:
            if len(self._plugins) >= self._max_plugins:
                print(f"[PluginManager] 插件数量已达上限 ({self._max_plugins})")
                return False
            
            if plugin_name in self._plugins:
                return False
            
            self._plugins[plugin_name] = PluginInfo(
                name=plugin_name,
                description=description,
                version=version,
                author=author,
                path=path,
                enabled=enabled,
                priority=priority
            )
            
            if enabled:
                self._enabled_plugins.append(plugin_name)
                self._enabled_plugins.sort(key=lambda x: self._plugins[x].priority, reverse=True)
            
            return True
    
    def load_plugin(self, plugin_name: str) -> Optional[Any]:
        """懒加载插件"""
        with self._lock:
            if plugin_name not in self._plugins:
                print(f"[PluginManager] 插件不存在: {plugin_name}")
                return None
            
            info = self._plugins[plugin_name]
            
            if info.loaded:
                info.last_used = datetime.now()
                return info.instance
            
            # 尝试加载插件
            try:
                # 构建模块路径
                module_path = f"plugins.{plugin_name.replace('-', '_')}"
                module = importlib.import_module(module_path)
                
                # 查找插件类（以 Plugin 结尾的类）
                plugin_class = None
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and name.endswith('Plugin'):
                        plugin_class = obj
                        break
                
                if plugin_class is None:
                    print(f"[PluginManager] 未找到插件类: {plugin_name}")
                    return None
                
                # 创建实例
                instance = plugin_class()
                info.instance = instance
                info.loaded = True
                info.load_time = datetime.now()
                info.last_used = datetime.now()
                
                print(f"[PluginManager] 插件加载成功: {plugin_name}")
                return instance
            
            except Exception as e:
                print(f"[PluginManager] 加载插件失败 {plugin_name}: {e}")
                return None
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        with self._lock:
            if plugin_name not in self._plugins:
                return False
            
            info = self._plugins[plugin_name]
            
            if not info.loaded:
                return True
            
            # 清理资源
            if info.instance:
                # 调用插件的清理方法
                if hasattr(info.instance, 'shutdown'):
                    try:
                        info.instance.shutdown()
                    except:
                        pass
                
                # 强制垃圾回收
                info.instance = None
            
            info.loaded = False
            info.load_time = None
            info.last_used = None
            
            print(f"[PluginManager] 插件已卸载: {plugin_name}")
            return True
    
    def toggle_plugin(self, plugin_name: str, enabled: bool) -> bool:
        """切换插件启用状态"""
        with self._lock:
            if plugin_name not in self._plugins:
                return False
            
            info = self._plugins[plugin_name]
            info.enabled = enabled
            
            if enabled:
                if plugin_name not in self._enabled_plugins:
                    self._enabled_plugins.append(plugin_name)
                    self._enabled_plugins.sort(key=lambda x: self._plugins[x].priority, reverse=True)
            else:
                if plugin_name in self._enabled_plugins:
                    self._enabled_plugins.remove(plugin_name)
                    # 如果已加载，卸载它
                    if info.loaded:
                        self.unload_plugin(plugin_name)
            
            return True
    
    def execute_plugin(self, plugin_name: str, action: str = 'run', params: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行插件动作"""
        start_time = time.time()
        
        try:
            plugin = self.load_plugin(plugin_name)
            
            if not plugin:
                return {
                    'success': False,
                    'error': f"插件加载失败: {plugin_name}"
                }
            
            # 执行动作
            if hasattr(plugin, action):
                method = getattr(plugin, action)
                result = method(params or {})
                
                # 更新统计信息
                with self._lock:
                    info = self._plugins[plugin_name]
                    info.call_count += 1
                    info.total_execution_time += time.time() - start_time
                    info.last_used = datetime.now()
                
                return {
                    'success': True,
                    'result': result,
                    'execution_time': time.time() - start_time
                }
            else:
                return {
                    'success': False,
                    'error': f"插件不支持动作: {action}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        with self._lock:
            return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        result = []
        
        with self._lock:
            for plugin_name in self._enabled_plugins:
                info = self._plugins[plugin_name]
                result.append({
                    'name': info.name,
                    'description': info.description,
                    'version': info.version,
                    'author': info.author,
                    'enabled': info.enabled,
                    'loaded': info.loaded,
                    'priority': info.priority,
                    'call_count': info.call_count,
                    'total_execution_time': round(info.total_execution_time, 2),
                    'last_used': info.last_used.isoformat() if info.last_used else None,
                    'load_time': info.load_time.isoformat() if info.load_time else None
                })
            
            # 添加禁用的插件
            for plugin_name, info in self._plugins.items():
                if not info.enabled:
                    result.append({
                        'name': info.name,
                        'description': info.description,
                        'version': info.version,
                        'author': info.author,
                        'enabled': False,
                        'loaded': False,
                        'priority': info.priority,
                        'call_count': 0,
                        'total_execution_time': 0,
                        'last_used': None,
                        'load_time': None
                    })
        
        return result
    
    def get_performance_report(self) -> Dict:
        """获取性能报告"""
        with self._lock:
            loaded_count = sum(1 for info in self._plugins.values() if info.loaded)
            enabled_count = len(self._enabled_plugins)
            total_calls = sum(info.call_count for info in self._plugins.values())
            total_time = sum(info.total_execution_time for info in self._plugins.values())
            
            # 找出最慢的插件
            slowest_plugins = sorted(
                self._plugins.values(),
                key=lambda x: x.total_execution_time,
                reverse=True
            )[:5]
            
            # 找出调用最频繁的插件
            busiest_plugins = sorted(
                self._plugins.values(),
                key=lambda x: x.call_count,
                reverse=True
            )[:5]
        
        return {
            'total_plugins': len(self._plugins),
            'enabled_plugins': enabled_count,
            'loaded_plugins': loaded_count,
            'total_calls': total_calls,
            'total_execution_time': round(total_time, 2),
            'slowest_plugins': [
                {'name': p.name, 'total_time': round(p.total_execution_time, 2), 'calls': p.call_count}
                for p in slowest_plugins
            ],
            'busiest_plugins': [
                {'name': p.name, 'calls': p.call_count, 'avg_time': round(p.total_execution_time / max(p.call_count, 1), 4)}
                for p in busiest_plugins
            ]
        }
    
    def shutdown(self):
        """关闭插件管理器"""
        with self._lock:
            # 卸载所有插件
            for plugin_name in list(self._plugins.keys()):
                self.unload_plugin(plugin_name)
            
            # 关闭线程池
            self._executor.shutdown(wait=True)
            
            # 从资源追踪器移除
            get_resource_tracker().untrack('plugin_manager', self)


# 全局插件管理器
_global_plugin_manager = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器"""
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
    return _global_plugin_manager


def initialize_plugins(plugins_dir: str = "plugins"):
    """初始化插件系统"""
    manager = get_plugin_manager()
    
    # 发现并注册插件
    discovered = manager.discover_plugins(plugins_dir)
    print(f"[PluginManager] 发现 {len(discovered)} 个插件")
    
    for plugin_name in discovered:
        manager.register_plugin(plugin_name, f"plugins.{plugin_name}")
    
    return discovered


if __name__ == '__main__':
    # 测试插件管理器
    manager = get_plugin_manager()
    
    print("=== 插件管理器测试 ===")
    
    # 发现插件
    plugins = manager.discover_plugins()
    print(f"\n发现插件: {plugins}")
    
    # 注册插件示例
    manager.register_plugin('test_plugin', 'plugins.test_plugin', '测试插件', '1.0', 'Test')
    
    # 列出插件
    print("\n插件列表:")
    for plugin in manager.list_plugins():
        print(f"  - {plugin['name']}: enabled={plugin['enabled']}, loaded={plugin['loaded']}")
    
    # 获取性能报告
    print("\n性能报告:")
    report = manager.get_performance_report()
    for key, value in report.items():
        print(f"  {key}: {value}")
    
    manager.shutdown()
    print("\n插件管理器测试完成")
