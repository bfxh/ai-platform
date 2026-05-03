#!/usr/bin/env python
"""
GSTACK - GitHub Tools Stack
\python 核心工作流引擎入口

用法:
    python gstack_core.py review <file>    # 代码审查
    python gstack_core.py ship             # 自动部署
    python gstack_core.py skill_doctor     # 技能自检
    python gstack_core.py status           # 系统状态
"""

import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
ARCH_CONFIG = ROOT / "ai_architecture.json"

COMMAND_MAP = {
    "review": str(ROOT / "scripts" / "review.py"),
    "check": str(ROOT / "scripts" / "deep_check.py"),
    "fix": str(ROOT / "scripts" / "fix" / "system_optimize.py"),
    "pipeline": str(ROOT / "core" / "pipeline_engine.py"),
    "skill-doctor": str(ROOT / "user" / "global" / "plugin" / "mcp-core" / "skills" / "skill_doctor" / "skill_doctor.py"),
}

def load_config():
    if ARCH_CONFIG.exists():
        with open(ARCH_CONFIG, encoding="utf-8") as f:
            return json.load(f)
    return {}

def cmd_status():
    """显示系统状态"""
    config = load_config()
    gstack = config.get("gstack", {})
    mcp = config.get("mcp", {})
    skills = config.get("skills", {})

    print("=== GSTACK System Status ===")
    print(f"Version: {gstack.get('description', 'unknown')}")

    # MCP stats
    cats = mcp.get("categories", {})
    jm = cats.get("JM", {}).get("file_count", 0)
    bc = cats.get("BC", {}).get("file_count", 0)
    tools = cats.get("Tools", {}).get("file_count", 0)
    print(f"MCP: JM({jm}) BC({bc}) Tools({tools})")

    # Skills
    skills_list = skills.get("available_skills", [])
    print(f"Skills: {len(skills_list)} available")

    # Directories
    dirs = config.get("directories", {})
    for key in ["core", "adapter", "storage_mcp", "storage_cll"]:
        p = Path(dirs.get(key, ""))
        if p.exists():
            print(f"  {key}: OK ({p})")
        else:
            print(f"  {key}: MISSING")

    return 0

def cmd_help():
    print("GSTACK Commands:")
    print(f"  {'status':<25} Show system status")
    print(f"  {'review':<25} Code review (scripts/review.py)")
    print(f"  {'check':<25} Deep check (scripts/deep_check.py)")
    print(f"  {'fix':<25} System fix (scripts/fix/system_optimize.py)")
    print(f"  {'pipeline':<25} Pipeline engine (core/pipeline_engine.py)")
    print(f"  {'skill-doctor':<25} Skill doctor (skill_doctor.py)")
    print(f"  {'help':<25} Show this help")

def run_command(script_path, extra_args):
    p = Path(script_path)
    if not p.exists():
        print(f"Script not found: {script_path}")
        return 1
    cmd = [sys.executable, script_path] + extra_args
    result = subprocess.run(cmd)
    return result.returncode

def main():
    if len(sys.argv) < 2:
        cmd_help()
        return 0

    command = sys.argv[1]
    extra_args = sys.argv[2:]

    if command == "status":
        return cmd_status()
    elif command in ("-h", "--help", "help"):
        cmd_help()
        return 0
    elif command in COMMAND_MAP:
        return run_command(COMMAND_MAP[command], extra_args)
    else:
        print(f"Unknown command: {command}")
        cmd_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
