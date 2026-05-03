#!/usr/bin/env python3
"""Bug 记录工具"""

from datetime import datetime
from pathlib import Path


def record_bug(
    project_dir: str,
    title: str,
    status: str = "open",
    log_summary: str = "",
    steps: list = None,
) -> str:
    project = Path(project_dir)
    bugs_file = project / "BUGS.md"

    if not bugs_file.exists():
        bugs_file.write_text("# Bug 记录\n", encoding="utf-8")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## [{timestamp}] {title}\n- 状态：{status}\n"
    if log_summary:
        entry += f"- 日志摘要：{log_summary}\n"
    if steps:
        entry += "- 复现步骤：\n"
        for i, step in enumerate(steps, 1):
            entry += f"  {i}. {step}\n"

    with open(bugs_file, "a", encoding="utf-8") as f:
        f.write(entry)

    return timestamp


def record_bug_from_test(
    project_dir: str,
    test_name: str,
    error_msg: str,
    steps: list = None,
) -> str:
    title = f"[{test_name}] {error_msg}"
    return record_bug(
        project_dir=project_dir,
        title=title,
        status="open",
        log_summary=error_msg,
        steps=steps,
    )


def record_bug_manual(
    project_dir: str,
    title: str,
    steps: list = None,
) -> str:
    return record_bug(
        project_dir=project_dir,
        title=title,
        status="open",
        steps=steps,
    )
