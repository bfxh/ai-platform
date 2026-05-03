#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件元数据和配置类
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    entry_point: str = "__init__.py"  # 插件入口点
    homepage: Optional[str] = None
    license: Optional[str] = None


@dataclass
class PluginConfig:
    """插件配置"""

    enabled: bool = True
    settings: Dict = field(default_factory=dict)
    ai_provider: Optional[str] = None  # 用于AI增强的提供商
    ai_model: Optional[str] = None
    priority: int = 0  # 优先级，数值越大优先级越高
