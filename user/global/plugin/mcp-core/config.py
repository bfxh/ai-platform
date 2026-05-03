#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 统一配置中心

功能:
- 统一配置管理
- 环境变量支持
- 配置热加载
- 配置验证

用法:
    from config import Config
    config = Config()
    value = config.get('skills.network_transfer.port')
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# 尝试导入yaml，如果没有则使用json
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class Config:
    """配置管理中心"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        'version': '2.0.0',
        'name': 'MCP Core System',
        
        'server': {
            'host': 'localhost',
            'port': 8766,
            'protocol': 'websocket',
            'max_connections': 100
        },
        
        'skills': {
            # file_backup 技能配置
        'file_backup': {
            'enabled': True
        },

            'network_transfer': {
                'enabled': True,
                'transfer_port': 50000,
                'buffer_size': 65536,
                'chunk_size': 1048576,  # 1MB
                'max_retries': 3,
                'timeout': 300
            },
            'exo_cluster': {
                'enabled': True,
                'exo_port': 50051,
                'api_port': 52415,
                'auto_discover': True,
                'node_timeout': 30
            },
            'notification': {
                'enabled': True,
                'notification_port': 50001,
                'toast_enabled': True,
                'sound_enabled': True
            },
            'system_config': {
                'enabled': True,
                'firewall_auto': True,
                'backup_before_change': True
            }
        },
        
        'workflow': {
            'templates_dir': '/python/MCP_Core/workflow/templates',
            'state_dir': '/python/MCP_Core/.workflow_state',
            'auto_backup': True,
            'max_parallel_steps': 5,
            'default_timeout': 600
        },
        
        'event_bus': {
            'async_mode': True,
            'max_queue_size': 1000,
            'workers': 4
        },
        
        'retry': {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 60.0,
            'exponential_base': 2.0
        },
        
        'monitoring': {
            'enabled': True,
            'metrics_interval': 60,
            'log_level': 'INFO',
            'log_file': '/python/Logs/mcp.log'
        },
        
        'paths': {
            'ai_path': '/python',
            'mcp_core': '/python/MCP_Core',
            'skills': '/python/user/skills',
            'workflows': '/python/storage/mcp',
            'logs': '/python/storage/logs',
            'temp': '/python/storage/temp',
            'memory': '/python/storage/Brain',
            'config': '/python/user/config',
            'mcp': '/python/storage/mcp',
            'plugins': '/python/user/plugins'
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path('/python/MCP_Core/config.json')
        self._config = {}
        self._last_load_time = None
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        # 从默认配置开始
        self._config = self._deep_copy(self.DEFAULT_CONFIG)
        
        # 从文件加载（如果存在）
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if YAML_AVAILABLE:
                        file_config = yaml.safe_load(f)
                    else:
                        # 尝试JSON
                        try:
                            file_config = json.load(f)
                        except:
                            file_config = None
                    if file_config:
                        self._merge_config(self._config, file_config)
                self._last_load_time = datetime.now()
            except Exception as e:
                print(f"[Config] 警告: 无法加载配置文件: {e}")
        
        # 从环境变量加载
        self._load_from_env()
    
    def _deep_copy(self, obj):
        """深拷贝"""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        return obj
    
    def _merge_config(self, base: dict, override: dict):
        """合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mappings = {
            'MCP_SERVER_HOST': 'server.host',
            'MCP_SERVER_PORT': 'server.port',
            'MCP_LOG_LEVEL': 'monitoring.log_level',
            'MCP_AI_PATH': 'paths.ai_path'
        }
        
        for env_key, config_path in env_mappings.items():
            value = os.getenv(env_key)
            if value:
                self._set_by_path(self._config, config_path, value)
    
    def _set_by_path(self, config: dict, path: str, value: Any):
        """通过路径设置配置值"""
        keys = path.split('.')
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def get(self, path: str, default: Any = None) -> Any:
        """通过路径获取配置值"""
        keys = path.split('.')
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def set(self, path: str, value: Any):
        """设置配置值"""
        self._set_by_path(self._config, path, value)
    
    def save(self):
        """保存配置到文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if YAML_AVAILABLE:
                    yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
                else:
                    json.dump(self._config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[Config] 错误: 无法保存配置: {e}")
            return False
    
    def reload(self):
        """重新加载配置"""
        self._load_config()
    
    def to_dict(self) -> Dict:
        """导出为字典"""
        return self._deep_copy(self._config)
    
    def get_skill_config(self, skill_name: str) -> Dict:
        """获取技能配置"""
        return self.get(f'skills.{skill_name}', {})
    
    def is_skill_enabled(self, skill_name: str) -> bool:
        """检查技能是否启用"""
        return self.get(f'skills.{skill_name}.enabled', False)


# 全局配置实例
_config_instance = None

def get_config() -> Config:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


if __name__ == '__main__':
    # 测试配置中心
    config = Config()
    print("MCP Core 配置测试")
    print(f"版本: {config.get('version')}")
    print(f"服务器端口: {config.get('server.port')}")
    print(f"传输端口: {config.get('skills.network_transfer.transfer_port')}")
    print(f"网络传输技能启用: {config.is_skill_enabled('network_transfer')}")
    
    # 保存默认配置
    config.save()
    print(f"\n配置已保存到: {config.config_path}")
