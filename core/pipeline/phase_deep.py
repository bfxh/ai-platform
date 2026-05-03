#!/usr/bin/env python
"""Phase 4: Deep Analysis - 深度/二次分析阶段

职责:
- 交叉分析 Phase 1+2+3 的所有发现
- 风险重评估 (结合安全和许可证信息)
- 可行性分析
- 技术债务识别
- 改进建议生成
- 决策树 (是否可以安全开发)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent.parent  # \python\
sys.path.insert(0, str(ROOT / "core"))
from pipeline_engine import GateReport, GateStatus
from pipeline_engine import Phase as PipelinePhase


def deep_analyze_phase(
    project_path: Path, project_name: str, run_id: str, prev_reports: dict = None, **kwargs
) -> GateReport:
    """执行深度/二次分析"""

    prev_reports = prev_reports or {}

    # 提取前序报告关键信息
    analysis = prev_reports.get("ANALYSIS", {})
    security = prev_reports.get("SECURITY", {})
    reverse = prev_reports.get("REVERSE", {})

    findings = []
    risk_level = "low"
    can_proceed = True
    blockers = []
    warnings = []
    recommendations = []

    # ─── 1. 交叉分析：语言 vs 安全 ──────────────────
    main_lang = ""
    lang_dict = analysis.get("details", {}).get("languages_detected", {})
    if lang_dict:
        main_lang = max(lang_dict, key=lang_dict.get)

    sec_risk = security.get("risk_level", "low")
    lic_type = reverse.get("details", {}).get("license_detected", "Unknown")

    # 语言特定风险评估
    lang_risk_map = {
        "JavaScript": "JS 项目常见: 依赖膨胀、原型链污染风险",
        "TypeScript": "TS 相对安全，但仍需检查 npm 依赖",
        "Python": "Python 项目常见: pickle 反序列化、路径注入",
        "Java": "Java 项目常见: 反序列化漏洞、XML 注入",
        "Go": "Go 项目相对安全，注意依赖和并发问题",
        "Rust": "Rust 内存安全好，注意 unsafe 块",
    }

    if main_lang in lang_risk_map:
        findings.append({"type": "lang_risk", "note": lang_risk_map[main_lang]})

    # ─── 2. 安全风险深度评估 ──────────────────────
    sec_details = security.get("details", {})
    critical_count = sec_details.get("critical_count", 0)
    high_count = sec_details.get("high_count", 0)

    if sec_risk == "critical":
        blockers.append(f"发现 {critical_count} 个 CRITICAL 级别安全问题")
        can_proceed = False
        risk_level = "critical"
    elif sec_risk == "high":
        warnings.append(f"发现 {high_count} 个 HIGH 级别安全问题")
        risk_level = "high"

    # ─── 3. 许可证风险深度评估 ────────────────────
    if lic_type == "Proprietary":
        blockers.append("项目为专有软件，需授权才能开发")
        can_proceed = False
        risk_level = "high"
    elif lic_type in ("GPL-2.0", "GPL-3.0"):
        warnings.append(f"GPL 许可证 — 修改后分发需开源，内部使用无限制")
        findings.append({"type": "license_note", "note": "GPL 传染性：衍生作品需以 GPL 发布"})
    elif lic_type == "Unknown" and reverse.get("details", {}).get("binaries_count", 0) > 0:
        warnings.append("许可证未知且存在二进制文件，建议先确认来源")
        risk_level = "medium"

    # ─── 4. 架构可行性分析 ─────────────────────
    arch = analysis.get("details", {}).get("architecture_patterns", [])
    entry_count = len(analysis.get("details", {}).get("entry_points", []))
    total_files = analysis.get("details", {}).get("total_files", 0)

    if total_files == 0:
        blockers.append("未检测到任何代码文件")
        can_proceed = False
    elif total_files < 5:
        warnings.append("项目文件极少，可能是空项目或配置项目")
    elif total_files > 10000:
        recommendations.append("大型项目，建议分批处理")

    if not arch:
        warnings.append("无法识别架构模式")

    # ─── 5. 依赖健康度 ───────────────────────────
    dep_count = 0
    for dep_list in analysis.get("details", {}).get("dependencies", {}).values():
        dep_count += len(dep_list)
    if dep_count > 200:
        warnings.append(f"依赖数量较多 ({dep_count} 个)，定期审计必要")

    # ─── 6. 二进制风险评估 ─────────────────────
    bin_count = reverse.get("details", {}).get("binaries_count", 0)
    bin_size = reverse.get("details", {}).get("total_binary_size_mb", 0)
    if bin_count > 100:
        recommendations.append("大量二进制文件，建议评估是否为第三方库集合")
    if bin_size > 500:
        warnings.append(f"二进制文件总体积 {bin_size:.0f}MB，较大")

    # ─── 7. 改进建议 ────────────────────────────
    if sec_risk in ("high", "critical"):
        recommendations.append("优先修复安全问题后再开发")
    if lic_type == "Unknown" and bin_count > 0:
        recommendations.append("建议执行反编译分析确认代码来源和许可证")
    if not lic_type or lic_type == "Unknown":
        recommendations.append("建议添加明确的 LICENSE 文件")

    # 通用建议
    recommendations.extend(
        [
            "确保有完整的测试覆盖",
            "建立 CI/CD 流水线自动化验证",
            "使用依赖扫描工具持续监控",
        ]
    )

    # ─── 8. 判定结果 ─────────────────────────────
    if not can_proceed:
        status = GateStatus.BLOCKED
    elif warnings:
        status = GateStatus.WARNING if risk_level == "high" else GateStatus.PASSED
    else:
        status = GateStatus.PASSED

    details = {
        "cross_analysis": {
            "main_language": main_lang,
            "language_risk_notes": [f["note"] for f in findings if f["type"] == "lang_risk"],
            "combined_risk": risk_level,
        },
        "security_reassessment": {
            "original_risk": sec_risk,
            "reassessed_risk": risk_level,
            "critical_blockers": critical_count,
            "high_warnings": high_count,
        },
        "license_reassessment": {
            "license_type": lic_type,
            "development_allowed": lic_type != "Proprietary",
            "requires_attribution": lic_type in ("MIT", "Apache-2.0", "BSD"),
        },
        "architecture_feasibility": {
            "patterns": arch,
            "total_files": total_files,
            "entry_points": entry_count,
            "estimated_complexity": "high" if total_files > 1000 else "medium" if total_files > 100 else "low",
        },
        "dependency_health": {
            "total_dependencies": dep_count,
            "needs_audit": dep_count > 100,
        },
        "blockers": blockers,
        "warnings": warnings,
        "recommendations": recommendations,
        "can_proceed_to_dev": can_proceed,
        "analysis_timestamp": datetime.now().isoformat(),
    }

    summary_parts = []
    if blockers:
        summary_parts.append(f"阻塞: {', '.join(blockers[:2])}")
    if warnings:
        summary_parts.append(f"警告: {len(warnings)} 项")
    if not blockers:
        summary_parts.append("可以进入开发阶段")

    return GateReport(
        phase=PipelinePhase.DEEP,
        status=status,
        summary=" | ".join(summary_parts),
        details=details,
        risk_level=risk_level,
    )


if __name__ == "__main__":
    # 模拟前序报告
    prev = {
        "ANALYSIS": {
            "details": {
                "languages_detected": {"Python": 200, "JavaScript": 50},
                "architecture_patterns": ["Layered Architecture"],
                "entry_points": ["core/dispatcher.py"],
                "dependencies": {"python_requirements": ["pytest", "requests", "flask", "numpy", "pandas"]},
                "total_files": 500,
            }
        },
        "SECURITY": {"risk_level": "medium", "details": {"critical_count": 0, "high_count": 2}},
        "REVERSE": {"details": {"license_detected": "MIT", "binaries_count": 5, "total_binary_size_mb": 50}},
    }
    report = deep_analyze_phase(Path("/python"), "AI-Platform", "test_run", prev_reports=prev)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
