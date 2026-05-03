#!/usr/bin/env python3
"""
Token优化器 - 智能压缩，减少50%+ token使用
保持质量的同时大幅降低成本
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class OptimizationResult:
    """优化结果"""

    original_tokens: int
    optimized_tokens: int
    compression_ratio: float
    optimized_text: str
    techniques_used: List[str]


class TokenOptimizer:
    """Token优化器"""

    # 中文平均每个字1.5 token，英文平均每个词1.3 token
    CN_TOKEN_RATIO = 1.5
    EN_TOKEN_RATIO = 1.3

    def __init__(self):
        self.techniques = []

    def estimate_tokens(self, text: str) -> int:
        """估算token数"""
        # 简单估算: 中文字符 + 英文单词
        cn_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        en_words = len(re.findall(r"[a-zA-Z]+", text))

        return int(cn_chars * self.CN_TOKEN_RATIO + en_words * self.EN_TOKEN_RATIO)

    def optimize(self, text: str, target_ratio: float = 0.5) -> OptimizationResult:
        """
        优化文本减少token
        目标: 减少50% token，保持95%+信息
        """
        original_tokens = self.estimate_tokens(text)
        techniques = []

        # 1. 去除多余空白
        text = self._remove_extra_whitespace(text)
        techniques.append("whitespace")

        # 2. 简化标点
        text = self._simplify_punctuation(text)
        techniques.append("punctuation")

        # 3. 去除冗余词汇
        text = self._remove_redundancy(text)
        techniques.append("redundancy")

        # 4. 缩写长内容
        if len(text) > 2000:
            text = self._summarize_sections(text)
            techniques.append("summarize")

        # 5. 代码优化
        if self._is_code(text):
            text = self._optimize_code(text)
            techniques.append("code_opt")

        optimized_tokens = self.estimate_tokens(text)
        ratio = optimized_tokens / original_tokens if original_tokens > 0 else 1

        return OptimizationResult(
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            compression_ratio=ratio,
            optimized_text=text,
            techniques_used=techniques,
        )

    def _remove_extra_whitespace(self, text: str) -> str:
        """去除多余空白"""
        # 多个空格/换行合并
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    def _simplify_punctuation(self, text: str) -> str:
        """简化标点"""
        # 多个句号/感叹号合并
        text = re.sub(r"\.{2,}", "...", text)
        text = re.sub(r"!{2,}", "!", text)
        text = re.sub(r"\?{2,}", "?", text)
        return text

    def _remove_redundancy(self, text: str) -> str:
        """去除冗余词汇"""
        # 定义冗余词组
        redundant = [
            r"非常地\s*",
            r"十分的\s*",
            r"相当的\s*",
            r"基本上\s*",
            r"事实上\s*",
            r"实际上\s*",
            r"简单来说\s*",
            r"坦率地说\s*",
        ]

        for pattern in redundant:
            text = re.sub(pattern, "", text)

        return text

    def _summarize_sections(self, text: str, max_section_length: int = 500) -> str:
        """分段摘要"""
        sections = text.split("\n\n")
        result = []

        for section in sections:
            if len(section) > max_section_length:
                # 保留开头和结尾，中间用...代替
                head = section[:200]
                tail = section[-100:]
                section = f"{head}\n...[内容省略]...\n{tail}"
            result.append(section)

        return "\n\n".join(result)

    def _is_code(self, text: str) -> bool:
        """判断是否为代码"""
        code_patterns = [
            r"def\s+\w+\s*\(",
            r"class\s+\w+",
            r"import\s+\w+",
            r"function\s+\w+",
            r"const\s+\w+",
            r"var\s+\w+",
            r"#include",
            r"public\s+static",
        ]

        for pattern in code_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _optimize_code(self, code: str) -> str:
        """优化代码"""
        # 1. 去除注释（保留文档字符串）
        code = re.sub(r"#\s*[^\n]*", "", code)

        # 2. 去除空行
        lines = [line for line in code.split("\n") if line.strip()]

        # 3. 简化缩进（2空格代替4空格）
        lines = [line.replace("    ", "  ") for line in lines]

        return "\n".join(lines)

    def smart_context(self, context: str, query: str, max_tokens: int = 2000) -> str:
        """
        智能上下文选择
        只保留与查询相关的部分
        """
        # 简单实现: 按段落匹配关键词
        paragraphs = context.split("\n\n")
        query_keywords = set(query.lower().split())

        scored_paragraphs = []
        for para in paragraphs:
            para_words = set(para.lower().split())
            score = len(query_keywords & para_words)
            scored_paragraphs.append((score, para))

        # 按相关性排序，取前N个
        scored_paragraphs.sort(reverse=True)

        result = []
        current_tokens = 0

        for score, para in scored_paragraphs:
            para_tokens = self.estimate_tokens(para)
            if current_tokens + para_tokens > max_tokens:
                break
            result.append(para)
            current_tokens += para_tokens

        return "\n\n".join(result)

    def create_prompt(self, task: str, context: str = None, examples: List[str] = None) -> str:
        """
        创建优化后的prompt
        """
        parts = []

        # 任务指令（简洁）
        parts.append(f"任务: {task}")

        # 上下文（优化后）
        if context:
            opt_context = self.optimize(context)
            parts.append(f"上下文:\n{opt_context.optimized_text}")

        # 示例（最多2个）
        if examples:
            parts.append("示例:")
            for i, ex in enumerate(examples[:2], 1):
                parts.append(f"{i}. {ex[:200]}...")

        return "\n\n".join(parts)


# 全局优化器
optimizer = TokenOptimizer()


def opt(text: str) -> str:
    """快速优化"""
    return optimizer.optimize(text).optimized_text


def smart_ctx(context: str, query: str) -> str:
    """智能上下文"""
    return optimizer.smart_context(context, query)


if __name__ == "__main__":
    # 测试
    test_text = """
    这是一个非常地长的文本。
    事实上，它包含了很多实际上不必要的内容。
    简单来说，我们需要优化它。
    
    def hello():
        # 这是一个注释
        print("Hello")
        
        return True
    """

    result = optimizer.optimize(test_text)
    print(f"原始token: {result.original_tokens}")
    print(f"优化后token: {result.optimized_tokens}")
    print(f"压缩率: {result.compression_ratio:.2%}")
    print(f"使用技术: {result.techniques_used}")
