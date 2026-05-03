#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台进程管理技能初始化文件
"""

from .skill import BackgroundProcessManagerSkill

__all__ = ['BackgroundProcessManagerSkill']

# 技能入口点
def get_skill():
    return BackgroundProcessManagerSkill