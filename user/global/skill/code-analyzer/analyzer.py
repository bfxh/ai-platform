#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码分析技能 - 专业代码审查和优化
"""

import ast
import re
from typing import Dict, List, Any
from pathlib import Path


class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self, code: str, language: str = "python"):
        self.code = code
        self.language = language.lower()
        self.issues = []
        self.metrics = {}
    
    def analyze(self) -> Dict:
        """完整分析"""
        self.metrics = {
            "lines": len(self.code.split('\n')),
            "characters": len(self.code),
            "functions": self._count_functions(),
            "classes": self._count_classes(),
            "complexity": self._calculate_complexity(),
        }
        
        self._check_style()
        self._check_security()
        self._check_performance()
        
        return {
            "metrics": self.metrics,
            "issues": self.issues,
            "score": self._calculate_score()
        }
    
    def _count_functions(self) -> int:
        """统计函数数量"""
        if self.language == "python":
            return len(re.findall(r'^def\s+\w+', self.code, re.MULTILINE))
        return 0
    
    def _count_classes(self) -> int:
        """统计类数量"""
        if self.language == "python":
            return len(re.findall(r'^class\s+\w+', self.code, re.MULTILINE))
        return 0
    
    def _calculate_complexity(self) -> int:
        """计算圈复杂度"""
        if self.language == "python":
            try:
                tree = ast.parse(self.code)
                complexity = 1
                for node in ast.walk(tree):
                    if isinstance(node, (ast.If, ast.While, ast.For, 
                                        ast.ExceptHandler, ast.With)):
                        complexity += 1
                return complexity
            except:
                return 0
        return 0
    
    def _check_style(self):
        """检查代码风格"""
        # 检查行长度
        for i, line in enumerate(self.code.split('\n'), 1):
            if len(line) > 100:
                self.issues.append({
                    "line": i,
                    "type": "style",
                    "severity": "warning",
                    "message": f"行长度超过100字符 ({len(line)})"
                })
        
        # 检查空行
        if self.language == "python":
            lines = self.code.split('\n')
            for i, line in enumerate(lines, 1):
                if line.endswith(' ') or line.endswith('\t'):
                    self.issues.append({
                        "line": i,
                        "type": "style",
                        "severity": "info",
                        "message": "行尾有空白字符"
                    })
    
    def _check_security(self):
        """检查安全问题"""
        security_patterns = {
            r'eval\s*\(': "使用eval()存在安全风险",
            r'exec\s*\(': "使用exec()存在安全风险",
            r'subprocess\.call\s*\([^)]*shell\s*=\s*True': "使用shell=True存在命令注入风险",
            r'password\s*=\s*["\'][^"\']+["\']': "硬编码密码",
            r'secret\s*=\s*["\'][^"\']+["\']': "硬编码密钥",
        }
        
        for pattern, message in security_patterns.items():
            if re.search(pattern, self.code, re.IGNORECASE):
                self.issues.append({
                    "line": 0,
                    "type": "security",
                    "severity": "critical",
                    "message": message
                })
    
    def _check_performance(self):
        """检查性能问题"""
        # 检查列表推导式 vs 循环
        if self.language == "python":
            # 检查低效循环
            if re.search(r'for\s+\w+\s+in\s+\w+:\s*\n\s*\w+\.append', self.code):
                self.issues.append({
                    "line": 0,
                    "type": "performance",
                    "severity": "warning",
                    "message": "可以使用列表推导式优化循环"
                })
    
    def _calculate_score(self) -> int:
        """计算代码质量分数"""
        score = 100
        
        for issue in self.issues:
            if issue["severity"] == "critical":
                score -= 10
            elif issue["severity"] == "warning":
                score -= 5
            elif issue["severity"] == "info":
                score -= 1
        
        return max(0, score)


def analyze_code(path: str) -> Dict:
    """分析代码文件"""
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    ext = Path(path).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.go': 'go',
        '.rs': 'rust'
    }
    
    language = language_map.get(ext, 'unknown')
    analyzer = CodeAnalyzer(code, language)
    
    return analyzer.analyze()


def review_code(code: str, language: str = "python") -> str:
    """审查代码并返回报告"""
    analyzer = CodeAnalyzer(code, language)
    result = analyzer.analyze()
    
    report = f"""# 代码审查报告

## 基本信息
- 语言: {language}
- 总行数: {result['metrics']['lines']}
- 函数数: {result['metrics']['functions']}
- 类数: {result['metrics']['classes']}
- 圈复杂度: {result['metrics']['complexity']}
- 质量评分: {result['score']}/100

## 发现的问题 ({len(result['issues'])}个)

"""
    
    for issue in result['issues']:
        emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(issue['severity'], "⚪")
        report += f"{emoji} **{issue['type'].upper()}** (行{issue['line']}): {issue['message']}\n\n"
    
    if result['score'] >= 90:
        report += "\n✅ 代码质量优秀！"
    elif result['score'] >= 70:
        report += "\n🟡 代码质量良好，建议改进。"
    else:
        report += "\n🔴 代码需要优化，请关注上述问题。"
    
    return report


if __name__ == "__main__":
    # 测试
    test_code = """
def example():
    result = []
    for i in range(10):
        result.append(i * 2)
    return result

password = "secret123"
"""
    
    print(review_code(test_code))
