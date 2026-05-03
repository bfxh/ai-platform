#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试技能
用于自动运行测试并生成测试报告
"""

import os
import sys
import subprocess
import json
import time
import fnmatch
from datetime import datetime
from skills.base import SkillBase

class AutomatedTestingSkill(SkillBase):
    name = "automated_testing"
    description = "自动化测试 - 自动运行测试并生成测试报告"
    version = "1.0.0"
    author = "MCP Core Team"
    
    def __init__(self, config: dict = None):
        # 先设置默认值，避免父类初始化时调用_load_config出错
        self.test_config = "test_config.json"
        self.test_reports_dir = "test_reports"
        self.default_test_frameworks = ["pytest", "unittest", "nose"]
        self.test_frameworks = []
        self.test_paths = []
        self.test_patterns = ["test_*.py", "*_test.py"]
        
        super().__init__(config)
        # 父类初始化后再从配置中获取
        self.test_config = self.config.get("test_config", "test_config.json")
        self.test_reports_dir = self.config.get("test_reports_dir", "test_reports")
        self.test_frameworks = self.config.get("test_frameworks", self.default_test_frameworks)
        self.test_paths = self.config.get("test_paths", ["tests", "test"])
        self.test_patterns = self.config.get("test_patterns", ["test_*.py", "*_test.py"])
        
        # 确保测试报告目录存在
        os.makedirs(self.test_reports_dir, exist_ok=True)
        # 确保配置文件存在
        self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        config = {
            "test_config": self.test_config,
            "test_reports_dir": self.test_reports_dir,
            "test_frameworks": self.test_frameworks,
            "test_paths": self.test_paths,
            "test_patterns": self.test_patterns
        }
        try:
            with open(self.test_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def find_test_files(self, directory):
        """查找测试文件"""
        test_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                for pattern in self.test_patterns:
                    if fnmatch.fnmatch(file, pattern):
                        test_files.append(os.path.join(root, file))
                        break
        return test_files
    
    def run_pytest(self, test_path, report_file):
        """运行pytest测试"""
        try:
            cmd = [
                sys.executable,
                "-m", "pytest",
                test_path,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={report_file}"
            ]
            self.logger.info(f"Running pytest: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
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
            self.logger.error(f"运行pytest失败: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "returncode": 1
            }
    
    def run_unittest(self, test_path, report_file):
        """运行unittest测试"""
        try:
            # 为unittest生成临时测试脚本
            temp_script = "run_unittest.py"
            with open(temp_script, 'w', encoding='utf-8') as f:
                f.write("""
import unittest
import json
import sys

# 导入测试文件
sys.path.insert(0, '.')

# 发现并运行测试
test_loader = unittest.TestLoader()
test_suite = test_loader.discover('{0}')
test_runner = unittest.TextTestRunner(verbosity=2)
result = test_runner.run(test_suite)

# 生成报告
report = {
    'success': result.wasSuccessful(),
    'tests_run': result.testsRun,
    'failures': len(result.failures),
    'errors': len(result.errors),
    'skipped': len(result.skipped)
}

with open('{1}', 'w') as f:
    json.dump(report, f, indent=2)

