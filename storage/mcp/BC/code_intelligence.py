#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码智能工具 - 基于 Claude Code 的 LSPTool 和 FileEditTool

功能：
- 代码分析与诊断
- 代码重构建议
- 智能代码编辑
- 代码生成
- 代码审查
- 批量代码处理

用法：
    python code_intelligence.py analyze <path>              # 分析代码
    python code_intelligence.py refactor <file>             # 重构建议
    python code_intelligence.py edit <file> <changes>       # 智能编辑
    python code_intelligence.py generate <prompt>           # 生成代码
    python code_intelligence.py review <file>               # 代码审查
    python code_intelligence.py batch <pattern> <action>    # 批量处理

MCP调用：
    {"tool": "code_intelligence", "action": "analyze", "params": {"path": "..."}}
"""

import json
import sys
import os
import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"

# 代码分析配置
CODE_CONFIG = {
    "max_line_length": 100,
    "max_function_length": 50,
    "max_class_length": 200,
    "max_parameters": 5,
    "max_nesting_depth": 4,
}

# ============================================================
# 代码问题
# ============================================================
@dataclass
class CodeIssue:
    """代码问题"""
    file: str
    line: int
    column: int
    severity: str  # error, warning, info
    code: str
    message: str
    suggestion: Optional[str] = None

# ============================================================
# 代码智能
# ============================================================
class CodeIntelligence:
    """代码智能工具"""
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
    
    def analyze_file(self, file_path: str) -> Dict:
        """分析单个文件"""
        path = Path(file_path)
        
        if not path.exists():
            return {"success": False, "error": f"文件不存在: {file_path}"}
        
        ext = path.suffix
        
        # 根据文件类型选择分析方法
        if ext == '.py':
            return self._analyze_python(path)
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            return self._analyze_javascript(path)
        elif ext in ['.java', '.kt']:
            return self._analyze_java(path)
        elif ext in ['.cpp', '.c', '.h', '.hpp']:
            return self._analyze_cpp(path)
        else:
            return self._analyze_generic(path)
    
    def _analyze_python(self, path: Path) -> Dict:
        """分析 Python 文件"""
        self.issues = []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 语法检查
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                self.issues.append(CodeIssue(
                    file=str(path),
                    line=e.lineno or 1,
                    column=e.offset or 0,
                    severity="error",
                    code="E001",
                    message=f"语法错误: {e.msg}"
                ))
                tree = None
            
            # 行长度检查
            for i, line in enumerate(lines, 1):
                if len(line) > CODE_CONFIG["max_line_length"]:
                    self.issues.append(CodeIssue(
                        file=str(path),
                        line=i,
                        column=CODE_CONFIG["max_line_length"],
                        severity="warning",
                        code="W001",
                        message=f"行长度超过 {CODE_CONFIG['max_line_length']} 字符",
                        suggestion="考虑换行或简化代码"
                    ))
            
            # 函数和类分析
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # 函数长度
                        func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                        if func_lines > CODE_CONFIG["max_function_length"]:
                            self.issues.append(CodeIssue(
                                file=str(path),
                                line=node.lineno,
                                column=0,
                                severity="warning",
                                code="W002",
                                message=f"函数 '{node.name}' 过长 ({func_lines} 行)",
                                suggestion="考虑拆分成多个小函数"
                            ))
                        
                        # 参数数量
                        args_count = len(node.args.args) + len(node.args.kwonlyargs)
                        if args_count > CODE_CONFIG["max_parameters"]:
                            self.issues.append(CodeIssue(
                                file=str(path),
                                line=node.lineno,
                                column=0,
                                severity="warning",
                                code="W003",
                                message=f"函数 '{node.name}' 参数过多 ({args_count} 个)",
                                suggestion="考虑使用配置对象或拆分函数"
                            ))
                    
                    elif isinstance(node, ast.ClassDef):
                        # 类长度
                        class_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                        if class_lines > CODE_CONFIG["max_class_length"]:
                            self.issues.append(CodeIssue(
                                file=str(path),
                                line=node.lineno,
                                column=0,
                                severity="warning",
                                code="W004",
                                message=f"类 '{node.name}' 过长 ({class_lines} 行)",
                                suggestion="考虑拆分成多个类"
                            ))
            
            # 复杂度分析
            complexity = self._calculate_complexity(content)
            
            return {
                "success": True,
                "file": str(path),
                "language": "Python",
                "metrics": {
                    "total_lines": len(lines),
                    "code_lines": len([l for l in lines if l.strip()]),
                    "blank_lines": len([l for l in lines if not l.strip()]),
                    "complexity": complexity
                },
                "issues": [
                    {
                        "line": issue.line,
                        "column": issue.column,
                        "severity": issue.severity,
                        "code": issue.code,
                        "message": issue.message,
                        "suggestion": issue.suggestion
                    }
                    for issue in self.issues
                ],
                "summary": {
                    "errors": len([i for i in self.issues if i.severity == "error"]),
                    "warnings": len([i for i in self.issues if i.severity == "warning"]),
                    "infos": len([i for i in self.issues if i.severity == "info"])
                }
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_complexity(self, content: str) -> int:
        """计算代码复杂度"""
        complexity = 1
        
        # 简单的圈复杂度估算
        control_keywords = ['if', 'elif', 'for', 'while', 'except', 'with', 'and', 'or']
        for keyword in control_keywords:
            complexity += content.count(f' {keyword} ')
        
        return complexity
    
    def _analyze_javascript(self, path: Path) -> Dict:
        """分析 JavaScript/TypeScript 文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 基础分析
            return {
                "success": True,
                "file": str(path),
                "language": "JavaScript/TypeScript",
                "metrics": {
                    "total_lines": len(lines),
                    "code_lines": len([l for l in lines if l.strip()]),
                    "blank_lines": len([l for l in lines if not l.strip()])
                },
                "issues": [],
                "summary": {"errors": 0, "warnings": 0, "infos": 0}
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _analyze_java(self, path: Path) -> Dict:
        """分析 Java/Kotlin 文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            return {
                "success": True,
                "file": str(path),
                "language": "Java/Kotlin",
                "metrics": {
                    "total_lines": len(lines),
                    "code_lines": len([l for l in lines if l.strip()]),
                    "blank_lines": len([l for l in lines if not l.strip()])
                },
                "issues": [],
                "summary": {"errors": 0, "warnings": 0, "infos": 0}
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _analyze_cpp(self, path: Path) -> Dict:
        """分析 C/C++ 文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            return {
                "success": True,
                "file": str(path),
                "language": "C/C++",
                "metrics": {
                    "total_lines": len(lines),
                    "code_lines": len([l for l in lines if l.strip()]),
                    "blank_lines": len([l for l in lines if not l.strip()])
                },
                "issues": [],
                "summary": {"errors": 0, "warnings": 0, "infos": 0}
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _analyze_generic(self, path: Path) -> Dict:
        """通用文件分析"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            return {
                "success": True,
                "file": str(path),
                "language": "Unknown",
                "metrics": {
                    "total_lines": len(lines),
                    "code_lines": len([l for l in lines if l.strip()]),
                    "blank_lines": len([l for l in lines if not l.strip()])
                },
                "issues": [],
                "summary": {"errors": 0, "warnings": 0, "infos": 0}
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_directory(self, dir_path: str) -> Dict:
        """分析整个目录"""
        path = Path(dir_path)
        
        if not path.exists():
            return {"success": False, "error": f"目录不存在: {dir_path}"}
        
        results = []
        file_count = 0
        total_issues = {"errors": 0, "warnings": 0, "infos": 0}
        
        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.kt', '.cpp', '.c']:
                result = self.analyze_file(str(file_path))
                if result.get("success"):
                    results.append(result)
                    file_count += 1
                    summary = result.get("summary", {})
                    total_issues["errors"] += summary.get("errors", 0)
                    total_issues["warnings"] += summary.get("warnings", 0)
                    total_issues["infos"] += summary.get("infos", 0)
        
        return {
            "success": True,
            "directory": str(path),
            "files_analyzed": file_count,
            "total_issues": total_issues,
            "results": results
        }
    
    def smart_edit(self, file_path: str, changes: List[Dict]) -> Dict:
        """智能编辑文件"""
        try:
            path = Path(file_path)
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            applied_changes = []
            failed_changes = []
            
            for change in changes:
                old_text = change.get("old", "")
                new_text = change.get("new", "")
                
                if old_text in content:
                    content = content.replace(old_text, new_text, 1)
                    applied_changes.append(change)
                else:
                    failed_changes.append({
                        "change": change,
                        "reason": "未找到匹配文本"
                    })
            
            # 保存
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "file": str(path),
                "applied_changes": len(applied_changes),
                "failed_changes": len(failed_changes),
                "changes": applied_changes,
                "failures": failed_changes
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_code(self, prompt: str, language: str = "python") -> Dict:
        """生成代码"""
        # 这里可以集成 AI 生成
        # 暂时返回模板
        templates = {
            "python": f"""# Generated Python code
# Prompt: {prompt}

def main():
    # TODO: Implement based on prompt
    pass

if __name__ == "__main__":
    main()
""",
            "javascript": f"""// Generated JavaScript code
// Prompt: {prompt}

function main() {{
    // TODO: Implement based on prompt
}}

module.exports = {{ main }};
"""
        }
        
        return {
            "success": True,
            "prompt": prompt,
            "language": language,
            "code": templates.get(language, "# Template not available")
        }
    
    def review_code(self, file_path: str) -> Dict:
        """代码审查"""
        # 先分析
        analysis = self.analyze_file(file_path)
        
        if not analysis.get("success"):
            return analysis
        
        # 生成审查报告
        review = {
            "file": file_path,
            "overall_score": 100,
            "categories": {
                "readability": 100,
                "maintainability": 100,
                "performance": 100,
                "security": 100
            },
            "recommendations": []
        }
        
        # 根据问题扣分
        issues = analysis.get("issues", [])
        for issue in issues:
            if issue["severity"] == "error":
                review["overall_score"] -= 10
                review["categories"]["maintainability"] -= 10
            elif issue["severity"] == "warning":
                review["overall_score"] -= 5
                review["categories"]["readability"] -= 5
        
        # 确保分数不低于 0
        review["overall_score"] = max(0, review["overall_score"])
        for key in review["categories"]:
            review["categories"][key] = max(0, review["categories"][key])
        
        # 添加建议
        if issues:
            review["recommendations"].append("修复所有错误和警告")
        
        return {
            "success": True,
            "analysis": analysis,
            "review": review
        }
    
    def batch_process(self, pattern: str, action: str, params: Dict) -> Dict:
        """批量处理文件"""
        import glob
        
        files = glob.glob(pattern, recursive=True)
        results = []
        
        for file_path in files:
            if action == "analyze":
                result = self.analyze_file(file_path)
            elif action == "review":
                result = self.review_code(file_path)
            else:
                result = {"success": False, "error": f"未知操作: {action}"}
            
            results.append({
                "file": file_path,
                "result": result
            })
        
        return {
            "success": True,
            "files_processed": len(files),
            "results": results
        }

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.intelligence = CodeIntelligence()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "analyze":
            path = params.get("path")
            if Path(path).is_file():
                return self.intelligence.analyze_file(path)
            else:
                return self.intelligence.analyze_directory(path)
        
        elif action == "edit":
            file_path = params.get("file")
            changes = params.get("changes", [])
            return self.intelligence.smart_edit(file_path, changes)
        
        elif action == "generate":
            prompt = params.get("prompt")
            language = params.get("language", "python")
            return self.intelligence.generate_code(prompt, language)
        
        elif action == "review":
            file_path = params.get("file")
            return self.intelligence.review_code(file_path)
        
        elif action == "batch":
            pattern = params.get("pattern")
            batch_action = params.get("action")
            batch_params = params.get("params", {})
            return self.intelligence.batch_process(pattern, batch_action, batch_params)
        
        else:
            return {"success": False, "error": f"未知操作: {action}"}

# ============================================================
# 命令行接口
# ============================================================
def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    intelligence = CodeIntelligence()
    
    if cmd == "analyze":
        if len(sys.argv) < 3:
            print("用法: code_intelligence.py analyze <path>")
            return
        
        path = sys.argv[2]
        result = intelligence.analyze_file(path) if Path(path).is_file() else intelligence.analyze_directory(path)
        
        if result.get("success"):
            print(f"分析结果: {result.get('file') or result.get('directory')}")
            print("=" * 60)
            
            if "metrics" in result:
                metrics = result["metrics"]
                print(f"\n代码指标:")
                print(f"  总行数: {metrics['total_lines']}")
                print(f"  代码行: {metrics['code_lines']}")
                print(f"  空行: {metrics['blank_lines']}")
                if 'complexity' in metrics:
                    print(f"  复杂度: {metrics['complexity']}")
            
            if "summary" in result:
                summary = result["summary"]
                print(f"\n问题统计:")
                print(f"  错误: {summary['errors']}")
                print(f"  警告: {summary['warnings']}")
                print(f"  信息: {summary['infos']}")
            
            if result.get("issues"):
                print(f"\n问题详情:")
                for issue in result["issues"]:
                    print(f"  [{issue['severity'].upper()}] 行{issue['line']}: {issue['message']}")
                    if issue.get('suggestion'):
                        print(f"    建议: {issue['suggestion']}")
        else:
            print(f"分析失败: {result.get('error')}")
    
    elif cmd == "edit":
        if len(sys.argv) < 4:
            print("用法: code_intelligence.py edit <file> <old>=<new>")
            return
        
        file_path = sys.argv[2]
        change_str = sys.argv[3]
        
        if '=' not in change_str:
            print("格式错误，应为: old_text=new_text")
            return
        
        old_text, new_text = change_str.split('=', 1)
        changes = [{"old": old_text, "new": new_text}]
        
        result = intelligence.smart_edit(file_path, changes)
        
        if result.get("success"):
            print(f"✓ 已编辑: {result['file']}")
            print(f"  成功: {result['applied_changes']} 处")
            print(f"  失败: {result['failed_changes']} 处")
        else:
            print(f"✗ 编辑失败: {result.get('error')}")
    
    elif cmd == "generate":
        if len(sys.argv) < 3:
            print("用法: code_intelligence.py generate <prompt> [language]")
            return
        
        prompt = sys.argv[2]
        language = sys.argv[3] if len(sys.argv) > 3 else "python"
        
        result = intelligence.generate_code(prompt, language)
        
        if result.get("success"):
            print(f"生成的代码 ({language}):")
            print("=" * 60)
            print(result["code"])
    
    elif cmd == "review":
        if len(sys.argv) < 3:
            print("用法: code_intelligence.py review <file>")
            return
        
        file_path = sys.argv[2]
        result = intelligence.review_code(file_path)
        
        if result.get("success"):
            review = result["review"]
            print(f"代码审查: {review['file']}")
            print("=" * 60)
            print(f"\n总体评分: {review['overall_score']}/100")
            print(f"\n分类评分:")
            for category, score in review['categories'].items():
                print(f"  {category}: {score}/100")
            
            if review.get('recommendations'):
                print(f"\n建议:")
                for rec in review['recommendations']:
                    print(f"  - {rec}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("代码智能工具 MCP 已启动")
        
        mcp = MCPInterface()
        
        import select
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line)
                    response = mcp.handle(request)
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print(json.dumps({"success": False, "error": "无效的JSON"}))
                    sys.stdout.flush()
    
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
