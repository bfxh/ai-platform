#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持续集成技能
用于自动化构建、测试和部署流程
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from skills.base import Skill as SkillBase

class ContinuousIntegrationSkill(SkillBase):
    name = "continuous_integration"
    description = "持续集成 - 自动化构建、测试和部署流程"
    version = "1.0.0"
    author = "MCP Core Team"
    
    def __init__(self, config: dict = None):
        # 先设置默认值，避免父类初始化时调用_load_config出错
        self.ci_config = "ci_config.json"
        self.build_dir = "build"
        self.artifacts_dir = "artifacts"
        self.steps = [
            "install",
            "build",
            "test",
            "deploy"
        ]
        self.commands = {
            "install": ["pip", "install", "-r", "requirements.txt"],
            "build": ["python", "-m", "build"],
            "test": ["python", "-m", "pytest"],
            "deploy": ["twine", "upload", "dist/*"]
        }
        self.environments = {
            "default": {
                "python_version": "3.10",
                "requirements": "requirements.txt"
            }
        }
        
        super().__init__(config)
        # 父类初始化后再从配置中获取
        self.ci_config = self.config.get("ci_config", "ci_config.json")
        self.build_dir = self.config.get("build_dir", "build")
        self.artifacts_dir = self.config.get("artifacts_dir", "artifacts")
        self.steps = self.config.get("steps", self.steps)
        self.commands = self.config.get("commands", self.commands)
        self.environments = self.config.get("environments", self.environments)
        
        # 确保目录存在
        os.makedirs(self.build_dir, exist_ok=True)
        os.makedirs(self.artifacts_dir, exist_ok=True)
        # 确保配置文件存在
        self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        config = {
            "ci_config": self.ci_config,
            "build_dir": self.build_dir,
            "artifacts_dir": self.artifacts_dir,
            "steps": self.steps,
            "commands": self.commands,
            "environments": self.environments
        }
        try:
            with open(self.ci_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def run_command(self, cmd, cwd=None):
        """运行命令"""
        self.logger.info(f"运行命令: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            self.logger.error(f"运行命令失败: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "returncode": 1
            }
    
    def run_step(self, step, environment="default", cwd=None):
        """运行单个步骤"""
        if step not in self.steps:
            self.logger.error(f"未知的步骤: {step}")
            return {
                "success": False,
                "error": f"未知的步骤: {step}"
            }
        
        if step not in self.commands:
            self.logger.error(f"步骤 {step} 没有配置命令")
            return {
                "success": False,
                "error": f"步骤 {step} 没有配置命令"
            }
        
        cmd = self.commands[step]
        result = self.run_command(cmd, cwd)
        return result
    
    def run_pipeline(self, environment="default", cwd=None, steps=None):
        """运行完整的CI流程"""
        self.logger.info("开始CI流程...")
        results = {}
        success = True
        
        # 使用指定的步骤或默认步骤
        pipeline_steps = steps or self.steps
        
        for step in pipeline_steps:
            self.logger.info(f"运行步骤: {step}")
            result = self.run_step(step, environment, cwd)
            results[step] = result
            
            if not result.get("success", False):
                self.logger.error(f"步骤 {step} 失败")
                success = False
                break
        
        # 生成CI报告
        report = {
            "success": success,
            "steps": results,
            "environment": environment,
            "timestamp": datetime.now().isoformat(),
            "duration": time.time() - self.start_time if hasattr(self, 'start_time') else 0
        }
        
        # 保存报告
        report_file = os.path.join(
            self.artifacts_dir,
            f"ci_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.logger.info(f"CI报告已保存到: {report_file}")
        except Exception as e:
            self.logger.error(f"保存CI报告失败: {e}")
        
        return report
    
    def build_project(self, cwd=None):
        """构建项目"""
        self.logger.info("构建项目...")
        return self.run_step("build", cwd=cwd)
    
    def test_project(self, cwd=None):
        """测试项目"""
        self.logger.info("测试项目...")
        return self.run_step("test", cwd=cwd)
    
    def deploy_project(self, cwd=None):
        """部署项目"""
        self.logger.info("部署项目...")
        return self.run_step("deploy", cwd=cwd)
    
    def generate_ci_config(self, template="github-actions"):
        """生成CI配置文件"""
        self.logger.info(f"生成CI配置文件，模板: {template}")
        
        if template == "github-actions":
            config_content = f"""
name: CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    - name: Build project
      run: |
        python -m build
    - name: Test project
      run: |
        python -m pytest
    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      with:
        name: dist
        path: dist/
"""
        
        config_file = ".github/workflows/ci.yml"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            self.logger.info(f"GitHub Actions 配置文件已生成: {config_file}")
            return {
                "success": True,
                "config_file": config_file
            }
        except Exception as e:
            self.logger.error(f"生成CI配置文件失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        
    def execute(self, command: str, **kwargs):
        """执行技能命令"""
        if command == "run":
            environment = kwargs.get("environment", "default")
            cwd = kwargs.get("cwd", None)
            steps = kwargs.get("steps", None)
            self.start_time = time.time()
            return self.run_pipeline(environment, cwd, steps)
        elif command == "build":
            cwd = kwargs.get("cwd", None)
            return self.build_project(cwd)
        elif command == "test":
            cwd = kwargs.get("cwd", None)
            return self.test_project(cwd)
        elif command == "deploy":
            cwd = kwargs.get("cwd", None)
            return self.deploy_project(cwd)
        elif command == "generate-config":
            template = kwargs.get("template", "github-actions")
            return self.generate_ci_config(template)
        else:
            return "无效的命令，请使用以下命令: run, build, test, deploy, generate-config"
    
    def get_info(self):
        """获取技能信息"""
        return {
            "name": "Continuous Integration",
            "description": "自动化构建、测试和部署流程",
            "version": "1.0.0",
            "author": "MCP Core Team",
            "commands": [
                {
                    "name": "run",
                    "description": "运行完整的CI流程",
                    "parameters": [
                        {
                            "name": "environment",
                            "type": "string",
                            "required": false,
                            "description": "环境名称"
                        },
                        {
                            "name": "cwd",
                            "type": "string",
                            "required": false,
                            "description": "工作目录"
                        },
                        {
                            "name": "steps",
                            "type": "array",
                            "required": false,
                            "description": "执行步骤列表"
                        }
                    ]
                },
                {
                    "name": "build",
                    "description": "构建项目",
                    "parameters": [
                        {
                            "name": "cwd",
                            "type": "string",
                            "required": false,
                            "description": "工作目录"
                        }
                    ]
                },
                {
                    "name": "test",
                    "description": "测试项目",
                    "parameters": [
                        {
                            "name": "cwd",
                            "type": "string",
                            "required": false,
                            "description": "工作目录"
                        }
                    ]
                },
                {
                    "name": "deploy",
                    "description": "部署项目",
                    "parameters": [
                        {
                            "name": "cwd",
                            "type": "string",
                            "required": false,
                            "description": "工作目录"
                        }
                    ]
                },
                {
                    "name": "generate-config",
                    "description": "生成CI配置文件",
                    "parameters": [
                        {
                            "name": "template",
                            "type": "string",
                            "required": false,
                            "description": "配置模板 (github-actions)"
                        }
                    ]
                }
            ]
        }

# 测试代码
if __name__ == "__main__":
    skill = ContinuousIntegrationSkill()
    print(skill.execute("run"))