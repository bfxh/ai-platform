#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Narsil MCP 客户端

功能:
- 提供代码结构分析接口
- 支持符号查找、依赖分析
- 与 GSTACK lint 集成

用法:
    python narsil-client.py analyze <file_path>
    python narsil-client.py symbols <file_path>
"""

import json
import sys
import argparse
import ast
import re
from pathlib import Path

try:
    import requests
except ImportError:
    print("请安装 requests: pip install requests")
    sys.exit(1)


class PythonCodeAnalyzer:
    """Python 代码分析器"""

    def __init__(self):
        pass

    def analyze_file(self, file_path: str) -> dict:
        """分析文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)
            analysis = {
                "symbols": self._extract_symbols(tree),
                "imports": self._extract_imports(tree),
                "complexity": self._calculate_complexity(tree),
                "issues": self._detect_issues(content, file_path)
            }

            return {"success": True, "data": analysis, "error": None}

        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _extract_symbols(self, tree) -> dict:
        """提取符号（函数、类等）"""
        symbols = {
            "functions": [],
            "classes": [],
            "variables": []
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols["functions"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "complexity": self._calculate_function_complexity(node)
                })
            elif isinstance(node, ast.ClassDef):
                symbols["classes"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [base.id for base in node.bases if isinstance(base, ast.Name)]
                })
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        symbols["variables"].append({
                            "name": target.id,
                            "line": node.lineno
                        })

        return symbols

    def _extract_imports(self, tree) -> list:
        """提取导入"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "module": alias.name,
                        "asname": alias.asname,
                        "type": "import"
                    })
            elif isinstance(node, ast.ImportFrom):
                imports.append({
                    "module": node.module,
                    "names": [alias.name for alias in node.names],
                    "type": "from_import"
                })
        return imports

    def _calculate_complexity(self, tree) -> dict:
        """计算代码复杂度"""
        complexity = {
            "cyclomatic": 0,
            "functions": []
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_complexity = self._calculate_function_complexity(node)
                complexity["cyclomatic"] += func_complexity
                complexity["functions"].append({
                    "name": node.name,
                    "complexity": func_complexity
                })

        return complexity

    def _calculate_function_complexity(self, node) -> int:
        """计算函数复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try, ast.ExceptHandler, ast.Break, ast.Continue, ast.Raise, ast.Assert)):
                complexity += 1
        return complexity

    def _detect_issues(self, content: str, file_path: str) -> list:
        """检测代码问题"""
        issues = []

        # 检测硬编码的绝对路径
        absolute_path_pattern = r'[A-Z]:\\[\\\w\s.-]+'
        paths = re.findall(absolute_path_pattern, content)
        for path in paths:
            issues.append({
                "type": "hardcoded_path",
                "message": f"硬编码绝对路径: {path}",
                "severity": "medium"
            })

        # 检测未使用的导入
        tree = ast.parse(content, filename=file_path)
        used_names = self._find_used_names(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name not in used_names:
                        issues.append({
                            "type": "unused_import",
                            "message": f"未使用的导入: {alias.name}",
                            "severity": "low"
                        })

        # 检测异常处理问题
        if "except:" in content and "pass" in content:
            issues.append({
                "type": "empty_exception_handler",
                "message": "空的异常处理块",
                "severity": "high"
            })

        return issues

    def _find_used_names(self, tree) -> set:
        """查找使用的名称"""
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)
        return used


class NarsilClient:
    """Narsil MCP 客户端"""

    def __init__(self, host="localhost", port=8401):
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.analyzer = PythonCodeAnalyzer()

    def is_server_running(self) -> bool:
        """检查服务器是否在线"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=1)
            return response.status_code == 200
        except:
            return False

    def analyze_file(self, file_path: str) -> dict:
        """分析文件"""
        # 优先使用本地分析器
        result = self.analyzer.analyze_file(file_path)
        if result["success"]:
            return result

        # 回退到远程服务器
        try:
            response = self.session.post(
                f"{self.base_url}/analyze",
                json={"path": file_path},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def get_symbols(self, file_path: str) -> dict:
        """获取文件中的符号（函数、类等）"""
        result = self.analyzer.analyze_file(file_path)
        if result["success"]:
            return {"success": True, "data": result["data"]["symbols"], "error": None}

        try:
            response = self.session.post(
                f"{self.base_url}/symbols",
                json={"path": file_path},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def find_string_literals(self, file_path: str, pattern: str) -> dict:
        """查找字符串字面量"""
        result = self.analyzer.analyze_file(file_path)
        if result["success"]:
            issues = [issue for issue in result["data"]["issues"] if issue["type"] == "hardcoded_path"]
            return {"success": True, "data": issues, "error": None}

        try:
            response = self.session.post(
                f"{self.base_url}/find_strings",
                json={"path": file_path, "pattern": pattern},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def get_dependencies(self, file_path: str) -> dict:
        """获取文件依赖"""
        result = self.analyzer.analyze_file(file_path)
        if result["success"]:
            return {"success": True, "data": result["data"]["imports"], "error": None}

        try:
            response = self.session.post(
                f"{self.base_url}/dependencies",
                json={"path": file_path},
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Narsil MCP 客户端")
    parser.add_argument("--host", default="localhost", help="服务器地址")
    parser.add_argument("--port", type=int, default=8401, help="服务器端口")
    parser.add_argument("command", choices=["analyze", "symbols", "strings", "deps", "status"])
    parser.add_argument("path", nargs="?", help="文件路径")

    args = parser.parse_args()

    client = NarsilClient(host=args.host, port=args.port)

    if args.command == "status":
        if client.is_server_running():
            print("✅ Narsil MCP 服务器在线")
        else:
            print("❌ Narsil MCP 服务器离线，使用本地分析器")
        return

    if not args.path:
        print("错误: 请提供文件路径")
        return

    if args.command == "analyze":
        result = client.analyze_file(args.path)
    elif args.command == "symbols":
        result = client.get_symbols(args.path)
    elif args.command == "strings":
        result = client.find_string_literals(args.path, r"[A-Z]:\\")
    elif args.command == "deps":
        result = client.get_dependencies(args.path)
    else:
        result = {"error": f"未知命令: {args.command}"}

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()