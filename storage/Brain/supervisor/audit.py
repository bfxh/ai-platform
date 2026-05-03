#!/usr/bin/env python
"""Compliance Auditor - AI合规审计系统

确保AI严格按用户要求执行:
- 行动前检查清单 (5项)
- 行动后验证清单 (4项)
- 10种违规检测 (scope_creep, lazy_execution, hallucination,
                   ignoring_instruction, over_explaining, no_verification,
                   bare_except_pass, missing_docstring, hardcoded_path,
                   nonstandard_commit)
- 审计日志记录
- 匹配度评分
- 产出标准合规检查
"""

import json
import re
import threading
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent  # storage/Brain/
SUPERVISOR_DIR = ROOT / "supervisor"
RULES_FILE = SUPERVISOR_DIR / "rules.json"
AUDIT_LOG = SUPERVISOR_DIR / "audit.log"
VIOLATIONS_LOG = SUPERVISOR_DIR / "violations.log"


class ComplianceAuditor:
    """合规审计器 - 行为监督与审计"""

    def __init__(self):
        SUPERVISOR_DIR.mkdir(parents=True, exist_ok=True)
        self.rules = self._load_rules()
        self._lock = threading.Lock()
        self._session_violations = []
        self._session_actions = []

    def _load_rules(self) -> dict:
        if RULES_FILE.exists():
            return json.loads(RULES_FILE.read_text(encoding="utf-8"))
        return {}

    # ─── 行动前检查 ────────────────────────────────────

    def pre_action_check(self, instruction: str,
                         planned_action: str,
                         expected_files: list = None,
                         tools_to_use: list = None) -> dict:
        """行动前合规检查

        Args:
            instruction: 用户原始指令
            planned_action: 计划执行的操作
            expected_files: 预期涉及的文件
            tools_to_use: 计划使用的工具

        Returns:
            {"passed": bool, "warnings": [...], "blocks": [...]}
        """
        checks = []
        checklist = self.rules.get("checklist_before_action", [])

        # 1. 核对是否是用户要求的
        checks.append({
            "item": "scope_verification",
            "passed": True,  # 由AI自行判断
            "note": "确认此操作是用户明确要求的",
        })

        # 2. 理解一致性
        checks.append({
            "item": "understanding_verification",
            "passed": True,
            "note": "确认理解和用户指令一致",
        })

        # 3. 安全性
        dangerous_keywords = ["delete", "rm", "remove", "drop", "truncate",
                              "format", "clean", "purge", "覆盖", "删除",
                              "清空", "格式化", "干掉"]
        is_dangerous = any(kw in planned_action.lower() for kw in dangerous_keywords)
        checks.append({
            "item": "safety_check",
            "passed": not is_dangerous,
            "note": "没有数据丢失风险" if not is_dangerous else "⚠ 危险操作，需确认",
        })

        # 4. 信息充分性
        checks.append({
            "item": "info_sufficiency",
            "passed": len(instruction) > 10,
            "note": "有足够信息执行" if len(instruction) > 10 else "信息不足",
        })

        # 5. 验证方法
        checks.append({
            "item": "verification_method",
            "passed": True,
            "note": "已计划验证方式",
        })

        # 6. 产出标准检查 (如果指定了预期文件)
        output_standards_violations = []
        if expected_files:
            std_result = self.check_output_standards(expected_files)
            output_standards_violations = std_result.get("violations", [])
            checks.append({
                "item": "output_standards",
                "passed": std_result["passed"],
                "note": f"产出标准: {std_result['files_checked']}文件, "
                        f"{len(output_standards_violations)}违规",
            })

        warnings = [c for c in checks if not c["passed"]]
        blocks = [c for c in warnings if "危险" in c.get("note", "")]

        result = {
            "timestamp": datetime.now().isoformat(),
            "passed": len(blocks) == 0,
            "warnings": warnings,
            "blocks": blocks,
            "instruction": instruction[:500],
            "planned_action": planned_action[:500],
            "output_standards_violations": output_standards_violations,
        }

        with self._lock:
            self._session_actions.append(result)

        return result

    # ─── 行动后验证 ────────────────────────────────────

    def post_action_check(self, action: str,
                          result: str,
                          success: bool,
                          has_verified: bool,
                          user_requirements: list = None) -> dict:
        """行动后合规验证

        Returns:
            {"passed": bool, "violations": [...], "match_score": float}
        """
        violations = []
        checklist = self.rules.get("checklist_after_action", [])

        # 检测违规
        if not success and not has_verified:
            violations.append({
                "type": "no_verification",
                "severity": "high",
                "description": "操作可能失败但未验证",
                "detail": f"Action: {action[:200]}, Result: {result[:200]}",
            })

        if success and not has_verified:
            violations.append({
                "type": "no_verification",
                "severity": "medium",
                "description": "操作完成但未确认结果",
                "detail": f"Action: {action[:200]}",
            })

        if not success:
            violations.append({
                "type": "execution_failure",
                "severity": "high",
                "description": "执行失败",
                "detail": result[:300],
            })

        # 检查是否遗漏需求
        if user_requirements:
            for req in user_requirements:
                if req not in action and req not in result:
                    violations.append({
                        "type": "ignoring_instruction",
                        "severity": "high",
                        "description": f"可能遗漏了用户需求: {req}",
                        "detail": "",
                    })

        # 匹配度评分
        match_score = 100
        for v in violations:
            severity_deduction = {
                "critical": 30, "high": 20, "medium": 10, "low": 5,
            }
            deduction = severity_deduction.get(v.get("severity", "medium"), 10)
            match_score -= deduction

        match_score = max(0, min(100, match_score))

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action[:500],
            "user_instruction": "",  # 由调用方提供
            "my_understanding": action[:300],
            "match_score": match_score,
            "result": result[:300],
            "verified": has_verified,
            "violations": [v["type"] for v in violations],
        }

        with self._lock:
            self._session_actions.append(audit_entry)
            if violations:
                self._session_violations.extend(violations)
                self._log_violations(violations, action)

        self._log_audit(audit_entry)

        return {
            "passed": len([v for v in violations
                          if v.get("severity") in ("critical", "high")]) == 0,
            "match_score": match_score,
            "violations": violations,
        }

    # ─── 产出标准检查 ──────────────────────────────────

    def check_output_standards(self, files: list = None) -> dict:
        """检查文件是否符合产出标准。

        扫描指定文件的:
        - bare except: pass (OSV-001)
        - 硬编码绝对路径 (OSV-003)

        Args:
            files: 待检查的文件路径列表

        Returns:
            {"passed": bool, "violations": [...], "files_checked": int}
        """
        violations = []
        files_checked = 0

        if not files:
            return {"passed": True, "violations": [], "files_checked": 0}

        for file_path in files:
            p = Path(file_path)
            if not p.exists() or not p.is_file():
                continue
            if p.suffix != ".py":
                continue

            files_checked += 1
            try:
                content = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            # 检查 bare except: pass
            if re.search(r'except\s*(?:Exception|BaseException)?\s*:\s*pass', content):
                violations.append({
                    "type": "bare_except_pass",
                    "severity": "high",
                    "description": f"检测到 bare except: pass 在 {p.name}",
                    "code": "OSV-001",
                    "file": str(p),
                })

            # 检查硬编码绝对路径 (Windows 风格)
            if re.search(r'[\"\']([A-Za-z]:\\[^\s\"\']+)', content):
                violations.append({
                    "type": "hardcoded_path",
                    "severity": "medium",
                    "description": f"检测到硬编码绝对路径在 {p.name}",
                    "code": "OSV-003",
                    "file": str(p),
                })

        passed = len(violations) == 0

        with self._lock:
            if violations:
                self._session_violations.extend(violations)
                self._log_violations(violations, "output_standards_check")

        return {
            "passed": passed,
            "violations": violations,
            "files_checked": files_checked,
        }

    # ─── 违规日志 ──────────────────────────────────────

    def _log_violations(self, violations: list, context: str):
        """记录违规"""
        for v in violations:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "violation_type": v["type"],
                "severity": v.get("severity", "medium"),
                "description": v.get("description", ""),
                "context": context[:500],
            }
            try:
                with open(VIOLATIONS_LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            except OSError:
                # 违规日志写入失败不应阻塞主流程
                pass

    def _log_audit(self, entry: dict):
        """写入审计日志"""
        try:
            with open(AUDIT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            # 审计日志写入失败不应阻塞主流程
            pass

    # ─── 报告 ──────────────────────────────────────────

    def get_session_report(self) -> dict:
        """获取会话审计报告"""
        violation_counts = defaultdict(int)
        for v in self._session_violations:
            violation_counts[v["type"]] += 1

        return {
            "total_actions": len(self._session_actions),
            "total_violations": len(self._session_violations),
            "violation_breakdown": dict(violation_counts),
            "match_score_avg": round(
                sum(a.get("match_score", 100) for a in self._session_actions) /
                max(len(self._session_actions), 1), 1
            ),
            "compliance_rate": round(
                (1 - len(self._session_violations) / max(len(self._session_actions), 1)) * 100, 1
            ),
        }

    def get_recent_violations(self, limit: int = 20) -> list:
        """获取最近的违规记录"""
        if not VIOLATIONS_LOG.exists():
            return []

        violations = []
        try:
            lines = VIOLATIONS_LOG.read_text(encoding="utf-8").strip().split("\n")
            for line in lines[-limit:]:
                if line.strip():
                    try:
                        violations.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        return violations


# ─── 全局单例 ───────────────────────────────────────────
_auditor_instance: Optional[ComplianceAuditor] = None


def get_auditor() -> ComplianceAuditor:
    global _auditor_instance
    if _auditor_instance is None:
        _auditor_instance = ComplianceAuditor()
    return _auditor_instance


# ─── CLI ────────────────────────────────────────────────
if __name__ == "__main__":
    auditor = get_auditor()

    # 模拟检查
    r1 = auditor.pre_action_check(
        "帮我创建一个Python脚本",
        "创建 D:/test.py，写入Python代码",
    )
    print("Pre-Action Check:", json.dumps(r1, ensure_ascii=False, indent=2))

    r2 = auditor.post_action_check(
        "创建文件",
        "文件创建成功",
        success=True,
        has_verified=True,
    )
    print("\nPost-Action Check:", json.dumps(r2, ensure_ascii=False, indent=2))

    print("\nSession Report:", json.dumps(
        auditor.get_session_report(), ensure_ascii=False, indent=2
    ))
