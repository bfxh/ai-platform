#!/usr/bin/env python
"""AI 系统异常体系

所有 AI 系统异常的基类为 AIError，细分异常继承自它。
遵循 output-standards.md 第三章"错误处理规范"。
"""


class AIError(Exception):
    """AI 系统基础异常。

    所有 AI 系统相关异常的基类。提供标准化的错误信息格式。

    Attributes:
        message: 错误描述信息
        code: 可选的错误代码
        details: 可选的附加详情
    """

    def __init__(self, message: str, code: str = "", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        """将异常转换为字典，便于跨 Agent 同步。"""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }


class ConfigurationError(AIError):
    """配置错误 — 配置文件缺失、格式错误或无效参数。"""


class AgentCoordinationError(AIError):
    """Agent 协调错误 — 多 Agent 协调过程中的通信、同步、冲突等错误。"""


class AuditViolationError(AIError):
    """审计违规错误 — Brain 合规审计检测到违规行为。"""


class KnowledgeSyncError(AIError):
    """知识同步错误 — 跨 Agent 知识同步失败。"""


class OutputStandardViolationError(AIError):
    """产出标准违规错误 — AI 产出不符合标准化规范。"""


# 向后兼容别名
AIException = AIError
