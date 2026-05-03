#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 技能包初始化文件
"""

from .base import Skill, SkillInfo, SkillRegistry, get_registry
import os
from pathlib import Path

__all__ = ["Skill", "SkillInfo", "SkillRegistry", "get_registry"]

# 自动加载技能
def _load_skills():
    """自动加载所有技能"""
    registry = get_registry()
    skills_dir = Path(__file__).parent
    registry.load_skills_from_directory(str(skills_dir))

# 初始化时加载技能
_load_skills()
