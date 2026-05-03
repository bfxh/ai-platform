#!/usr/bin/env python3
"""
深度Bug检查器 - 多层次代码分析
静态分析 + 动态分析 + AI分析
"""

import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class BugSeverity(Enum):
    CRITICAL = "critical"  # 崩溃、安全漏洞
    HIGH = "high"  # 严重逻辑错误
    MEDIUM = "medium"  # 潜在问题
    LOW = "low"  # 代码风格
    INFO = "info"  # 建议


class BugCategory(Enum):
    SYNTAX = "syntax"  # 语法错误
    LOGIC = "logic"  # 逻辑错误
    SECURITY = "security"  # 安全漏洞
    PERFORMANCE = "performance"  # 性能问题
    MEMORY = "memory"  # 内存问题
    CONCURRENCY = "concurrency"  # 并发问题
    STYLE = "style"  # 代码风格
    MAINTAINABILITY = "maintainability"  # 可维护性


@dataclass
class Bug:
    """Bug定义"""

    id: str
    severity: BugSeverity
    category: BugCategory
    file: str
    line: int
    column: int
    message: str
    code_snippet: str
    suggestion: str
    confidence: float  # 0-1
    fix_available: bool = False
    auto_fix: Optional[str] = None


class DeepBugChecker:
    """深度Bug检查器"""

    def __init__(self):
        self.bugs: List[Bug] = []
        self.checked_files: set = set()

    def check_file(self, filepath: str, deep: bool = True) -> List[Bug]:
        """检查单个文件"""
        if not os.path.exists(filepath):
            return []

        self.checked_files.add(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        bugs = []

        # 1. 语法检查
        bugs.extend(self._check_syntax(code, filepath))

        # 2. 基础静态分析
        bugs.extend(self._check_basic_patterns(code, filepath))

        # 3. 深度分析
        if deep:
            bugs.extend(self._check_logic_errors(code, filepath))
            bugs.extend(self._check_security_issues(code, filepath))
            bugs.extend(self._check_performance_issues(code, filepath))
            bugs.extend(self._check_memory_issues(code, filepath))
            bugs.extend(self._check_concurrency_issues(code, filepath))
            bugs.extend(self._check_maintainability(code, filepath))

        self.bugs.extend(bugs)
        return bugs

    def _check_syntax(self, code: str, filepath: str) -> List[Bug]:
        """语法检查"""
        bugs = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            bugs.append(
                Bug(
                    id=f"SYN-{e.lineno}",
                    severity=BugSeverity.CRITICAL,
                    category=BugCategory.SYNTAX,
                    file=filepath,
                    line=e.lineno or 1,
                    column=e.offset or 0,
                    message=f"语法错误: {e.msg}",
                    code_snippet=self._get_line(code, e.lineno or 1),
                    suggestion="修复语法错误",
                    confidence=1.0,
                )
            )
        return bugs

    def _check_basic_patterns(self, code: str, filepath: str) -> List[Bug]:
        """基础模式检查"""
        bugs = []
        lines = code.split("\n")

        # 危险函数
        dangerous_patterns = [
            (r"eval\s*\(", "使用eval()存在代码注入风险", BugSeverity.CRITICAL),
            (r"exec\s*\(", "使用exec()存在代码注入风险", BugSeverity.CRITICAL),
            (r"input\s*\(\s*\)", "使用input()存在安全风险", BugSeverity.HIGH),
            (r"os\.system\s*\(", "使用os.system()存在命令注入风险", BugSeverity.HIGH),
            (r"subprocess\.call\s*\([^)]*shell\s*=\s*True", "使用shell=True存在命令注入风险", BugSeverity.HIGH),
        ]

        for pattern, msg, severity in dangerous_patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    bugs.append(
                        Bug(
                            id=f"SEC-{i}",
                            severity=severity,
                            category=BugCategory.SECURITY,
                            file=filepath,
                            line=i,
                            column=line.find("eval") if "eval" in line else 0,
                            message=msg,
                            code_snippet=line.strip(),
                            suggestion="使用更安全的替代方案",
                            confidence=0.9,
                        )
                    )

        # 未使用的变量
        unused_vars = self._find_unused_variables(code)
        for var, line_no in unused_vars:
            bugs.append(
                Bug(
                    id=f"UNU-{line_no}",
                    severity=BugSeverity.LOW,
                    category=BugCategory.MAINTAINABILITY,
                    file=filepath,
                    line=line_no,
                    column=0,
                    message=f"未使用的变量: {var}",
                    code_snippet=self._get_line(code, line_no),
                    suggestion=f"删除未使用的变量 '{var}' 或使用它",
                    confidence=0.8,
                )
            )

        return bugs

    def _check_logic_errors(self, code: str, filepath: str) -> List[Bug]:
        """逻辑错误检查"""
        bugs = []
        lines = code.split("\n")

        # 无限循环检查
        for i, line in enumerate(lines, 1):
            if re.search(r"while\s+True\s*:", line):
                # 检查是否有break
                has_break = False
                for j in range(i, min(i + 20, len(lines))):
                    if "break" in lines[j]:
                        has_break = True
                        break
                if not has_break:
                    bugs.append(
                        Bug(
                            id=f"INF-{i}",
                            severity=BugSeverity.HIGH,
                            category=BugCategory.LOGIC,
                            file=filepath,
                            line=i,
                            column=0,
                            message="可能的无限循环: while True没有break",
                            code_snippet=line.strip(),
                            suggestion="添加break条件或使用for循环",
                            confidence=0.7,
                        )
                    )

        # 空except
        for i, line in enumerate(lines, 1):
            if re.search(r"except\s*:", line) or re.search(r"except\s+Exception\s*:", line):
                bugs.append(
                    Bug(
                        id=f"EMP-{i}",
                        severity=BugSeverity.MEDIUM,
                        category=BugCategory.LOGIC,
                        file=filepath,
                        line=i,
                        column=0,
                        message="捕获所有异常可能隐藏错误",
                        code_snippet=line.strip(),
                        suggestion="捕获具体异常类型",
                        confidence=0.8,
                    )
                )

        # 变量在使用前定义检查
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    # 简化检查，实际应该做作用域分析
                    pass
        except:
            pass

        return bugs

    def _check_security_issues(self, code: str, filepath: str) -> List[Bug]:
        """安全检查"""
        bugs = []
        lines = code.split("\n")

        # SQL注入
        sql_patterns = [
            r"execute\s*\([^)]*%s",
            r"execute\s*\([^)]*\+",
            r"execute\s*\([^)]*\.format\s*\(",
            r'execute\s*\([^)]*f["\']',
        ]

        for pattern in sql_patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    bugs.append(
                        Bug(
                            id=f"SQL-{i}",
                            severity=BugSeverity.CRITICAL,
                            category=BugCategory.SECURITY,
                            file=filepath,
                            line=i,
                            column=0,
                            message="可能的SQL注入漏洞",
                            code_snippet=line.strip(),
                            suggestion="使用参数化查询",
                            confidence=0.85,
                        )
                    )

        # 硬编码密钥
        key_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "硬编码API密钥"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "硬编码密钥"),
        ]

        for pattern, msg in key_patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    # 排除环境变量和配置
                    if "os.environ" not in line and "getenv" not in line:
                        bugs.append(
                            Bug(
                                id=f"KEY-{i}",
                                severity=BugSeverity.CRITICAL,
                                category=BugCategory.SECURITY,
                                file=filepath,
                                line=i,
                                column=0,
                                message=f"{msg}",
                                code_snippet=line.strip()[:50] + "...",
                                suggestion="使用环境变量或密钥管理服务",
                                confidence=0.9,
                            )
                        )

        return bugs

    def _check_performance_issues(self, code: str, filepath: str) -> List[Bug]:
        """性能检查"""
        bugs = []
        lines = code.split("\n")

        # 列表推导式vs循环
        for i, line in enumerate(lines, 1):
            if re.search(r"for\s+\w+\s+in\s+\w+:\s*$", line):
                # 检查下一行是否是append
                if i < len(lines) and "append" in lines[i]:
                    bugs.append(
                        Bug(
                            id=f"PERF-{i}",
                            severity=BugSeverity.LOW,
                            category=BugCategory.PERFORMANCE,
                            file=filepath,
                            line=i,
                            column=0,
                            message="可以使用列表推导式优化",
                            code_snippet=line.strip(),
                            suggestion="使用列表推导式替代循环+append",
                            confidence=0.6,
                        )
                    )

        # 重复计算
        for i, line in enumerate(lines, 1):
            if re.search(r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(", line):
                bugs.append(
                    Bug(
                        id=f"ENUM-{i}",
                        severity=BugSeverity.LOW,
                        category=BugCategory.PERFORMANCE,
                        file=filepath,
                        line=i,
                        column=0,
                        message="使用enumerate替代range(len())",
                        code_snippet=line.strip(),
                        suggestion="使用enumerate()",
                        confidence=0.8,
                    )
                )

        return bugs

    def _check_memory_issues(self, code: str, filepath: str) -> List[Bug]:
        """内存检查"""
        bugs = []
        lines = code.split("\n")

        # 大列表创建
        for i, line in enumerate(lines, 1):
            if re.search(r"range\s*\(\s*1000000", line):
                bugs.append(
                    Bug(
                        id=f"MEM-{i}",
                        severity=BugSeverity.MEDIUM,
                        category=BugCategory.MEMORY,
                        file=filepath,
                        line=i,
                        column=0,
                        message="大范围可能消耗大量内存",
                        code_snippet=line.strip(),
                        suggestion="使用生成器或迭代器",
                        confidence=0.7,
                    )
                )

        # 循环引用（简化检查）
        if "__del__" in code:
            bugs.append(
                Bug(
                    id=f"DEL-1",
                    severity=BugSeverity.LOW,
                    category=BugCategory.MEMORY,
                    file=filepath,
                    line=1,
                    column=0,
                    message="使用__del__可能导致循环引用问题",
                    code_snippet="__del__方法",
                    suggestion="使用weakref或上下文管理器",
                    confidence=0.5,
                )
            )

        return bugs

    def _check_concurrency_issues(self, code: str, filepath: str) -> List[Bug]:
        """并发检查"""
        bugs = []
        lines = code.split("\n")

        # 全局变量修改
        has_thread = "threading" in code or "Thread" in code
        has_global = "global " in code

        if has_thread and has_global:
            bugs.append(
                Bug(
                    id=f"CON-1",
                    severity=BugSeverity.HIGH,
                    category=BugCategory.CONCURRENCY,
                    file=filepath,
                    line=1,
                    column=0,
                    message="多线程中使用全局变量可能导致竞态条件",
                    code_snippet="global变量 + threading",
                    suggestion="使用锁或线程安全的数据结构",
                    confidence=0.7,
                )
            )

        return bugs

    def _check_maintainability(self, code: str, filepath: str) -> List[Bug]:
        """可维护性检查"""
        bugs = []
        lines = code.split("\n")

        # 函数长度
        in_function = False
        func_start = 0
        func_lines = 0

        for i, line in enumerate(lines, 1):
            if re.search(r"^def\s+\w+\s*\(", line):
                if in_function and func_lines > 50:
                    bugs.append(
                        Bug(
                            id=f"LONG-{func_start}",
                            severity=BugSeverity.LOW,
                            category=BugCategory.MAINTAINABILITY,
                            file=filepath,
                            line=func_start,
                            column=0,
                            message=f"函数过长 ({func_lines}行)",
                            code_snippet=f"函数从第{func_start}行开始",
                            suggestion="将函数拆分为更小的函数",
                            confidence=0.8,
                        )
                    )
                in_function = True
                func_start = i
                func_lines = 0
            elif in_function:
                if line.strip() and not line.startswith(" "):
                    in_function = False
                else:
                    func_lines += 1

        # 复杂度检查（简化）
        for i, line in enumerate(lines, 1):
            indent = len(line) - len(line.lstrip())
            if indent > 40:  # 8层缩进
                bugs.append(
                    Bug(
                        id=f"IND-{i}",
                        severity=BugSeverity.LOW,
                        category=BugCategory.MAINTAINABILITY,
                        file=filepath,
                        line=i,
                        column=0,
                        message="嵌套层级过深",
                        code_snippet=line.strip()[:50],
                        suggestion="重构减少嵌套层级",
                        confidence=0.7,
                    )
                )

        return bugs

    def _find_unused_variables(self, code: str) -> List[Tuple[str, int]]:
        """查找未使用的变量"""
        unused = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    assigned = set()
                    used = set()
                    for n in ast.walk(node):
                        if isinstance(n, ast.Name):
                            if isinstance(n.ctx, ast.Store):
                                assigned.add(n.id)
                            elif isinstance(n.ctx, ast.Load):
                                used.add(n.id)
                    for var in assigned - used - {"_", "self", "cls"}:
                        # 找到定义行
                        for n in ast.walk(node):
                            if isinstance(n, ast.Name) and n.id == var:
                                unused.append((var, n.lineno))
                                break
        except:
            pass
        return unused

    def _get_line(self, code: str, line_no: int) -> str:
        """获取指定行"""
        lines = code.split("\n")
        if 1 <= line_no <= len(lines):
            return lines[line_no - 1].strip()
        return ""

    def check_directory(self, dirpath: str, pattern: str = "*.py") -> List[Bug]:
        """检查目录"""
        import glob

        bugs = []
        for filepath in glob.glob(os.path.join(dirpath, "**", pattern), recursive=True):
            bugs.extend(self.check_file(filepath))
        return bugs

    def generate_report(self, format: str = "text") -> str:
        """生成报告"""
        if format == "json":
            return json.dumps(
                [
                    {
                        "id": b.id,
                        "severity": b.severity.value,
                        "category": b.category.value,
                        "file": b.file,
                        "line": b.line,
                        "message": b.message,
                        "suggestion": b.suggestion,
                    }
                    for b in self.bugs
                ],
                indent=2,
                ensure_ascii=False,
            )

        # 文本格式
        lines = ["=" * 60, "深度Bug检查报告", "=" * 60, ""]

        # 统计
        severity_count = {}
        category_count = {}
        for bug in self.bugs:
            severity_count[bug.severity.value] = severity_count.get(bug.severity.value, 0) + 1
            category_count[bug.category.value] = category_count.get(bug.category.value, 0) + 1

        lines.append("【统计】")
        lines.append(f"总Bug数: {len(self.bugs)}")
        lines.append(f"严重级别: {dict(severity_count)}")
        lines.append(f"类别分布: {dict(category_count)}")
        lines.append("")

        # 按严重级别排序
        severity_order = [BugSeverity.CRITICAL, BugSeverity.HIGH, BugSeverity.MEDIUM, BugSeverity.LOW, BugSeverity.INFO]
        for severity in severity_order:
            bugs = [b for b in self.bugs if b.severity == severity]
            if bugs:
                lines.append(f"\n【{severity.value.upper()}】({len(bugs)}个)")
                lines.append("-" * 60)
                for bug in bugs:
                    lines.append(f"\n{bug.id}: {bug.message}")
                    lines.append(f"  文件: {bug.file}:{bug.line}")
                    lines.append(f"  代码: {bug.code_snippet[:60]}")
                    lines.append(f"  建议: {bug.suggestion}")
                    lines.append(f"  置信度: {bug.confidence:.0%}")

        return "\n".join(lines)

    def auto_fix(self, bug: Bug) -> Optional[str]:
        """自动修复"""
        if not os.path.exists(bug.file):
            return None

        with open(bug.file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if bug.line > len(lines):
            return None

        # 简单修复规则
        line = lines[bug.line - 1]
        fixed_line = line

        if bug.category == BugCategory.STYLE:
            # 去除行尾空格
            fixed_line = line.rstrip() + "\n"
        elif "except:" in line and "Exception" not in line:
            # 修复空except
            fixed_line = line.replace("except:", "except Exception:")
        elif "range(len(" in line:
            # 修复为enumerate
            fixed_line = line.replace("range(len(", "enumerate(")
        else:
            return None

        if fixed_line != line:
            lines[bug.line - 1] = fixed_line
            return "".join(lines)

        return None


# 便捷函数
def check_file(filepath: str) -> List[Bug]:
    """检查文件"""
    checker = DeepBugChecker()
    return checker.check_file(filepath)


def check_code(code: str, filename: str = "<string>") -> List[Bug]:
    """检查代码"""
    checker = DeepBugChecker()
    # 临时保存到文件
    temp_file = f"/tmp/check_{hash(code)}.py"
    os.makedirs("/tmp", exist_ok=True)
    with open(temp_file, "w") as f:
        f.write(code)
    bugs = checker.check_file(temp_file)
    # 更新文件名
    for bug in bugs:
        bug.file = filename
    os.remove(temp_file)
    return bugs


if __name__ == "__main__":
    # 测试
    test_code = """
def bad_function():
    x = 1  # 未使用
    password = "123456"  # 硬编码
    eval(input())  # 危险
    for i in range(len(items)):  # 性能
        pass
"""

    checker = DeepBugChecker()
    bugs = check_code(test_code)
    print(f"发现 {len(bugs)} 个问题")
    for bug in bugs:
        print(f"[{bug.severity.value}] {bug.message}")
