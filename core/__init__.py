"""AI 核心模块。

包含跨 Agent 共享上下文、异常体系、管道引擎、会话记忆、
文件保护、MCP 分类器、进化引擎、AI 规则引擎等核心功能。

主要模块:
    session_memory   — 会话记忆与上下文延续
    file_protector   — CC 三级缓存文件保护
    mcp_classifier   — MCP 工具分类与验证
    evo_engine       — EvoAgentX 风格自进化引擎
    ai_rules         — AI 约束规则引擎
    infra_adapter    — 基础设施统一适配器
    superpowers      — 可组合技能链引擎 (obra/superpowers)
    evaluator        — 技能评测 + 代码质量评分 + 回归检测
    data_bridge      — TRAE ↔ CLAUDE 双向数据桥接
    trae_ide_bridge  — TRAE IDE 桥接控制
    dispatcher       — 能力单元注册与调度
    shared_context   — 跨 Agent 共享上下文
    pipeline_engine  — 管道执行引擎
"""

# 核心基础设施
from .session_memory import SessionMemory, get_memory
from .file_protector import FileProtector, get_protector
from .mcp_classifier import MCPClassifier
from .evo_engine import EvoEngine, get_evo_engine
from .ai_rules import AIRulesEngine, get_rules_engine
from .infra_adapter import InfraAdapter, get_adapter
from .superpowers import SuperpowerEngine, get_superpower_engine
from .evaluator import SkillBenchmark, QualityScorer, DashboardGenerator, get_benchmark
from .data_bridge import DataBridge, get_bridge

__all__ = [
    "SessionMemory", "get_memory",
    "FileProtector", "get_protector",
    "MCPClassifier",
    "EvoEngine", "get_evo_engine",
    "AIRulesEngine", "get_rules_engine",
    "InfraAdapter", "get_adapter",
    "SuperpowerEngine", "get_superpower_engine",
    "SkillBenchmark", "QualityScorer", "DashboardGenerator", "get_benchmark",
    "DataBridge", "get_bridge",
]
