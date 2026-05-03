#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub项目搜索技能初始化文件
"""

from .skill import GitHubProjectSearchSkill

__all__ = ['GitHubProjectSearchSkill']

# 技能入口点
def get_skill():
    return GitHubProjectSearchSkill