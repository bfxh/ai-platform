#!/usr/bin/env python3
"""
统一入口 - 一句话完成所有
整合: 路由 + 工作流 + MCP + 优化

⚠️ 注意: 此文件为旧版兼容入口
推荐使用新的统一接口: from ai_unified import AI
"""

import os
import sys
from pathlib import Path

# 自动添加核心目录到系统路径
_CORE_DIR = Path(__file__).resolve().parent
if str(_CORE_DIR) not in sys.path:
    sys.path.insert(0, str(_CORE_DIR))

# 优先尝试导入新的统一接口
try:
    from ai_unified import AI as NewAI
    from ai_unified import ask as new_ask

    try:
        from ai_config import get_config
    except ImportError:
        get_config = None
    NEW_AI_AVAILABLE = True
except ImportError:
    NEW_AI_AVAILABLE = False

    # 导入原有模块
    try:
        from router import analyze, code, design, do, review, router
    except ImportError:
        do = None
    try:
        from workflow import dev, doc, fix, go, wf
    except ImportError:
        wf = None
    try:
        from mcp_lite import browser
        from mcp_lite import code as code_tool
        from mcp_lite import db
        from mcp_lite import design as design_tool
        from mcp_lite import file, mcp, search
    except ImportError:
        mcp = None
    try:
        from optimizer import opt, optimizer, smart_ctx
    except ImportError:
        optimizer = None
    OLD_MODULES_AVAILABLE = True
except ImportError:
    OLD_MODULES_AVAILABLE = False


