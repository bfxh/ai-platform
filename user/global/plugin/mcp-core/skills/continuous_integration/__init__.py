#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持续集成技能初始化文件
"""

from .skill import ContinuousIntegrationSkill

__all__ = ['ContinuousIntegrationSkill']

# 技能入口点
def get_skill():
    return ContinuousIntegrationSkill