#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流引擎测试
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflow.engine import Workflow, WorkflowEngine, WorkflowStep


class TestWorkflowEngine:
    """工作流引擎测试类"""

    @pytest.fixture
    def engine(self):
        """创建工作流引擎实例"""
        return WorkflowEngine()

    @pytest.fixture
    def sample_workflow(self, tmp_path):
        """创建示例工作流"""
        workflow_data = {
            "name": "test_workflow",
            "version": "1.0",
            "description": "测试工作流",
            "steps": [
                {
                    "id": "step1",
                    "name": "步骤1",
                    "description": "第一步",
                    "skill": "notification",
                    "action": "notify",
                    "params": {"title": "Test", "message": "Step 1"},
                },
                {
                    "id": "step2",
                    "name": "步骤2",
                    "description": "第二步",
                    "skill": "notification",
                    "action": "notify",
                    "params": {"title": "Test", "message": "Step 2"},
                    "depends_on": ["step1"],
                },
            ],
            "config": {"timeout": 300},
        }

        # 保存到临时目录
        workflow_file = tmp_path / "test_workflow.json"
        with open(workflow_file, "w", encoding="utf-8") as f:
            json.dump(workflow_data, f)

        return workflow_file

    def test_engine_initialization(self, engine):
        """测试引擎初始化"""
        assert engine is not None
        assert engine.workflows == {}

    def test_load_workflow_from_file(self, engine, sample_workflow, tmp_path):
        """测试从文件加载工作流"""
        # 临时修改模板目录
        original_dir = engine.templates_dir
        engine.templates_dir = tmp_path

        try:
            workflow = engine.load_workflow("test_workflow")

            assert workflow is not None
            assert workflow.name == "test_workflow"
            assert len(workflow.steps) == 2
        finally:
            engine.templates_dir = original_dir

    def test_load_nonexistent_workflow(self, engine):
        """测试加载不存在的工作流"""
        workflow = engine.load_workflow("nonexistent")
        assert workflow is None

    def test_list_workflows(self, engine, sample_workflow, tmp_path):
        """测试列出工作流"""
        original_dir = engine.templates_dir
        engine.templates_dir = tmp_path

        try:
            workflows = engine.list_workflows()

            assert len(workflows) >= 1
            workflow_names = [w["name"] for w in workflows]
            assert "test_workflow" in workflow_names
        finally:
            engine.templates_dir = original_dir

    def test_workflow_step_dependencies(self, sample_workflow):
        """测试工作流步骤依赖"""
        with open(sample_workflow, "r", encoding="utf-8") as f:
            data = json.load(f)

        step1 = data["steps"][0]
        step2 = data["steps"][1]

        assert "depends_on" not in step1 or step1["depends_on"] == []
        assert step2["depends_on"] == ["step1"]