class AI:
    """
    统一AI接口 - 兼容版
    支持新旧两种模式，自动检测并使用最佳方案

    推荐使用新接口: from ai_unified import AI
    """

    def __init__(self, provider: str = None, model: str = None):
        self._new_ai = None
        self._old_available = OLD_MODULES_AVAILABLE

        # 尝试使用新的统一接口
        if NEW_AI_AVAILABLE:
            try:
                self._new_ai = NewAI(provider=provider, model=model)
            except Exception as e:
                print(f"[警告] 新AI接口初始化失败: {e}")

        # 保持旧版属性兼容
        if self._old_available:
            self.router = router
            self.workflow = wf
            self.mcp = mcp
            self.optimizer = optimizer

    def _use_new_ai(self) -> bool:
        """判断是否使用新的AI接口"""
        return self._new_ai is not None

    @property
    def provider(self) -> str:
        """当前AI提供商"""
        if self._use_new_ai():
            return self._new_ai.provider
        return "stepfun"  # 默认

    # ========== 核心方法 ==========

    def __call__(self, prompt: str, **kwargs) -> str:
        """
        极简调用 - 自动选择最优方式
        示例: ai("写快速排序")
        """
        if self._use_new_ai():
            return self._new_ai(prompt, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return do(prompt, **kwargs)
        return "[错误] 没有可用的AI接口"

    def ask(self, question: str, **kwargs) -> str:
        """提问"""
        if self._use_new_ai():
            return self._new_ai.ask(question, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return do(question)
        return "[错误] 没有可用的AI接口"

    # ========== 代码 ==========

    def write_code(self, prompt: str, **kwargs) -> str:
        """写代码"""
        if self._use_new_ai():
            return self._new_ai.write_code(prompt, **kwargs)
        if OLD_MODULES_AVAILABLE:
            try:
                from router import code as router_code
            except ImportError:
                code = None
            return router_code(prompt)
        return "[错误] 没有可用的AI接口"

    def review_code(self, code_str: str, **kwargs) -> str:
        """审查代码"""
        if self._use_new_ai():
            return self._new_ai.review_code(code_str, **kwargs)
        if OLD_MODULES_AVAILABLE:
            try:
                from router import review as router_review
            except ImportError:
                review = None
            return router_review(code_str)
        return "[错误] 没有可用的AI接口"

    def fix(self, code_str: str, **kwargs) -> str:
        """修复代码"""
        if self._use_new_ai():
            return self._new_ai.fix(code_str, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return go(f"fix:{code_str}")
        return "[错误] 没有可用的AI接口"

    def test(self, code_str: str, **kwargs) -> str:
        """生成测试"""
        if self._use_new_ai():
            return self._new_ai.test(code_str, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return do(f"为以下代码生成测试:\n{code_str}")
        return "[错误] 没有可用的AI接口"

    def doc(self, code_str: str, **kwargs) -> str:
        """生成文档"""
        if self._use_new_ai():
            return self._new_ai.doc(code_str, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return go(f"doc:{code_str}")
        return "[错误] 没有可用的AI接口"

    def refactor(self, code_str: str, **kwargs) -> str:
        """重构代码"""
        if self._use_new_ai():
            return self._new_ai.refactor(code_str, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return go(f"refactor:{code_str}")
        return "[错误] 没有可用的AI接口"

    # ========== 文件 ==========

    def read(self, path: str) -> str:
        """读文件"""
        if self._use_new_ai():
            return self._new_ai.read(path)
        if OLD_MODULES_AVAILABLE:
            return file("read", path)
        # 基础实现
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"[错误] 读取文件失败: {e}"

    def write(self, path: str, content: str) -> str:
        """写文件"""
        if self._use_new_ai():
            return self._new_ai.write(path, content)
        if OLD_MODULES_AVAILABLE:
            return file("write", path, content=content)
        # 基础实现
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"[成功] 已写入: {path}"
        except Exception as e:
            return f"[错误] 写入文件失败: {e}"

    def ls(self, path: str = ".") -> str:
        """列目录"""
        if self._use_new_ai():
            return self._new_ai.ls(path)
        if OLD_MODULES_AVAILABLE:
            return file("list", path)
        # 基础实现
        try:
            items = os.listdir(path)
            return "\n".join(items)
        except Exception as e:
            return f"[错误] 列目录失败: {e}"

    # ========== 搜索 ==========

    def search(self, query: str) -> str:
        """搜索"""
        if self._use_new_ai():
            return self._new_ai.search(query)
        if OLD_MODULES_AVAILABLE:
            return search(query)
        return "[错误] 搜索功能不可用"

    def fetch(self, url: str) -> str:
        """获取网页"""
        if self._use_new_ai():
            return self._new_ai.fetch(url)
        if OLD_MODULES_AVAILABLE:
            return browser(url)
        return "[错误] 网页获取功能不可用"

    # ========== 设计 ==========

    def design(self, prompt: str, **kwargs) -> str:
        """设计"""
        if self._use_new_ai():
            return self._new_ai.design(prompt, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return design(prompt)
        return "[错误] 没有可用的AI接口"

    def ui(self, description: str, **kwargs) -> str:
        """UI设计"""
        if self._use_new_ai():
            return self._new_ai.ui(description, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return do(f"设计UI: {description}")
        return "[错误] 没有可用的AI接口"

    # ========== 分析 ==========

    def analyze(self, content: str, **kwargs) -> str:
        """分析"""
        if self._use_new_ai():
            return self._new_ai.analyze(content, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return analyze(content)
        return "[错误] 没有可用的AI接口"

    def summary(self, text: str, **kwargs) -> str:
        """摘要"""
        if self._use_new_ai():
            return self._new_ai.summary(text, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return do(f"总结以下内容:\n{text[:3000]}")
        return "[错误] 没有可用的AI接口"

    # ========== 工作流 ==========

    def dev(self, feature: str, **kwargs) -> str:
        """完整开发"""
        if self._use_new_ai():
            return self._new_ai.dev(feature, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return dev(feature)
        return "[错误] 没有可用的AI接口"

    def workflow(self, spec: str, **kwargs) -> str:
        """执行工作流"""
        if self._use_new_ai():
            return self._new_ai.workflow(spec, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return go(spec)
        return "[错误] 没有可用的AI接口"

    # ========== 优化 ==========

    def opt(self, text: str, **kwargs) -> str:
        """优化文本"""
        if self._use_new_ai():
            return self._new_ai.opt(text, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return opt(text)
        return "[错误] 没有可用的AI接口"

    def ctx(self, context: str, query: str, **kwargs) -> str:
        """智能上下文"""
        if self._use_new_ai():
            return self._new_ai.ctx(context, query, **kwargs)
        if OLD_MODULES_AVAILABLE:
            return smart_ctx(context, query)
        return "[错误] 没有可用的AI接口"

    # ========== 数据库 ==========

    def sql(self, query: str, db_path: str = None) -> str:
        """执行SQL"""
        if self._use_new_ai():
            return self._new_ai.sql(query, db_path)
        if OLD_MODULES_AVAILABLE:
            return db(query, db_path)
        return "[错误] 数据库功能不可用"

    # ========== 新增: 提供商管理 ==========

    def switch_provider(self, provider: str, model: str = None):
        """切换AI提供商"""
        if self._use_new_ai():
            self._new_ai.switch_provider(provider, model)
        else:
            print(f"[警告] 新AI接口不可用，无法切换提供商")

    def list_providers(self) -> list:
        """列出所有支持的提供商"""
        if self._use_new_ai():
            return self._new_ai.list_providers()
        return ["stepfun"]  # 默认

    def get_provider_status(self):
        """获取提供商状态"""
        if self._use_new_ai():
            self._new_ai.get_provider_status()
        else:
            print("[警告] 新AI接口不可用")

    # ========== 快捷命令 ==========

    def help(self) -> str:
        """帮助"""
        help_text = """
AI 统一接口 - 可用方法:

核心:
  ai("prompt")          # 通用调用
  ai.ask("question")    # 提问
  ai.chat("message")    # 聊天（保持历史）

代码:
  ai.write_code("需求")       # 写代码
  ai.review_code(code)       # 审查
  ai.fix_code(code)          # 修复
  ai.test_code(code)         # 测试
  ai.doc_code(code)          # 文档
  ai.refactor_code(code)     # 重构

文件:
  ai.read(path)         # 读文件
  ai.write(path, content) # 写文件
  ai.ls(path)           # 列目录

搜索:
  ai.search(query)      # 搜索
  ai.fetch(url)         # 获取网页

设计:
  ai.design("描述")     # 设计
  ai.ui("描述")         # UI设计

分析:
  ai.analyze(content)   # 分析
  ai.summary(text)      # 摘要

工作流:
  ai.dev("功能")        # 完整开发
  ai.workflow("type:task") # 执行工作流

优化:
  ai.opt(text)          # 优化文本
  ai.ctx(context, query) # 智能上下文

数据库:
  ai.sql(query)         # SQL查询

提供商管理:
  ai.switch_provider("openai")  # 切换提供商
  ai.list_providers()           # 列出提供商
  ai.get_provider_status()      # 查看状态

当前提供商: {provider}
        """.format(provider=self.provider)
        return help_text


# 全局实例 - 自动检测最佳配置
ai = AI()


# 快捷函数 - 使用新接口优先
def ask(q: str, **kwargs) -> str:
    """快速提问"""
    if NEW_AI_AVAILABLE:
        return new_ask(q, **kwargs)
    return AI().ask(q, **kwargs)


def write_code(p: str, **kwargs) -> str:
    """快速写代码"""
    return AI().write_code(p, **kwargs)


def read_file(p: str) -> str:
    """快速读文件"""
    return AI().read(p)


def write_file(p: str, c: str) -> str:
    """快速写文件"""
    return AI().write(p, c)


def search_query(q: str) -> str:
    """快速搜索"""
    return AI().search(q)


def design_prompt(p: str, **kwargs) -> str:
    """快速设计"""
    return AI().design(p, **kwargs)


def analyze_content(c: str, **kwargs) -> str:
    """快速分析"""
    return AI().analyze(c, **kwargs)


def summary_text(t: str, **kwargs) -> str:
    """快速摘要"""
    return AI().summary(t, **kwargs)


def dev_feature(f: str, **kwargs) -> str:
    """快速开发"""
    return AI().dev(f, **kwargs)


def fix_code(c: str, **kwargs) -> str:
    """快速修复"""
    return AI().fix(c, **kwargs)


def doc_code(c: str, **kwargs) -> str:
    """快速生成文档"""
    return AI().doc(c, **kwargs)


def opt_text(t: str, **kwargs) -> str:
    """快速优化"""
    return AI().opt(t, **kwargs)


# 代码别名（向后兼容）
code = write_code
review = lambda c, **kw: AI().review_code(c, **kw)

# Claude模式导入
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
    print(f"\n当前提供商: {ai.provider}")
    print(f"新接口可用: {NEW_AI_AVAILABLE}")
    print(f"旧模块可用: {OLD_MODULES_AVAILABLE}")
    print("\n" + ai.help())
