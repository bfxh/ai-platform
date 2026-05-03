#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 约束规则引擎 — 操作前自动校验，防止 AI 执行危险/违规操作

核心设计:
- 规则用 YAML 定义，分类管理（security / file / system / code / resource）
- 每个规则有: 条件、优先级、动作(deny/warn/allow)、原因
- 支持模式匹配（regex + glob）+ 白名单/黑名单
- 集成到 InfraAdapter → Dispatcher → Skill 执行链

EvoAgentX 启发:
    "约束不是限制，是进化方向。每条规则都是经过验证的最优实践。"

用法:
    from core.ai_rules import AIRulesEngine

    engine = AIRulesEngine()
    result = engine.validate("write_file", {"path": "core/dispatcher.py"})
    if not result["allowed"]:
        print(f"操作被阻止: {result['reason']}")
"""

import json
import os
import re
import yaml
from fnmatch import fnmatch
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple


# ================================================================
# 默认规则集（内置）
# ================================================================

DEFAULT_RULES = {
    "rules_version": "1.0.0",
    "categories": {
        "security": {
            "description": "安全相关规则 — 最高优先级",
            "priority_base": 100,
        },
        "file_protection": {
            "description": "文件保护规则 — 防止误删核心文件",
            "priority_base": 90,
        },
        "system_access": {
            "description": "系统访问规则 — 限制危险系统操作",
            "priority_base": 80,
        },
        "code_quality": {
            "description": "代码质量规则 — 确保生成代码符合标准",
            "priority_base": 50,
        },
        "resource_limits": {
            "description": "资源限制 — 防止过度消耗",
            "priority_base": 40,
        },
        "superpowers": {
            "description": "强制工作流规则 — 保证 TDD/安全审计等不可跳过",
            "priority_base": 85,
        },
    },
    "rules": [
        # ---- SECURITY ----
        {
            "id": "SEC-001",
            "category": "security",
            "description": "禁止删除核心系统文件",
            "patterns": [
                "core/**/*.py",
                "scripts/**/*.py",
                "storage/**/da.py",
                "user/global/plugin/mcp-core/**/*.py",
            ],
            "actions": ["delete_file", "move_file", "rm", "del"],
            "effect": "deny",
            "reason": "核心系统文件不可删除。如需修改，请使用 safe_write 自动备份。",
            "priority": 100,
        },
        {
            "id": "SEC-002",
            "category": "security",
            "description": "禁止执行危险系统命令",
            "patterns": [
                r"rm\s+-rf\s+/",
                r"format\s+[cdefgh]:",
                r"del\s+/[fsq].*",
                r"shutdown",
                r"Restart-Computer",
                r"Stop-Computer",
            ],
            "actions": ["execute_command", "trae_command", "run_command"],
            "effect": "deny",
            "reason": "禁止执行危险系统命令（格式化、强制删除、关机等）",
            "priority": 100,
        },
        {
            "id": "SEC-003",
            "category": "security",
            "description": "禁止在生产环境写入 .env 或凭证文件",
            "patterns": [
                "*.env",
                "**/.env",
                "*credentials*",
                "*secret*",
                "*.pem",
                "*.key",
            ],
            "actions": ["write_file"],
            "effect": "warn",
            "reason": "凭证文件应手动管理。如确需写入，请先备份。",
            "priority": 95,
        },
        # ---- FILE PROTECTION ----
        {
            "id": "FILE-001",
            "category": "file_protection",
            "description": "修改受保护文件前必须备份",
            "patterns": [],  # 动态从 file_protector 获取
            "actions": ["write_file", "edit_file"],
            "effect": "require_backup",
            "reason": "受保护文件修改前必须自动备份到 CC/2_old",
            "priority": 90,
        },
        {
            "id": "FILE-002",
            "category": "file_protection",
            "description": "禁止在非项目目录创建文件",
            "patterns": [
                "C:/Windows/**",
                "C:/Program Files/**",
                "C:/Program Files (x86)/**",
                "/etc/**",
                "/usr/**",
                "/bin/**",
            ],
            "actions": ["write_file", "create_directory"],
            "effect": "deny",
            "reason": "禁止在系统目录创建文件",
            "priority": 90,
        },
        # ---- SYSTEM ACCESS ----
        {
            "id": "SYS-001",
            "category": "system_access",
            "description": "限制高危注册表操作",
            "patterns": [
                r"HKEY_LOCAL_MACHINE",
                r"HKLM:",
                r"reg\s+(add|delete)\s+HKLM",
            ],
            "actions": ["execute_command", "trae_command"],
            "effect": "warn",
            "reason": "修改系统注册表可能影响系统稳定性",
            "priority": 85,
        },
        # ---- CODE QUALITY ----
        {
            "id": "CODE-001",
            "category": "code_quality",
            "description": "Python 文件不能有语法错误",
            "patterns": ["*.py"],
            "actions": ["write_file"],
            "effect": "warn",
            "reason": "写入前应确保代码语法正确",
            "priority": 55,
        },
        # ---- RESOURCE LIMITS ----
        {
            "id": "RES-001",
            "category": "resource_limits",
            "description": "单次写入文件不能超过 10MB",
            "patterns": [],
            "actions": ["write_file"],
            "effect": "deny",
            "reason": "单次写入超过 10MB 可能触发 OOM",
            "priority": 45,
            "condition": "content_size > 10485760",
        },
        # ---- SUPERPOWERS ----
        {
            "id": "SUPER-001",
            "category": "superpowers",
            "description": "强制工作流不可跳过 — TDD/安全审计等必须执行",
            "patterns": [],
            "actions": ["execute_superpower", "skip_superpower"],
            "effect": "deny",
            "reason": "检测到匹配的强制工作流 (TDD/安全审计等)，不可跳过。请先完成工作流。",
            "priority": 85,
        },
    ],
}


class AIRulesEngine:
    """AI 约束规则引擎"""

    def __init__(self, base_dir: str = None, rules_file: str = None):
        if base_dir is None:
            base_dir = os.environ.get(
                "AI_BASE_DIR",
                str(Path(__file__).resolve().parent.parent)
            )
        self.base_dir = Path(base_dir)
        self.rules_file = (
            Path(rules_file) if rules_file
            else self.base_dir / "storage" / "rules" / "ai_rules.yaml"
        )

        # 加载规则
        self.rules_config = self._load_rules()
        self.rules: List[dict] = self.rules_config.get("rules", [])
        self.categories: dict = self.rules_config.get("categories", {})

        # 编译正则
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

        # 统计
        self.stats = {
            "total_validations": 0,
            "allowed": 0,
            "denied": 0,
            "warned": 0,
            "violations": [],
        }

    # ================================================================
    # 规则加载
    # ================================================================

    def _load_rules(self) -> dict:
        """加载规则（文件优先 → 内置默认）"""
        if self.rules_file.exists():
            try:
                with open(self.rules_file, "r", encoding="utf-8") as f:
                    rules = yaml.safe_load(f)
                if rules and isinstance(rules, dict) and "rules" in rules:
                    return rules
            except Exception as e:
                print(f"[AIRules] 规则文件加载失败: {e}，使用默认规则")

        # 确保目录存在并写入默认规则
        self.rules_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.rules_file, "w", encoding="utf-8") as f:
            yaml.dump(DEFAULT_RULES, f, allow_unicode=True, default_flow_style=False)

        return DEFAULT_RULES

    def _compile_patterns(self):
        """预编译正则模式"""
        for rule in self.rules:
            rid = rule.get("id", "?")
            compiled = []
            for pattern in rule.get("patterns", []):
                try:
                    if any(c in pattern for c in ".*+?[](){}|^$\\"):
                        compiled.append(re.compile(pattern, re.IGNORECASE))
                except re.error:
                    pass  # glob 模式不需要编译
            if compiled:
                self._compiled_patterns[rid] = compiled

    def reload_rules(self) -> bool:
        """重新加载规则"""
        self.rules_config = self._load_rules()
        self.rules = self.rules_config.get("rules", [])
        self._compile_patterns()
        return True

    # ================================================================
    # 校验核心
    # ================================================================

    def validate(self, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """验证操作是否符合规则

        Args:
            action: 操作类型 (write_file, delete_file, execute_command, ...)
            params: 操作参数 (path, content, command, ...)

        Returns:
            {"allowed": bool, "violations": [...], "warnings": [...], "backup_required": bool}
        """
        params = params or {}
        self.stats["total_validations"] += 1

        result = {
            "allowed": True,
            "violations": [],
            "warnings": [],
            "backup_required": False,
            "action": action,
            "params_summary": {k: str(v)[:100] for k, v in params.items()},
        }

        # 按优先级排序
        sorted_rules = sorted(self.rules, key=lambda r: r.get("priority", 0), reverse=True)

        for rule in sorted_rules:
            # 检查是否匹配该操作
            if action not in rule.get("actions", []):
                continue

            # 检查模式匹配
            match = self._match_rule(rule, action, params)
            if not match:
                continue

            effect = rule.get("effect", "deny")
            reason = rule.get("reason", rule.get("description", "违规操作"))

            if effect == "deny":
                result["allowed"] = False
                result["violations"].append({
                    "rule_id": rule["id"],
                    "category": rule.get("category", ""),
                    "reason": reason,
                    "severity": "HIGH",
                })
                self.stats["denied"] += 1
                self.stats["violations"].append({
                    "rule_id": rule["id"],
                    "action": action,
                    "params": params,
                    "timestamp": datetime.now().isoformat(),
                })

            elif effect == "warn":
                result["warnings"].append({
                    "rule_id": rule["id"],
                    "category": rule.get("category", ""),
                    "reason": reason,
                    "severity": "MEDIUM",
                })
                self.stats["warned"] += 1

            elif effect == "require_backup":
                result["backup_required"] = True

        if result["allowed"]:
            self.stats["allowed"] += 1

        return result

    def _match_rule(self, rule: dict, action: str, params: dict) -> bool:
        """检查操作是否匹配规则"""
        patterns = rule.get("patterns", [])
        rid = rule.get("id", "?")

        # 无模式 → 检查 condition
        if not patterns:
            return self._check_condition(rule, params)

        # 获取目标路径/命令
        target = (
            params.get("path")
            or params.get("file_path")
            or params.get("command")
            or params.get("source", "")
        )
        if not target:
            return False

        # 1. 正则匹配
        if rid in self._compiled_patterns:
            for regex in self._compiled_patterns[rid]:
                if regex.search(target):
                    return self._check_condition(rule, params)

        # 2. Glob 匹配
        for pattern in patterns:
            if not any(c in pattern for c in ".*+?[](){}|^$\\"):
                if fnmatch(target, pattern):
                    return self._check_condition(rule, params)
                # 也检查 basename
                basename = os.path.basename(target)
                if fnmatch(basename, pattern):
                    return self._check_condition(rule, params)

        return False

    def _check_condition(self, rule: dict, params: dict) -> bool:
        """检查额外条件"""
        condition = rule.get("condition", "")
        if not condition:
            return True

        try:
            # 安全地评估简单条件
            if "content_size" in condition:
                content = str(params.get("content", ""))
                size = len(content)
                if ">" in condition:
                    threshold = int(condition.split(">")[1].strip())
                    return size > threshold
                elif "<" in condition:
                    threshold = int(condition.split("<")[1].strip())
                    return size < threshold
        except Exception:
            pass

        return True

    # ================================================================
    # 快捷方法
    # ================================================================

    def can_write(self, file_path: str, content: str = "") -> Dict[str, Any]:
        """检查是否可以写入文件"""
        return self.validate("write_file", {
            "path": file_path,
            "content": content,
        })

    def can_execute(self, command: str) -> Dict[str, Any]:
        """检查是否可以执行命令"""
        return self.validate("execute_command", {
            "command": command,
        })

    def can_delete(self, file_path: str) -> Dict[str, Any]:
        """检查是否可以删除文件"""
        return self.validate("delete_file", {
            "path": file_path,
        })

    # ================================================================
    # 规则管理
    # ================================================================

    def add_rule(self, rule: dict) -> bool:
        """动态添加规则"""
        if "id" not in rule or "effect" not in rule:
            return False
        # 去重
        self.rules = [r for r in self.rules if r.get("id") != rule["id"]]
        self.rules.append(rule)
        self._compile_patterns()
        return True

    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.get("id") != rule_id]
        if len(self.rules) < before:
            self._compile_patterns()
            return True
        return False

    def list_rules_by_category(self, category: str = None) -> List[dict]:
        """按分类列出规则"""
        if category:
            return [r for r in self.rules if r.get("category") == category]
        return self.rules

    def get_stats(self) -> dict:
        """获取统计"""
        return {
            **self.stats,
            "total_rules": len(self.rules),
            "categories": list(self.categories.keys()),
            "recent_violations": self.stats["violations"][-10:],
        }

    def save_rules(self):
        """保存当前规则到文件"""
        self.rules_config["rules"] = self.rules
        with open(self.rules_file, "w", encoding="utf-8") as f:
            yaml.dump(self.rules_config, f, allow_unicode=True, default_flow_style=False)

    # ================================================================
    # 集成钩子
    # ================================================================

    def as_skill_hook(self, skill_name: str, params: dict) -> Optional[Dict]:
        """作为 Skill 执行的前置钩子

        用法: registry.register_global_hook('before_skill_execute', rules_engine.as_skill_hook)
        """
        action = params.get("action", "")
        if action in ("write_file", "execute_command", "delete_file"):
            result = self.validate(action, params)
            if not result["allowed"]:
                return {
                    "blocked": True,
                    "violations": result["violations"],
                }
        return None  # 通过


# ============================================================
# 模块级便捷函数
# ============================================================

_rules_instance = None


def get_rules_engine() -> AIRulesEngine:
    """获取全局规则引擎"""
    global _rules_instance
    if _rules_instance is None:
        _rules_instance = AIRulesEngine()
    return _rules_instance
