#!/usr/bin/env python
"""TRAE Pipeline v6.0 - 五阶段强制管道

所有项目在开发前必须通过:
  1. Preliminary Analysis  (架构分析)
  2. Security Audit        (安全审计)
  3. Reverse Engineering   (许可证检测)
  4. Deep Analysis         (交叉分析)
  5. Development           (仅当前4阶段通过)

Usage:
  from core.pipeline import Pipeline
  pipeline = Pipeline(project_path='D:/my_project')
  pipeline.run_all()
"""
