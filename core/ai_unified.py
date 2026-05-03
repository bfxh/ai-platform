#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新后的AI统一入口 - 完全兼容多AI平台
向后兼容旧代码，同时支持新架构
"""

import os
import sys

sys.path.insert(0, r"\python\core")
sys.path.insert(0, r"\python\tools")

try:
    from ai_adapter import AIClientFactory, AIProvider, UnifiedAI
    from ai_adapter import ask as unified_ask
    from ai_adapter import chat_session
except ImportError:
    UnifiedAI = None
    AIClientFactory = None
    AIProvider = None
    unified_ask = None
    chat_session = None

try:
    from ai_config import get_config, set_default_provider
except ImportError:
    get_config = None
    set_default_provider = None

try:
    from router import analyze, code, design, do, review, router
except ImportError:
    do = None
    code = None
    review = None
    design = None
    analyze = None
    router = None

try:
    from workflow import dev, doc, fix, go, wf
except ImportError:
    wf = None
    go = None
    dev = None
    fix = None
    doc = None

try:
    from mcp_lite import browser
    from mcp_lite import code as code_tool
    from mcp_lite import db
    from mcp_lite import design as design_tool
    from mcp_lite import file, mcp, search
except ImportError:
    mcp = None
    file = None
    code_tool = None
    search = None
    browser = None
    db = None
    design_tool = None

try:
    from optimizer import opt, optimizer, smart_ctx
except ImportError:
    optimizer = None
    opt = None
    smart_ctx = None

try:
    from mcp_extended import MCPExtended

    MCP_EXTENDED_AVAILABLE = True
except ImportError:
    MCPExtended = None
    MCP_EXTENDED_AVAILABLE = False

try:
    from workflow_advanced import create_workflow

    WORKFLOW_ADVANCED_AVAILABLE = True
except ImportError:
    create_workflow = None
    WORKFLOW_ADVANCED_AVAILABLE = False

try:
    from agent_core import Agent

    AGENT_AVAILABLE = True
except ImportError:
    Agent = None
    AGENT_AVAILABLE = False

ROUTER_AVAILABLE = router is not None


class AI:
    """
    统一AI接口 - 多平台兼容版本

    特性:
    - 自动检测可用的AI提供商
    - 支持运行时切换
    - 向后兼容旧代码
    - 统一的API接口

    用法:
        # 基础用法（使用默认配置）
        ai = AI()
        result = ai("你好")

        # 指定提供商
        ai = AI(provider="openai")
        ai = AI(provider="claude", model="claude-3-opus")

        # 快捷调用
        from ai_unified import ask, code, chat
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
        self._provider = provider
        self._model = model
        self._client = UnifiedAI(provider=provider, model=model)
        self._config = get_config()

        # 初始化扩展工具
        self.mcp_ext = MCPExtended() if MCP_EXTENDED_AVAILABLE else None
        self.workflow = create_workflow("default") if WORKFLOW_ADVANCED_AVAILABLE else None
        self.agent = Agent(provider=provider, model=model) if AGENT_AVAILABLE else None

        # 保持向后兼容的属性
        if ROUTER_AVAILABLE:
            self.router = router
            self.workflow_old = wf
            self.mcp = mcp
            self.optimizer = optimizer

    @property
    def provider(self) -> str:
        """当前使用的AI提供商"""
        return self._client.provider

    @property
    def model(self) -> str:
        """当前使用的模型"""
        return self._client.model

    # ========== 核心方法 ==========

    def __call__(self, prompt: str, **kwargs) -> str:
        """
        极简调用 - 自动选择最优方式
        示例: ai("写快速排序")
        """
        return self._client.chat(prompt, **kwargs)

    def ask(self, question: str, **kwargs) -> str:
        """提问 - 不保持历史"""
        return self._client.chat(question, keep_history=False, **kwargs)

    def chat(self, message: str, **kwargs) -> str:
        """聊天 - 保持历史"""
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

    # ========== 文件操作 ==========

    def read(self, path: str) -> str:
        """读文件"""
        if ROUTER_AVAILABLE:
            return file("read", path)
        else:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                return f"[错误] 读取文件失败: {e}"

    def write(self, path: str, content: str) -> str:
        """写文件"""
        if ROUTER_AVAILABLE:
            return file("write", path, content=content)
        else:
            try:
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"[成功] 已写入: {path}"
            except Exception as e:
                return f"[错误] 写入文件失败: {e}"

    def ls(self, path: str = ".") -> str:
        """列目录"""
        if ROUTER_AVAILABLE:
            return file("list", path)
        else:
            try:
                items = os.listdir(path)
                return "\n".join(items)
            except Exception as e:
                return f"[错误] 列目录失败: {e}"

    # ========== 搜索 ==========

    def search(self, query: str) -> str:
        """搜索"""
        if ROUTER_AVAILABLE:
            return search(query)
        else:
            return self._client.chat(f"搜索并总结: {query}")

    def fetch(self, url: str) -> str:
        """获取网页"""
        if ROUTER_AVAILABLE:
            return browser(url)
        else:
            import urllib.request

            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    return response.read().decode("utf-8")
            except Exception as e:
                return f"[错误] 获取网页失败: {e}"

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

    # ========== 工作流 ==========

    def dev(self, feature: str, **kwargs) -> str:
        """完整开发"""
        if ROUTER_AVAILABLE:
            return go(f"dev:{feature}")
        else:
            return self._client.chat(f"完整开发功能: {feature}", **kwargs)

    def workflow(self, spec: str, **kwargs) -> str:
        """执行工作流"""
        if ROUTER_AVAILABLE:
            return go(spec)
        else:
            return self._client.chat(f"执行工作流: {spec}", **kwargs)

    # ========== 优化 ==========

    def opt(self, text: str, **kwargs) -> str:
        """优化文本"""
        return self._client.chat(f"优化以下内容:\n{text}", **kwargs)

    def ctx(self, context: str, query: str, **kwargs) -> str:
        """智能上下文"""
        return self._client.chat(f"基于以下上下文回答问题:\n{context}\n\n问题: {query}", **kwargs)

    # ========== 数据库 ==========

    def sql(self, query: str, db_path: str = None) -> str:
        """执行SQL"""
        if ROUTER_AVAILABLE:
            return db(query, db_path)
        else:
            return self._client.chat(f"SQL查询: {query}")

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
        return self._config.get_available_providers()

    def get_provider_status(self):
        """获取提供商状态"""
        self._config.print_status()

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

文件:
  ai.read(path)             # 读文件
  ai.write(path, content)   # 写文件
  ai.ls(path)               # 列目录

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


def read_file(path: str) -> str:
    """快速读文件"""
    return ai.read(path)


def write_file(path: str, content: str) -> str:
    """快速写文件"""
    return ai.write(path, content)


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


def interactive_chat(provider: str = None, model: str = None):
    """启动交互式对话"""
    chat_session(provider=provider, model=model)


# ============ 向后兼容 ============

# 保持旧版导入兼容
try:
    from claude_mode import ClaudeAgent

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

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
