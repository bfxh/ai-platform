#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 配置管理器（已修复资源泄漏）

功能:
- 配置加载与合并
- 配置文件监听
- 观察者管理
- 配置版本控制
- 资源泄漏防护
"""

import os
import json
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))

from resource_manager import ObserverManager, get_resource_tracker


@dataclass
class ConfigVersion:
    """配置版本"""
    version: str
    timestamp: float
    config: Dict[str, Any]


class ConfigManager:
    """配置管理器（已修复资源泄漏）"""
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._config_files: List[str] = []
        self._watchers: Dict[str, threading.Thread] = {}
        self._reload_callbacks: List[Callable] = []
        self._lock = threading.RLock()
        self._version_history: List[ConfigVersion] = []
        self._max_history = 10
        
        # 使用观察者管理器
        self._observer_manager = ObserverManager()
        
        # 注册到资源追踪器
        get_resource_tracker().track('config_manager', self, 'main_manager')
    
    def load(self, config_file: str, section: Optional[str] = None):
        """加载配置文件"""
        if not os.path.exists(config_file):
            print(f"[ConfigManager] 配置文件不存在: {config_file}")
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            with self._lock:
                # 如果指定了section，只加载该部分
                if section:
                    if section in config_data:
                        self._config[section] = config_data[section]
                    else:
                        print(f"[ConfigManager] 配置文件中不存在 section: {section}")
                else:
                    # 深度合并配置
                    self._config = self._deep_merge(self._config, config_data)
                
                # 记录版本
                self._record_version()
                
                # 添加到监控列表
                if config_file not in self._config_files:
                    self._config_files.append(config_file)
                
                print(f"[ConfigManager] 配置文件加载成功: {config_file}")
                
        except Exception as e:
            print(f"[ConfigManager] 加载配置文件失败 {config_file}: {e}")
    
    def load_from_directory(self, config_dir: str):
        """从目录加载所有配置文件"""
        config_path = Path(config_dir)
        
        if not config_path.exists():
            return
        
        for item in config_path.iterdir():
            if item.is_file() and item.suffix == ".json":
                self.load(str(item))
            elif item.is_dir():
                self.load_from_directory(str(item))
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        
        with self._lock:
            for i, k in enumerate(keys[:-1]):
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
            self._record_version()
            
            # 通知观察者
            self._observer_manager.notify('config_changed', key, value)
            
            # 执行回调
            for callback in self._reload_callbacks:
                try:
                    callback(key, value)
                except Exception as e:
                    print(f"[ConfigManager] 回调执行失败: {e}")
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """深度合并配置"""
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _record_version(self):
        """记录配置版本"""
        version = ConfigVersion(
            version=f"v{len(self._version_history) + 1}",
            timestamp=time.time(),
            config=self._config.copy()
        )
        
        self._version_history.append(version)
        
        # 保持历史记录限制
        if len(self._version_history) > self._max_history:
            self._version_history = self._version_history[-self._max_history:]
    
    def get_version(self, version_index: int = -1) -> Optional[ConfigVersion]:
        """获取指定版本的配置"""
        if version_index < 0:
            version_index = len(self._version_history) + version_index
        
        if 0 <= version_index < len(self._version_history):
            return self._version_history[version_index]
        
        return None
    
    def rollback(self, version_index: int = -1):
        """回滚到指定版本"""
        version = self.get_version(version_index)
        
        if version:
            with self._lock:
                self._config = version.config.copy()
                self._record_version()
                return True
        
        return False
    
    def watch(self, config_file: str, callback: Optional[Callable] = None):
        """监控配置文件变化"""
        if not os.path.exists(config_file):
            return
        
        # 注册观察者
        observer_id = f"file_{config_file}"
        self._observer_manager.register(observer_id, config_file, callback)
        
        # 创建监控线程
        if config_file not in self._watchers:
            def watch_thread():
                last_modified = os.path.getmtime(config_file)
                
                while config_file in self._watchers:
                    try:
                        current_modified = os.path.getmtime(config_file)
                        
                        if current_modified > last_modified:
                            last_modified = current_modified
                            
                            # 重新加载配置
                            self.load(config_file)
                            
                            # 通知观察者
                            self._observer_manager.notify(observer_id, config_file)
                            
                            print(f"[ConfigManager] 配置文件已更新: {config_file}")
                    
                    except Exception as e:
                        print(f"[ConfigManager] 监控文件失败 {config_file}: {e}")
                    
                    time.sleep(1)
            
            thread = threading.Thread(target=watch_thread, daemon=True)
            thread.start()
            self._watchers[config_file] = thread
    
    def unwatch(self, config_file: str):
        """停止监控配置文件"""
        observer_id = f"file_{config_file}"
        self._observer_manager.unregister(observer_id)
        
        if config_file in self._watchers:
            del self._watchers[config_file]
    
    def register_callback(self, callback: Callable):
        """注册配置变更回调"""
        if callback not in self._reload_callbacks:
            self._reload_callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable):
        """注销配置变更回调"""
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)
    
    def save(self, config_file: str):
        """保存配置到文件"""
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            
            print(f"[ConfigManager] 配置保存成功: {config_file}")
        except Exception as e:
            print(f"[ConfigManager] 保存配置失败 {config_file}: {e}")
    
    def dump(self) -> Dict[str, Any]:
        """导出完整配置"""
        return self._config.copy()
    
    def clear(self):
        """清空配置"""
        with self._lock:
            self._config.clear()
            self._version_history.clear()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'config_keys_count': len(self._config),
            'config_files_count': len(self._config_files),
            'watchers_count': len(self._watchers),
            'version_history_count': len(self._version_history),
            'callback_count': len(self._reload_callbacks),
            'observer_count': self._observer_manager.get_observer_count()
        }
    
    def shutdown(self):
        """关闭管理器"""
        # 停止所有监控线程
        self._watchers.clear()
        
        # 清理观察者
        self._observer_manager.cleanup()
        
        # 清理回调
        self._reload_callbacks.clear()
        
        get_resource_tracker().untrack('config_manager', self)


if __name__ == '__main__':
    # 测试配置管理器
    config_manager = ConfigManager()
    
    print("配置管理器测试")
    
    # 加载配置
    test_config = {
        'app': {
            'name': 'TestApp',
            'version': '1.0'
        },
        'database': {
            'host': 'localhost',
            'port': 5432
        }
    }
    
    # 模拟加载配置
    config_manager._config = test_config
    
    print(f"\n1. 配置内容: {config_manager.dump()}")
    
    # 获取配置
    print(f"\n2. 获取配置 app.name: {config_manager.get('app.name')}")
    print(f"   获取配置 database.port: {config_manager.get('database.port')}")
    print(f"   获取不存在的配置: {config_manager.get('nonexistent.key', 'default')}")
    
    # 设置配置
    config_manager.set('app.debug', True)
    print(f"\n3. 设置后配置: {config_manager.dump()}")
    
    # 注册回调
    def on_config_change(key, value):
        print(f"[回调] 配置变更: {key} = {value}")
    
    config_manager.register_callback(on_config_change)
    
    # 再次设置
    config_manager.set('database.host', '192.168.1.100')
    
    # 获取版本历史
    print(f"\n4. 版本历史数量: {len(config_manager._version_history)}")
    
    # 获取统计信息
    print(f"\n5. 统计信息: {config_manager.get_stats()}")
    
    config_manager.shutdown()
    print("\n配置管理器测试完成")