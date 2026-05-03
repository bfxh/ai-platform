#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新的AI统一入口 - 基于模块化架构
"""

from adapter.ai import AIClientFactory, UnifiedAI
from core.config import get_base_dir, get_config, get_core_dir, get_tools_dir

# 延迟导入记忆召回器
_recaller = None

def _get_recaller():
    global _recaller
    if _recaller is None:
        from storage.Brain.memory.recall import get_recaller
        _recaller = get_recaller()
    return _recaller


class AI:
    """
    统一AI接口 - 多平台兼容版本

    特性:
    - 自动检测可用的AI提供商
    - 支持运行时切换
    - 向后兼容旧代码
    - 统一的API接口
    - 自动记忆召回

    用法:
        # 基础用法（使用默认配置）
        ai = AI()
        result = ai("你好")

        # 指定提供商
        ai = AI(provider="openai")
        ai = AI(provider="claude", model="claude-3-opus")

        # 快捷调用
        from ai_new import ask, code, chat
        result = ask("你好", provider="gemini")

        # 切换提供商
        ai.switch_provider("deepseek")
    """

    def __init__(self, provider: str = None, model: str = None, **kwargs):
        """
        初始化AI接口

        Args:
            provider: AI提供商名称 (stepfun/openai/anthropic/gemini/ollama/deepseek/qwen/doubao/xiaolongxia)
            model: 模型名称
            **kwargs: 额外配置
        """
        self._provider = provider or get_config("ai.default_provider", "stepfun")
        self._model = model
        self._client = UnifiedAI(provider=self._provider, model=model, **kwargs)
        self._enable_recall = kwargs.get("enable_recall", True)

    @property
    def provider(self) -> str:
        """当前使用的AI提供商"""
        return self._client.provider

    @property
    def model(self) -> str:
        """当前使用的模型"""
        return self._client.model

    def _recall_context(self, message: str) -> str:
        """召回相关记忆上下文"""
        if not self._enable_recall:
            return ""
        try:
            recaller = _get_recaller()
            result = recaller.recall(message)
            return recaller.format_context(result)
        except Exception as e:
            print(f"Memory recall error: {e}")
            return ""

    # ========== 核心方法 ==========

    def __call__(self, prompt: str, **kwargs) -> str:
        """
        极简调用 - 自动选择最优方式
        示例: ai("写快速排序")
        """
        context = self._recall_context(prompt) if kwargs.get("recall", True) else ""
        if context:
            prompt = f"{context}\n\n用户提问: {prompt}"
        return self._client.chat(prompt, **kwargs)

    def ask(self, question: str, **kwargs) -> str:
        """提问 - 不保持历史"""
        context = self._recall_context(question) if kwargs.get("recall", True) else ""
        if context:
            question = f"{context}\n\n用户提问: {question}"
        return self._client.chat(question, keep_history=False, **kwargs)

    def chat(self, message: str, **kwargs) -> str:
        """聊天 - 保持历史"""
        context = self._recall_context(message) if kwargs.get("recall", True) else ""
        if context:
            message = f"{context}\n\n用户消息: {message}"
        return self._client.chat(message, keep_history=True, **kwargs)

    # ========== 代码相关 ==========

    def write_code(self, prompt: str, **kwargs) -> str:
        """写代码"""
        return self._client.chat(f"写代码: {prompt}", **kwargs)

    def review_code(self, code_str: str, **kwargs) -> str:
        """审查代码"""
        return self._client.chat(f"审查代码:\n{code_str}", **kwargs)

    def fix(self, code_str: str, **kwargs) -> str:
        """修复代码"""
        return self._client.chat(f"修复以下代码:\n{code_str}", **kwargs)

    def test(self, code_str: str, **kwargs) -> str:
        """生成测试"""
        return self._client.chat(f"为以下代码生成测试:\n{code_str}", **kwargs)

    def doc(self, code_str: str, **kwargs) -> str:
        """生成文档"""
        return self._client.chat(f"为代码生成文档:\n{code_str}", **kwargs)

    def refactor(self, code_str: str, **kwargs) -> str:
        """重构代码"""
        return self._client.chat(f"重构以下代码:\n{code_str}", **kwargs)

    # ========== 搜索 ==========

    def search(self, query: str) -> str:
        """搜索"""
        return self._client.chat(f"搜索并总结: {query}")

    def fetch(self, url: str) -> str:
        """获取网页"""
        return self._client.chat(f"获取并总结以下网页内容:\n{url}")

    # ========== 设计 ==========

    def design(self, prompt: str, **kwargs) -> str:
        """设计"""
        return self._client.chat(f"设计: {prompt}", **kwargs)

    def ui(self, description: str, **kwargs) -> str:
        """UI设计"""
        return self._client.chat(f"设计UI: {description}", **kwargs)

    # ========== 分析 ==========

    def analyze(self, content: str, **kwargs) -> str:
        """分析"""
        return self._client.chat(f"分析以下内容:\n{content}", **kwargs)

    def summary(self, text: str, **kwargs) -> str:
        """摘要"""
        return self._client.chat(f"总结以下内容:\n{text[:5000]}", **kwargs)

    # ========== 优化 ==========

    def opt(self, text: str, **kwargs) -> str:
        """优化文本"""
        return self._client.chat(f"优化以下内容:\n{text}", **kwargs)

    def ctx(self, context: str, query: str, **kwargs) -> str:
        """智能上下文"""
        return self._client.chat(f"基于以下上下文回答问题:\n{context}\n\n问题: {query}", **kwargs)

    # ========== 提供商管理 ==========

    def switch_provider(self, provider: str, model: str = None):
        """切换AI提供商"""
        self._client.switch_provider(provider, model)
        self._provider = provider
        self._model = model or self._model
        print(f"✅ 已切换到 {provider}" + (f" ({model})" if model else ""))

    def list_providers(self) -> list:
        """列出所有支持的提供商"""
        return AIClientFactory.list_providers()

    def list_available_providers(self) -> list:
        """列出可用的提供商"""
        from core.config import get_available_providers

        return get_available_providers()

    def get_provider_status(self):
        """获取提供商状态"""
        from core.config import print_status

        print_status()

    # ========== 帮助 ==========

    def help(self) -> str:
        """帮助信息"""
        return """