# 设置退出码
sys.exit(0 if result.wasSuccessful() else 1)
""".format(os.path.dirname(test_path), report_file))
            
            cmd = [sys.executable, temp_script]
            self.logger.info(f"Running unittest: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # 清理临时脚本
            if os.path.exists(temp_script):
                os.remove(temp_script)
                
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            self.logger.error(f"运行unittest失败: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "returncode": 1
            }
    
    def run_nose(self, test_path, report_file):
        """运行nose测试"""
        try:
            cmd = [
                sys.executable,
                "-m", "nose",
                test_path,
                "-v",
                "--with-json",
                f"--json-file={report_file}"
            ]
            self.logger.info(f"Running nose: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
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
            self.logger.error(f"运行nose失败: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "returncode": 1
            }
    
    def run_tests(self, test_path, framework="pytest"):
        """运行测试"""
        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(
            self.test_reports_dir,
            f"test_report_{timestamp}.json"
        )
        
        # 根据框架运行测试
        if framework == "pytest":
            result = self.run_pytest(test_path, report_file)
        elif framework == "unittest":
            result = self.run_unittest(test_path, report_file)
        elif framework == "nose":
            result = self.run_nose(test_path, report_file)
        else:
            self.logger.error(f"不支持的测试框架: {framework}")
            return {
                "success": False,
                "output": "",
                "error": f"不支持的测试框架: {framework}",
                "returncode": 1
            }
        
        # 读取报告文件
        if os.path.exists(report_file):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                result["report"] = report
            except Exception as e:
                self.logger.error(f"读取报告文件失败: {e}")
        
        return result
    
    def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("开始运行所有测试...")
        results = {}
        
        # 查找测试文件
        test_files = []
        for test_path in self.test_paths:
            if os.path.exists(test_path):
                test_files.extend(self.find_test_files(test_path))
        
        if not test_files:
            self.logger.warning("没有找到测试文件")
            return {"success": False, "error": "没有找到测试文件"}
        
        # 运行测试
        for framework in self.test_frameworks:
            self.logger.info(f"使用 {framework} 运行测试")
            framework_results = {}
            
            for test_file in test_files:
                self.logger.info(f"测试文件: {test_file}")
                result = self.run_tests(test_file, framework)
                framework_results[test_file] = result
            
            results[framework] = framework_results
        
        # 生成汇总报告
        summary = {
            "total_tests": len(test_files),
            "frameworks": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for framework, framework_results in results.items():
            passed = sum(1 for r in framework_results.values() if r.get("success", False))
            failed = len(framework_results) - passed
            summary["frameworks"][framework] = {
                "passed": passed,
                "failed": failed,
                "total": len(framework_results)
            }
        
        # 保存汇总报告
        summary_file = os.path.join(
            self.test_reports_dir,
            f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            self.logger.info(f"汇总报告已保存到: {summary_file}")
        except Exception as e:
            self.logger.error(f"保存汇总报告失败: {e}")
        
        return {
            "success": True,
            "summary": summary,
            "results": results
        }
    
    def generate_test_report(self, report_file):
        """生成测试报告"""
        try:
            if not os.path.exists(report_file):
                return {"success": False, "error": f"报告文件不存在: {report_file}"}
            
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            # 生成HTML报告
            html_report = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .summary {{
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        .success {{
            color: green;
        }}
        .failure {{
            color: red;
        }}
        .test-result {{
            margin-bottom: 10px;
            padding: 10px;
            border-left: 4px solid #ddd;
        }}
        .test-result.success {{
            border-left-color: green;
            background-color: #f0fff0;
        }}
        .test-result.failure {{
            border-left-color: red;
            background-color: #fff0f0;
        }}
        pre {{
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>测试报告</h1>
        <div class="summary">
            <h2>测试摘要</h2>
            <p>测试时间: {timestamp}</p>
            <p>总测试数: {total_tests}</p>
            {summary_html}
        </div>
        {details_html}
    </div>
</body>
</html>
"""
            
            # 生成摘要HTML
            summary_html = ""
            for framework, stats in report.get("frameworks", {}).items():
                summary_html += f"<p>{framework}: 通过 {stats['passed']}, 失败 {stats['failed']}, 总计 {stats['total']}</p>"
            
            # 生成详细HTML
            details_html = ""
            for framework, framework_results in report.get("results", {}).items():
                details_html += f"<h2>{framework} 测试结果</h2>"
                for test_file, result in framework_results.items():
                    status = "success" if result.get("success", False) else "failure"
                    details_html += f"<div class='test-result {status}'>"
                    details_html += f"<h3>{test_file}</h3>"
                    details_html += f"<p>状态: {'通过' if status == 'success' else '失败'}</p>"
                    if result.get("output"):
                        details_html += f"<h4>输出:</h4><pre>{result['output']}</pre>"
                    if result.get("error"):
                        details_html += f"<h4>错误:</h4><pre>{result['error']}</pre>"
                    details_html += "</div>"
            
            # 填充HTML模板
            html_report = html_report.format(
                timestamp=report.get("timestamp", ""),
                total_tests=report.get("total_tests", 0),
                summary_html=summary_html,
                details_html=details_html
            )
            
            # 保存HTML报告
            html_report_file = report_file.replace(".json", ".html")
            with open(html_report_file, 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            self.logger.info(f"HTML报告已生成: {html_report_file}")
            return {
                "success": True,
                "html_report": html_report_file
            }
        except Exception as e:
            self.logger.error(f"生成测试报告失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute(self, command: str, **kwargs):
        """执行技能命令"""
        if command == "run":
            test_path = kwargs.get("test_path", ".")
            framework = kwargs.get("framework", "pytest")
            return self.run_tests(test_path, framework)
        elif command == "run-all":
            return self.run_all_tests()
        elif command == "generate-report":
            report_file = kwargs.get("report_file")
            if not report_file:
                return "错误: 缺少 report_file 参数"
            return self.generate_test_report(report_file)
        elif command == "list-tests":
            test_path = kwargs.get("test_path", ".")
            test_files = self.find_test_files(test_path)
            return "\n".join(test_files)
        else:
            return "无效的命令，请使用以下命令: run, run-all, generate-report, list-tests"
    
    def get_info(self):
        """获取技能信息"""
        return {
            "name": "Automated Testing",
            "description": "自动化运行测试并生成测试报告",
            "version": "1.0.0",
            "author": "MCP Core Team",
            "commands": [
                {
                    "name": "run",
                    "description": "运行指定路径的测试",
                    "parameters": [
                        {
                            "name": "test_path",
                            "type": "string",
                            "required": false,
                            "description": "测试文件或目录路径"
                        },
                        {
                            "name": "framework",
                            "type": "string",
                            "required": false,
                            "description": "测试框架 (pytest, unittest, nose)"
                        }
                    ]
                },
                {
                    "name": "run-all",
                    "description": "运行所有测试"
                },
                {
                    "name": "generate-report",
                    "description": "生成测试报告",
                    "parameters": [
                        {
                            "name": "report_file",
                            "type": "string",
                            "required": true,
                            "description": "测试报告JSON文件路径"
                        }
                    ]
                },
                {
                    "name": "list-tests",
                    "description": "列出测试文件",
                    "parameters": [
                        {
                            "name": "test_path",
                            "type": "string",
                            "required": false,
                            "description": "测试目录路径"
                        }
                    ]
                }
            ]
        }



# 测试代码
if __name__ == "__main__":
    skill = AutomatedTestingSkill()
    print(skill.execute("run-all"))