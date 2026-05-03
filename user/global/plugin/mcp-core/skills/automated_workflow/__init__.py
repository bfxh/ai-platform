#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化工作流技能初始化文件
"""

from .skill import AutomatedWorkflowSkill

__all__ = ['AutomatedWorkflowSkill']

# 技能入口点
def get_skill():
    return AutomatedWorkflowSkill