#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 配置验证器

功能:
- 配置结构验证
- 类型检查
- 必需字段检查
- 默认值填充

用法:
    from config_validator import ConfigValidator
    
    validator = ConfigValidator()
    is_valid, errors = validator.validate(config_dict)
    
    # 或使用装饰器
    @validate_config
    def process_config(config):
        pass
"""

import re
from typing import Any, Dict, List, Tuple, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import json


class ValidationError(Exception):
    """验证错误"""
    pass


class ConfigType(Enum):
    """配置类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    PATH = "path"
    PORT = "port"
    IP = "ip"
    ENUM = "enum"


@dataclass
class FieldSchema:
    """字段模式"""
    name: str
    type: ConfigType
    required: bool = True
    default: Any = None
    description: str = ""
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None  # 正则表达式
    enum_values: Optional[List[str]] = None
    nested_schema: Optional[Dict[str, 'FieldSchema']] = None


class ConfigValidator:
    """配置验证器"""
    
    # MCP Core 配置模式
    CONFIG_SCHEMA = {
        'version': FieldSchema(
            name='version',
            type=ConfigType.STRING,
            required=True,
            description='系统版本'
        ),
        'name': FieldSchema(
            name='name',
            type=ConfigType.STRING,
            required=False,
            default='MCP Core System',
            description='系统名称'
        ),
        'server': FieldSchema(
            name='server',
            type=ConfigType.DICT,
            required=True,
            description='服务器配置',
            nested_schema={
                'host': FieldSchema(
                    name='host',
                    type=ConfigType.IP,
                    required=True,
                    default='localhost',
                    description='服务器地址'
                ),
                'port': FieldSchema(
                    name='port',
                    type=ConfigType.PORT,
                    required=True,
                    default=8766,
                    description='服务器端口'
                ),
                'protocol': FieldSchema(
                    name='protocol',
                    type=ConfigType.ENUM,
                    required=True,
                    default='websocket',
                    enum_values=['websocket', 'http', 'tcp'],
                    description='通信协议'
                ),
                'max_connections': FieldSchema(
                    name='max_connections',
                    type=ConfigType.INTEGER,
                    required=False,
                    default=100,
                    min_value=1,
                    max_value=10000,
                    description='最大连接数'
                )
            }
        ),
        'skills': FieldSchema(
            name='skills',
            type=ConfigType.DICT,
            required=True,
            description='技能配置'
        ),
        'workflow': FieldSchema(
            name='workflow',
            type=ConfigType.DICT,
            required=False,
            description='工作流配置',
            nested_schema={
                'templates_dir': FieldSchema(
                    name='templates_dir',
                    type=ConfigType.PATH,
                    required=True,
                    description='模板目录'
                ),
                'state_dir': FieldSchema(
                    name='state_dir',
                    type=ConfigType.PATH,
                    required=True,
                    description='状态目录'
                ),
                'auto_backup': FieldSchema(
                    name='auto_backup',
                    type=ConfigType.BOOLEAN,
                    required=False,
                    default=True,
                    description='自动备份'
                ),
                'max_parallel_steps': FieldSchema(
                    name='max_parallel_steps',
                    type=ConfigType.INTEGER,
                    required=False,
                    default=5,
                    min_value=1,
                    max_value=100,
                    description='最大并行步骤'
                ),
                'default_timeout': FieldSchema(
                    name='default_timeout',
                    type=ConfigType.INTEGER,
                    required=False,
                    default=600,
                    min_value=1,
                    description='默认超时'
                )
            }
        ),
        'event_bus': FieldSchema(
            name='event_bus',
            type=ConfigType.DICT,
            required=False,
            description='事件总线配置',
            nested_schema={
                'async_mode': FieldSchema(
                    name='async_mode',
                    type=ConfigType.BOOLEAN,
                    required=False,
                    default=True,
                    description='异步模式'
                ),
                'max_queue_size': FieldSchema(
                    name='max_queue_size',
                    type=ConfigType.INTEGER,
                    required=False,
                    default=1000,
                    min_value=100,
                    description='最大队列大小'
                ),
                'workers': FieldSchema(
                    name='workers',
                    type=ConfigType.INTEGER,
                    required=False,
                    default=4,
                    min_value=1,
                    max_value=100,
                    description='工作线程数'
                )
            }
        ),
        'retry': FieldSchema(
            name='retry',
            type=ConfigType.DICT,
            required=False,
            description='重试配置',
            nested_schema={
                'max_retries': FieldSchema(
                    name='max_retries',
                    type=ConfigType.INTEGER,
                    required=False,
                    default=3,
                    min_value=0,
                    max_value=10,
                    description='最大重试次数'
                ),
                'base_delay': FieldSchema(
                    name='base_delay',
                    type=ConfigType.FLOAT,
                    required=False,
                    default=1.0,
                    min_value=0.1,
                    description='基础延迟'
                ),
                'max_delay': FieldSchema(
                    name='max_delay',
                    type=ConfigType.FLOAT,
                    required=False,
                    default=60.0,
                    min_value=1.0,
                    description='最大延迟'
                )
            }
        ),
        'monitoring': FieldSchema(
            name='monitoring',
            type=ConfigType.DICT,
            required=False,
            description='监控配置',
            nested_schema={
                'enabled': FieldSchema(
                    name='enabled',
                    type=ConfigType.BOOLEAN,
                    required=False,
                    default=True,
                    description='是否启用'
                ),
                'metrics_interval': FieldSchema(
                    name='metrics_interval',
                    type=ConfigType.INTEGER,
                    required=False,
                    default=60,
                    min_value=10,
                    description='指标收集间隔'
                ),
                'log_level': FieldSchema(
                    name='log_level',
                    type=ConfigType.ENUM,
                    required=False,
                    default='INFO',
                    enum_values=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    description='日志级别'
                ),
                'log_file': FieldSchema(
                    name='log_file',
                    type=ConfigType.PATH,
                    required=False,
                    description='日志文件路径'
                )
            }
        ),
        'paths': FieldSchema(
            name='paths',
            type=ConfigType.DICT,
            required=False,
            description='路径配置'
        )
    }
    
    def __init__(self):
        self.errors: List[str] = []
    
    def validate(
        self,
        config: Dict[str, Any],
        schema: Optional[Dict[str, FieldSchema]] = None
    ) -> Tuple[bool, List[str]]:
        """验证配置"""
        self.errors = []
        schema = schema or self.CONFIG_SCHEMA
        
        self._validate_dict(config, schema, "")
        
        return len(self.errors) == 0, self.errors
    
    def _validate_dict(
        self,
        data: Dict[str, Any],
        schema: Dict[str, FieldSchema],
        path: str
    ):
        """验证字典"""
        # 检查必需字段
        for field_name, field_schema in schema.items():
            full_path = f"{path}.{field_name}" if path else field_name
            
            if field_name not in data:
                if field_schema.required:
                    self.errors.append(f"缺少必需字段: {full_path}")
                continue
            
            value = data[field_name]
            self._validate_value(value, field_schema, full_path)
        
        # 检查未知字段
        for key in data:
            if key not in schema:
                full_path = f"{path}.{key}" if path else key
                # 可选：警告未知字段
                # self.errors.append(f"未知字段: {full_path}")
    
    def _validate_value(
        self,
        value: Any,
        schema: FieldSchema,
        path: str
    ):
        """验证单个值"""
        # 类型验证
        if schema.type == ConfigType.STRING:
            if not isinstance(value, str):
                self.errors.append(f"{path} 必须是字符串")
                return
        
        elif schema.type == ConfigType.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool):
                self.errors.append(f"{path} 必须是整数")
                return
            # 范围验证
            if schema.min_value is not None and value < schema.min_value:
                self.errors.append(f"{path} 最小值为 {schema.min_value}")
            if schema.max_value is not None and value > schema.max_value:
                self.errors.append(f"{path} 最大值为 {schema.max_value}")
        
        elif schema.type == ConfigType.FLOAT:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                self.errors.append(f"{path} 必须是数字")
                return
            # 范围验证
            if schema.min_value is not None and value < schema.min_value:
                self.errors.append(f"{path} 最小值为 {schema.min_value}")
            if schema.max_value is not None and value > schema.max_value:
                self.errors.append(f"{path} 最大值为 {schema.max_value}")
        
        elif schema.type == ConfigType.BOOLEAN:
            if not isinstance(value, bool):
                self.errors.append(f"{path} 必须是布尔值")
                return
        
        elif schema.type == ConfigType.LIST:
            if not isinstance(value, list):
                self.errors.append(f"{path} 必须是列表")
                return
        
        elif schema.type == ConfigType.DICT:
            if not isinstance(value, dict):
                self.errors.append(f"{path} 必须是字典")
                return
            # 递归验证嵌套结构
            if schema.nested_schema:
                self._validate_dict(value, schema.nested_schema, path)
        
        elif schema.type == ConfigType.PATH:
            if not isinstance(value, str):
                self.errors.append(f"{path} 必须是路径字符串")
                return
        
        elif schema.type == ConfigType.PORT:
            if not isinstance(value, int) or isinstance(value, bool):
                self.errors.append(f"{path} 必须是整数")
                return
            if not (1 <= value <= 65535):
                self.errors.append(f"{path} 必须是有效的端口号 (1-65535)")
        
        elif schema.type == ConfigType.IP:
            if not isinstance(value, str):
                self.errors.append(f"{path} 必须是字符串")
                return
            if not self._is_valid_ip(value):
                self.errors.append(f"{path} 必须是有效的IP地址")
        
        elif schema.type == ConfigType.ENUM:
            if schema.enum_values and value not in schema.enum_values:
                self.errors.append(
                    f"{path} 必须是以下值之一: {', '.join(schema.enum_values)}"
                )
        
        # 正则验证
        if schema.pattern and isinstance(value, str):
            if not re.match(schema.pattern, value):
                self.errors.append(f"{path} 格式不正确")
    
    def _is_valid_ip(self, ip: str) -> bool:
        """验证IP地址"""
        if ip in ['localhost', '0.0.0.0', '127.0.0.1']:
            return True
        
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    def fill_defaults(
        self,
        config: Dict[str, Any],
        schema: Optional[Dict[str, FieldSchema]] = None
    ) -> Dict[str, Any]:
        """填充默认值"""
        schema = schema or self.CONFIG_SCHEMA
        result = {}
        
        for field_name, field_schema in schema.items():
            if field_name in config:
                value = config[field_name]
                # 递归填充嵌套结构
                if (field_schema.type == ConfigType.DICT and 
                    field_schema.nested_schema and 
                    isinstance(value, dict)):
                    value = self.fill_defaults(value, field_schema.nested_schema)
                result[field_name] = value
            elif field_schema.default is not None:
                result[field_name] = field_schema.default
        
        # 保留未在schema中定义的其他字段
        for key in config:
            if key not in schema:
                result[key] = config[key]
        
        return result


