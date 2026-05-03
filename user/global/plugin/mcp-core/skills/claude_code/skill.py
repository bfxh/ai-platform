#!/usr/bin/env python3
import os
import sys
import ast
import re
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill


class ClaudeCode(Skill):
    name = "claude_code"
    description = "Claude Code - 代码分析、优化、生成和审查"
    version = "2.0.0"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}

    def execute(self, action: str, params: Dict) -> Dict:
        actions = {
            "optimize_code": self._optimize_code,
            "get_best_practices": self._get_best_practices,
            "generate_code": self._generate_code,
            "analyze_code": self._analyze_code,
        }
        fn = actions.get(action)
        if fn:
            return fn(params)
        return {"success": False, "error": f"未知动作: {action}, 可用: {list(actions.keys())}"}

    def _analyze_code(self, params: Dict) -> Dict:
        code = params.get("code")
        file_path = params.get("file_path")
        
        if file_path and not code:
            try:
                code = Path(file_path).read_text(encoding="utf-8")
            except Exception as e:
                return {"success": False, "error": f"无法读取文件: {e}"}
        
        if not code:
            return {"success": False, "error": "缺少代码内容或文件路径"}

        lines = code.split("\n")
        issues = []
        suggestions = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if re.search(r'except\s*:', stripped):
                issues.append({"line": i, "type": "bare_except", "message": "裸 except 会捕获所有异常包括 KeyboardInterrupt"})
                suggestions.append({"line": i, "fix": "使用 except Exception: 或更具体的异常类型"})
            
            if re.search(r'except\s+Exception\s*:', stripped) and i < len(lines):
                next_lines = "\n".join(lines[i:i+3])
                if 'pass' in next_lines or '...' in next_lines:
                    issues.append({"line": i, "type": "silent_exception", "message": "捕获异常后静默忽略"})
                    suggestions.append({"line": i, "fix": "至少记录日志: import logging; logging.exception(...)"})
            
            if '==' in stripped and 'None' in stripped:
                issues.append({"line": i, "type": "none_comparison", "message": "使用 == None 而非 is None"})
                suggestions.append({"line": i, "fix": "使用 is None / is not None"})
            
            if re.search(r'import\s+\*', stripped):
                issues.append({"line": i, "type": "wildcard_import", "message": "通配符导入污染命名空间"})
                suggestions.append({"line": i, "fix": "明确导入需要的名称"})
            
            if len(stripped) > 120:
                issues.append({"line": i, "type": "line_too_long", "message": f"行长度 {len(stripped)} 超过 120"})
                suggestions.append({"line": i, "fix": "拆分长行"})
            
            if re.search(r'print\s*\(', stripped) and 'def ' not in stripped:
                issues.append({"line": i, "type": "print_statement", "message": "使用 print 而非 logging"})
                suggestions.append({"line": i, "fix": "使用 logging 模块替代 print"})
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if len(node.body) > 50:
                        issues.append({"line": node.lineno, "type": "function_too_long", "message": f"函数 {node.name} 有 {len(node.body)} 行，建议拆分"})
                if isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    if len(methods) > 20:
                        issues.append({"line": node.lineno, "type": "class_too_large", "message": f"类 {node.name} 有 {len(methods)} 个方法，考虑拆分"})
        except SyntaxError as e:
            issues.append({"line": e.lineno or 0, "type": "syntax_error", "message": f"语法错误: {e.msg}"})

        complexity = "低"
        if len(issues) > 10:
            complexity = "高"
        elif len(issues) > 4:
            complexity = "中"

        return {
            "success": True,
            "analysis": {
                "total_lines": len(lines),
                "code_lines": sum(1 for l in lines if l.strip() and not l.strip().startswith("#")),
                "comment_lines": sum(1 for l in lines if l.strip().startswith("#")),
                "complexity": complexity,
                "issues": issues,
                "suggestions": suggestions,
                "issue_count": len(issues)
            }
        }

    def _optimize_code(self, params: Dict) -> Dict:
        code = params.get("code")
        file_path = params.get("file_path")
        language = params.get("language", "python")
        
        if file_path and not code:
            try:
                code = Path(file_path).read_text(encoding="utf-8")
            except Exception as e:
                return {"success": False, "error": f"无法读取文件: {e}"}
        
        if not code:
            return {"success": False, "error": "缺少代码内容"}

        optimized = code
        changes = []

        if language == "python":
            replacements = [
                (r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):\s*\n(\s+)\1\s*=\s*\2\[(\w+)\]',
                 r'for \1 in \2:\n\3# 直接迭代，无需索引'),
                (r'if\s+len\((\w+)\)\s*==\s*0:', r'if not \1:'),
                (r'if\s+len\((\w+)\)\s*>\s*0:', r'if \1:'),
                (r'if\s+\w+\s*==\s*None:', r'if \1 is None:'),
                (r'if\s+\w+\s*!=\s*None:', r'if \1 is not None:'),
                (r'\.append\(\s*\[\s*(\w+)\s*,\s*(\w+)\s*\]\s*\)', r'.append((\1, \2))  # 使用元组替代列表'),
            ]
            
            for pattern, replacement in replacements:
                new_code = re.sub(pattern, replacement, optimized)
                if new_code != optimized:
                    changes.append(f"应用优化: {pattern[:40]}...")
                    optimized = new_code

        return {
            "success": True,
            "original_code": code,
            "optimized_code": optimized,
            "changes": changes,
            "change_count": len(changes),
            "language": language
        }

    def _get_best_practices(self, params: Dict) -> Dict:
        language = params.get("language", "python")
        
        practices = {
            "python": {
                "style": ["遵循 PEP 8", "使用 f-string 格式化", "每行不超过 120 字符", "使用类型注解"],
                "structure": ["函数不超过 50 行", "类不超过 20 个方法", "模块级别函数优于静态方法", "使用 dataclass 替代简单类"],
                "error_handling": ["永远不要裸 except", "使用 logging 替代 print", "自定义异常继承 Exception", "使用 contextlib"],
                "performance": ["使用列表推导式替代 map/filter", "使用生成器处理大数据", "用 set 做成员检查", "使用 collections.defaultdict"],
                "testing": ["使用 pytest", "测试文件名 test_*.py", "使用 fixture 管理资源", "参数化测试用例"]
            },
            "javascript": {
                "style": ["使用 ESLint + Prettier", "使用 const/let 替代 var", "使用模板字符串", "解构赋值"],
                "structure": ["单一职责原则", "函数不超过 30 行", "使用 async/await", "模块化导入导出"],
                "error_handling": ["try/catch 包裹异步操作", "自定义 Error 类", "Promise 链式错误处理", "全局错误边界"],
                "performance": ["避免不必要的 re-render", "使用 Web Worker", "懒加载模块", "防抖和节流"],
                "testing": ["使用 Jest/Vitest", "测试覆盖率 > 80%", "Mock 外部依赖", "E2E 测试用 Playwright"]
            },
            "java": {
                "style": ["遵循 Java 编码规范", "使用 Optional 替代 null", "使用 try-with-resources", "StringBuilder 替代字符串拼接"],
                "structure": ["SOLID 原则", "接口优于抽象类", "组合优于继承", "依赖注入"],
                "error_handling": ["检查型 vs 非检查型异常", "不要忽略异常", "异常链保留原因", "使用自定义异常"],
                "performance": ["使用 Stream API", "避免过早优化", "合理使用缓存", "连接池管理"],
                "testing": ["JUnit 5", "Mockito", "测试金字塔", "集成测试用 TestContainers"]
            }
        }
        
        result = practices.get(language, practices["python"])
        
        return {
            "success": True,
            "language": language,
            "best_practices": result,
            "categories": list(result.keys())
        }

    def _generate_code(self, params: Dict) -> Dict:
        prompt = params.get("prompt")
        language = params.get("language", "python")
        
        if not prompt:
            return {"success": False, "error": "缺少提示词"}

        templates = {
            "python": {
                "class": 'class {name}:\n    def __init__(self{params}):\n{init_body}\n{methods}',
                "function": 'def {name}({params}):\n    """{docstring}"""\n{body}',
                "api": 'from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/{endpoint}")\nasync def {name}():\n    return {{"status": "ok"}}',
                "test": 'import pytest\n\ndef test_{name}():\n    result = {call}\n    assert result == {expected}',
                "cli": 'import argparse\n\ndef main():\n    parser = argparse.ArgumentParser(description="{desc}")\n    parser.add_argument("--input", required=True)\n    args = parser.parse_args()\n    print(args.input)\n\nif __name__ == "__main__":\n    main()',
            },
            "javascript": {
                "class": 'class {name} {{\n  constructor({params}) {{\n{init_body}\n  }}\n{methods}\n}}',
                "function": 'async function {name}({params}) {{\n{body}\n}}',
                "api": 'import express from "express";\nconst app = express();\napp.get("/{endpoint}", (req, res) => res.json({{ status: "ok" }}));',
                "test": 'import {{ test, expect }} from "vitest";\n\ntest("{name}", () => {{\n  expect({call}).toBe({expected});\n}});',
            }
        }
        
        lang_templates = templates.get(language, templates["python"])
        
        return {
            "success": True,
            "prompt": prompt,
            "language": language,
            "templates": lang_templates,
            "available_types": list(lang_templates.keys()),
            "message": "使用模板生成代码骨架，指定 type 参数选择模板类型"
        }


if __name__ == "__main__":
    skill = ClaudeCode()
    print("Claude Code 技能 v2.0")
    print("动作: optimize_code, get_best_practices, generate_code, analyze_code")
