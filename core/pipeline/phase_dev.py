#!/usr/bin/env python
"""Phase 5: Development - 开发实施阶段

职责 (仅当前四个阶段全部通过后才可执行):
- 根据分析结果选择合适的实现策略
- 代码生成/修改 (依赖: Phase 1 的架构分析)
- 3D建模 (依赖: Phase 3 的资源类型分析)
- 测试执行 (依赖: Phase 2 的安全要求)
- 部署发布 (依赖: Phase 3 的许可证合规)
- 开发后验证
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent.parent  # \python\
sys.path.insert(0, str(ROOT / "core"))
from pipeline_engine import GateReport, GateStatus
from pipeline_engine import Phase as PipelinePhase


def dev_phase(project_path: Path, project_name: str, run_id: str, prev_reports: dict = None, **kwargs) -> GateReport:
    """执行开发阶段"""

    prev_reports = prev_reports or {}

    # 提取前置报告关键信息
    analysis = prev_reports.get("ANALYSIS", {})
    security = prev_reports.get("SECURITY", {})
    reverse = prev_reports.get("REVERSE", {})
    reanalysis = prev_reports.get("DEEP", {})

    # ─── 必要条件验证 ─────────────────────────────
    if not reanalysis or not reanalysis.get("details", {}).get("can_proceed_to_dev", True):
        return GateReport(
            phase=PipelinePhase.DEV,
            status=GateStatus.BLOCKED,
            summary="深度分析未通过，不能进入开发阶段",
            risk_level="high",
        )

    lic_type = reverse.get("details", {}).get("license_detected", "Unknown")
    if lic_type == "Proprietary":
        return GateReport(
            phase=PipelinePhase.DEV,
            status=GateStatus.BLOCKED,
            summary="专有软件 — 需要授权许可才能开发",
            risk_level="high",
        )

    # ─── 开发策略选择 ────────────────────────────
    main_lang = ""
    lang_dict = analysis.get("details", {}).get("languages_detected", {})
    if lang_dict:
        main_lang = max(lang_dict, key=lang_dict.get)

    frameworks = analysis.get("details", {}).get("frameworks_detected", [])
    arch_patterns = analysis.get("details", {}).get("architecture_patterns", [])
    entry_points = analysis.get("details", {}).get("entry_points", [])
    dep_count = 0
    for dep_list in analysis.get("details", {}).get("dependencies", {}).values():
        dep_count += len(dep_list)

    # ─── 开发准备检查 ────────────────────────────
    dev_plan = []
    risks = []

    # 语言策略
    lang_strategies = {
        "Python": {"tool": "pip + venv/poetry", "linter": "ruff", "test": "pytest"},
        "JavaScript": {"tool": "npm/yarn/pnpm", "linter": "eslint", "test": "jest/vitest"},
        "TypeScript": {"tool": "npm/yarn/pnpm", "linter": "eslint", "test": "jest/vitest"},
        "Java": {"tool": "maven/gradle", "linter": "checkstyle", "test": "junit"},
        "Go": {"tool": "go modules", "linter": "golangci-lint", "test": "go test"},
        "Rust": {"tool": "cargo", "linter": "clippy", "test": "cargo test"},
    }

    strategy = lang_strategies.get(main_lang, {"tool": "custom", "linter": "generic", "test": "custom"})
    dev_plan.append(
        {
            "step": "环境准备",
            "action": f"配置 {main_lang} 开发环境: {strategy['tool']}",
        }
    )

    # 框架策略
    if frameworks:
        dev_plan.append(
            {
                "step": "框架配置",
                "action": f"使用框架: {', '.join(frameworks[:3])}",
            }
        )

    # 架构策略
    if "Layered Architecture" in arch_patterns:
        dev_plan.append(
            {
                "step": "分层开发",
                "action": "按 user → core → adapter → storage 分层实施",
            }
        )
    elif "Plugin Architecture" in arch_patterns:
        dev_plan.append(
            {
                "step": "插件开发",
                "action": "遵循插件架构规范，接口一致性验证",
            }
        )

    # 安全要求
    sec_risk = security.get("risk_level", "low")
    if sec_risk in ("high",):
        dev_plan.append(
            {
                "step": "安全加固",
                "action": "修复所有 HIGH 级别安全问题后方可提交",
            }
        )
        risks.append("遗留安全问题未解决，代码审查需额外注意")

    # 许可证合规
    if lic_type in ("GPL-2.0", "GPL-3.0"):
        dev_plan.append(
            {
                "step": "许可证合规",
                "action": "确认: 修改后分发需以 GPL 发布，内部使用无限制",
            }
        )
    elif lic_type == "MIT":
        dev_plan.append(
            {
                "step": "许可证合规",
                "action": "MIT — 保留原作者版权声明即可",
            }
        )

    # Linting
    dev_plan.append(
        {
            "step": "代码质量控制",
            "action": f"启用 {strategy['linter']} 进行代码检查",
        }
    )

    # Testing
    dev_plan.append(
        {
            "step": "测试策略",
            "action": f"使用 {strategy['test']} 进行测试",
        }
    )

    # Dependencies
    if dep_count > 100:
        dev_plan.append(
            {
                "step": "依赖管理",
                "action": f"项目有 {dep_count} 个依赖，建议审计和锁定版本",
            }
        )

    # ─── 入口点建议 ─────────────────────────────
    if entry_points:
        dev_plan.append(
            {
                "step": "开发起点",
                "action": f"建议从以下入口开始: {entry_points[0]}",
            }
        )

    # ─── 完成后验证 ─────────────────────────────
    dev_plan.append(
        {
            "step": "开发后验证",
            "action": "运行测试套件 → 安全检查 → 许可证合规确认 → 生成报告",
        }
    )

    # ─── 综合评估 ───────────────────────────────
    if risks:
        status = GateStatus.WARNING
        summary = f"开发准备就绪 ({len(risks)} 个风险项需要注意)"
    else:
        status = GateStatus.PASSED
        summary = "开发准备就绪 — 所有前置条件满足"

    details = {
        "development_strategy": {
            "primary_language": main_lang,
            "recommended_toolchain": strategy,
            "frameworks_in_use": frameworks,
            "architecture": arch_patterns,
        },
        "development_plan": dev_plan,
        "key_entry_points": entry_points[:5],
        "dependency_count": dep_count,
        "license_compliance": {
            "type": lic_type,
            "development_allowed": True,
            "required_actions": [
                "保留版权声明" if lic_type in ("MIT", "Apache-2.0", "BSD") else "",
                "确认不分发GPL修改" if lic_type in ("GPL-2.0", "GPL-3.0") else "",
            ],
        },
        "risks_reported": risks,
        "estimated_setup_time": "5-15分钟" if dep_count < 50 else "15-30分钟",
        "generated_at": datetime.now().isoformat(),
    }

    return GateReport(
        phase=PipelinePhase.DEV,
        status=status,
        summary=summary,
        details=details,
        risk_level="low" if not risks else "medium",
    )


if __name__ == "__main__":
    prev = {
        "ANALYSIS": {
            "details": {
                "languages_detected": {"Python": 200},
                "frameworks_detected": ["Flask", "GSTACK"],
                "architecture_patterns": ["Layered Architecture", "Plugin Architecture"],
                "entry_points": ["core/dispatcher.py"],
                "dependencies": {"python_requirements": ["pytest", "requests", "flask"] * 20},
            }
        },
        "SECURITY": {"risk_level": "medium"},
        "REVERSE": {"details": {"license_detected": "MIT"}},
        "DEEP": {"details": {"can_proceed_to_dev": True}},
    }
    report = dev_phase(Path("/python"), "AI-Platform", "test_run", prev_reports=prev)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
