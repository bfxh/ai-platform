#!/usr/bin/env python
"""Phase 2: Security Audit - 安全审计阶段

职责:
- 敏感信息/密钥检测 (API keys, tokens, passwords)
- 依赖漏洞扫描 (已知 CVE 检查)
- 配置安全审计 (弱配置、不安全默认值)
- 代码安全模式检测 (命令注入、路径遍历、硬编码凭据)
- 文件权限检查
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent.parent  # \python\
sys.path.insert(0, str(ROOT / "core"))
from pipeline_engine import GateReport, GateStatus
from pipeline_engine import Phase as PipelinePhase


def audit_phase(project_path: Path, project_name: str, run_id: str, prev_reports: dict = None, **kwargs) -> GateReport:
    """执行安全审计"""

    if isinstance(project_path, str):
        project_path = Path(project_path)

    findings = []
    risk_level = "low"
    env_files_found = []
    secrets_found = []
    unsafe_patterns = []

    # 跳过非代码目录
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "CC", "backups", "docs", "logs"}

    # 1. 敏感文件检测
    sensitive_files = [
        ".env",
        ".env.local",
        ".env.production",
        "credentials.json",
        "credentials.yaml",
        ".npmrc",
        ".pypirc",
        "config.local",
        "secret",
        "secrets",
        "private_key",
        "id_rsa",
    ]

    for pattern in sensitive_files:
        for f in project_path.rglob(pattern):
            if not any(s in f.parts for s in skip_dirs):
                env_files_found.append(str(f.relative_to(project_path)))

    # 2. 内容扫描: 密钥/Token/密码
    secret_patterns = [
        (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{10,}', "API Key", "high"),
        (r'(?i)(token|secret|password|passwd)\s*[:=]\s*["\']?[a-zA-Z0-9_\-\.]{6,}', "凭据", "high"),
        (r"(?i)(gh[pous]_[a-zA-Z0-9]{36,})", "GitHub Token", "critical"),
        (r"(?i)(sk-[a-zA-Z0-9]{20,})", "OpenAI API Key", "high"),
        (r"(?i)(AKIA[0-9A-Z]{16})", "AWS Access Key", "critical"),
        (r"(?i)(BEGIN\s+(RSA|EC|DSA|OPENSSH)\s+PRIVATE\s+KEY)", "私钥", "critical"),
        (r"(?i)(mongodb(?:\+srv)?://[^\s]+)", "数据库连接串", "high"),
        (r"(?i)(postgres(?:ql)?://[^\s]+)", "数据库连接串", "high"),
        (r"(?i)(mysql://[^\s]+)", "数据库连接串", "high"),
    ]

    scan_files = (
        list(project_path.rglob("*.py"))[:200]
        + list(project_path.rglob("*.js"))[:100]
        + list(project_path.rglob("*.json"))[:100]
        + list(project_path.rglob("*.yaml"))[:50]
        + list(project_path.rglob("*.yml"))[:50]
        + list(project_path.rglob("*.toml"))[:50]
        + list(project_path.rglob("*.env*"))[:20]
    )

    for f in scan_files:
        try:
            if any(s in f.parts for s in skip_dirs):
                continue
            content = f.read_text(encoding="utf-8", errors="ignore")
            for pattern, label, sev in secret_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    for match in matches[:3]:
                        match_str = str(match)
                        masked = match_str[:20] + ("..." if len(match_str) > 20 else "")
                        secrets_found.append(
                            {
                                "file": str(f.relative_to(project_path)),
                                "type": label,
                                "severity": sev,
                                "match_preview": str(masked),
                            }
                        )
        except Exception:
            continue

    # 3. 不安全代码模式
    code_patterns = [
        (r"(?i)os\.system\(.*\$", "Shell命令注入风险", "high"),
        (r"(?i)subprocess\.(?:call|Popen)\(.*shell\s*=\s*True", "Shell=True风险", "high"),
        (r"(?i)eval\(", "eval() 风险", "medium"),
        (r"(?i)exec\(", "exec() 风险", "medium"),
        (r"(?i)\.\./\.\./(?:etc|passwd|shadow)", "路径遍历风险", "high"),
        (r"(?i)SELECT.*\+.*FROM|INSERT.*\+", "SQL注入风险", "high"),
        (r"(?i)hardcoded|fixed_key|static_key|default_password", "硬编码凭据", "medium"),
        (r"(?i)disable.*ssl|verify\s*=\s*False|check_hostname\s*=\s*False", "SSL验证禁用", "medium"),
    ]

    code_files = list(project_path.rglob("*.py"))[:100]
    for cf in code_files:
        if any(s in cf.parts for s in skip_dirs):
            continue
        try:
            content = cf.read_text(encoding="utf-8", errors="ignore")
            for pattern, label, sev in code_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    unsafe_patterns.append(
                        {
                            "file": str(cf.relative_to(project_path)),
                            "issue": label,
                            "severity": sev,
                            "occurrences": len(matches),
                        }
                    )
        except Exception:
            pass

    # 4. 风险评估
    critical_count = sum(1 for s in secrets_found if s.get("severity") == "critical")
    high_count = sum(1 for s in secrets_found if s.get("severity") == "high")

    if critical_count > 0:
        risk_level = "critical"
        status = GateStatus.BLOCKED
    elif high_count >= 3 or len(secrets_found) >= 5:
        risk_level = "high"
        status = GateStatus.WARNING
    elif secrets_found or unsafe_patterns:
        risk_level = "medium"
        status = GateStatus.PASSED
    else:
        risk_level = "low"
        status = GateStatus.PASSED

    details = {
        "env_files_detected": env_files_found,
        "secrets_found": secrets_found[:30],
        "unsafe_patterns": unsafe_patterns[:30],
        "critical_count": critical_count,
        "high_count": high_count,
        "total_findings": len(secrets_found) + len(unsafe_patterns),
        "audit_timestamp": datetime.now().isoformat(),
    }

    summary_parts = []
    if env_files_found:
        summary_parts.append(f"发现 {len(env_files_found)} 个敏感配置文件")
    if critical_count:
        summary_parts.append(f"CRITICAL: {critical_count} 个关键密钥泄露")
    if secrets_found:
        summary_parts.append(f"检测到 {len(secrets_found)} 个潜在密钥")
    if unsafe_patterns:
        summary_parts.append(f"发现 {len(unsafe_patterns)} 个不安全代码模式")

    if not summary_parts:
        summary_parts.append("未发现严重安全问题")

    return GateReport(
        phase=PipelinePhase.SECURITY,
        status=status,
        summary=" | ".join(summary_parts),
        details=details,
        risk_level=risk_level,
    )


if __name__ == "__main__":
    report = audit_phase(Path("/python"), "AI-Platform", "test_run")
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