AI 统一接口 - 多平台兼容版

当前提供商: {provider}

核心方法:
  ai("prompt")              # 通用调用
  ai.ask("question")        # 提问（无历史）
  ai.chat("message")        # 聊天（有历史）

代码:
  ai.write_code("需求")     # 写代码
  ai.review_code(code)      # 审查
  ai.fix(code)              # 修复
  ai.test(code)             # 测试
  ai.doc(code)              # 文档
  ai.refactor(code)         # 重构

搜索:
  ai.search(query)          # 搜索
  ai.fetch(url)             # 获取网页

设计:
  ai.design("描述")         # 设计
  ai.ui("描述")             # UI设计

分析:
  ai.analyze(content)       # 分析
  ai.summary(text)          # 摘要

提供商管理:
  ai.switch_provider("openai")     # 切换到OpenAI
  ai.switch_provider("claude")     # 切换到Claude
  ai.list_providers()              # 列出所有提供商
  ai.list_available_providers()    # 列出可用提供商
  ai.get_provider_status()         # 查看提供商状态

支持的提供商:
  - stepfun (阶跃AI)
  - openai (OpenAI)
  - anthropic (Claude)
  - gemini (Google Gemini)
  - ollama (本地模型)
  - deepseek (DeepSeek)
  - qwen (通义千问)
  - doubao (豆包)
  - xiaolongxia (小龙虾AI)

环境变量配置:
  AI_PROVIDER=openai        # 设置默认提供商
  OPENAI_API_KEY=xxx        # 设置API Key
  AI_BASE_DIR=/path/to/AI   # 设置项目根目录
        """.format(provider=self.provider)


# ============ 全局实例 ============

# 创建全局AI实例
ai = AI()

# ============ 便捷函数 ============


def ask(question: str, provider: str = None, **kwargs) -> str:
    """快速提问 - 无历史"""
    client = AI(provider=provider) if provider else ai
    return client.ask(question, **kwargs)


def chat(message: str, provider: str = None, **kwargs) -> str:
    """快速聊天 - 保持历史"""
    client = AI(provider=provider) if provider else ai
    return client.chat(message, **kwargs)


def write_code(prompt: str, provider: str = None, **kwargs) -> str:
    """快速写代码"""
    client = AI(provider=provider) if provider else ai
    return client.write_code(prompt, **kwargs)


def search_query(query: str) -> str:
    """快速搜索"""
    return ai.search(query)


def design_prompt(prompt: str, provider: str = None, **kwargs) -> str:
    """快速设计"""
    client = AI(provider=provider) if provider else ai
    return client.design(prompt, **kwargs)


def analyze_content(content: str, provider: str = None, **kwargs) -> str:
    """快速分析"""
    client = AI(provider=provider) if provider else ai
    return client.analyze(content, **kwargs)


def summary_text(text: str, provider: str = None, **kwargs) -> str:
    """快速摘要"""
    client = AI(provider=provider) if provider else ai
    return client.summary(text, **kwargs)


def switch(provider: str, model: str = None):
    """快速切换提供商"""
    ai.switch_provider(provider, model)


def status():
    """查看提供商状态"""
    ai.get_provider_status()


# ============ 向后兼容 ============

# 保持旧版导入兼容
try:
    from claude_mode import ClaudeAgent
    from claude_mode import chat as claude_chat
    from claude_mode import get_agent

    CLAUDE_MODE = True
except ImportError:
    ClaudeAgent = None
    CLAUDE_MODE = False


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("AI统一接口测试")
    print("=" * 60)

    # 显示状态
    print("\n当前提供商状态:")
    ai.get_provider_status()

    # 测试基础功能
    print("\n测试基础功能:")
    print(f"当前提供商: {ai.provider}")
    print(f"支持的提供商: {', '.join(ai.list_providers())}")

    # 测试提问
    print("\n测试提问:")
    try:
        result = ai.ask("你好，请用一句话介绍自己")
        print(f"回复: {result}")
    except Exception as e:
        print(f"错误: {e}")

    print("=" * 60)
    print("测试完成")
    print("=" * 60)