def validate_config(func: Callable) -> Callable:
    """配置验证装饰器"""
    def wrapper(config: Dict[str, Any], *args, **kwargs):
        validator = ConfigValidator()
        is_valid, errors = validator.validate(config)
        
        if not is_valid:
            raise ValidationError(f"配置验证失败: {'; '.join(errors)}")
        
        # 填充默认值
        config = validator.fill_defaults(config)
        
        return func(config, *args, **kwargs)
    
    return wrapper


if __name__ == '__main__':
    # 测试配置验证器
    print("测试 MCP 配置验证器")
    print("=" * 50)
    
    validator = ConfigValidator()
    
    # 测试1: 有效配置
    print("\n1. 测试有效配置:")
    valid_config = {
        'version': '2.0.0',
        'server': {
            'host': 'localhost',
            'port': 8766,
            'protocol': 'websocket'
        },
        'skills': {}
    }
    
    is_valid, errors = validator.validate(valid_config)
    print(f"  验证结果: {'通过' if is_valid else '失败'}")
    if errors:
        for error in errors:
            print(f"  错误: {error}")
    
    # 测试2: 无效配置
    print("\n2. 测试无效配置:")
    invalid_config = {
        'version': '2.0.0',
        'server': {
            'host': 'invalid_ip',
            'port': 99999,
            'protocol': 'invalid'
        }
    }
    
    is_valid, errors = validator.validate(invalid_config)
    print(f"  验证结果: {'通过' if is_valid else '失败'}")
    print(f"  发现 {len(errors)} 个错误:")
    for error in errors:
        print(f"    - {error}")
    
    # 测试3: 填充默认值
    print("\n3. 测试填充默认值:")
    minimal_config = {
        'version': '2.0.0',
        'server': {
            'host': '0.0.0.0',
            'port': 9000
        },
        'skills': {}
    }
    
    filled_config = validator.fill_defaults(minimal_config)
    print(f"  填充后的配置:")
    print(json.dumps(filled_config, indent=2, ensure_ascii=False))
    
    print("\n配置验证器测试完成!")
