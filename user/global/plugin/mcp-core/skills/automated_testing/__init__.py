#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试技能初始化文件
"""

from .skill import AutomatedTestingSkill

__all__ = ['AutomatedTestingSkill']

# 技能入口点
def get_skill():
    return AutomatedTestingSkill