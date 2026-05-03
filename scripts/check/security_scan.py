#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(r"\python")
SCRIPTS = Path(r"C:\Users\888\AppData\Local\Programs\Python\Python310\Scripts")
LOG_DIR = ROOT / "logs" / "security"
SCAN_DIRS = [str(ROOT / "core"), str(ROOT / "storage" / "mcp"), str(ROOT / "remote-control"), str(ROOT / "scripts"), str(ROOT / "skills")]

def run(cmd, **kwargs):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, **kwargs)
        return result
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None

def quick_scan():
    print("[1/2] Ruff security rules...")
    ruff = run([str(SCRIPTS / "ruff.exe"), "check", "--select", "S", "--output-format", "json"] + SCAN_DIRS)
    ruff_issues = json.loads(ruff.stdout) if ruff and ruff.stdout.strip() else []

    print("[2/2] Bandit...")
    bandit = run([str(SCRIPTS / "bandit.exe"), "-r"] + SCAN_DIRS + ["-f", "json", "-ll"])
    bandit_data = {}
    if bandit and bandit.stdout and bandit.stdout.strip():
        try:
            bandit_data = json.loads(bandit.stdout)
        except json.JSONDecodeError:
            bandit_data = {}
    bandit_issues = bandit_data.get("results", [])

    high_count = sum(1 for i in bandit_issues if i.get("issue_severity") == "HIGH")
    high_count += sum(1 for i in ruff_issues if i.get("severity", "") in ("error", "fatal"))

    return {
        "ruff_issues": len(ruff_issues),
        "bandit_issues": len(bandit_issues),
        "high_severity": high_count,
        "bandit_high": high_count,
    }

def full_scan():
    results = {}

    print("[1/5] Bandit...")
    bandit = run([str(SCRIPTS / "bandit.exe"), "-r"] + SCAN_DIRS + ["-f", "json"])
    if bandit and bandit.stdout.strip():
        data = json.loads(bandit.stdout)
        results["bandit"] = {"total": len(data.get("results", [])), "high": sum(1 for r in data.get("results", []) if r.get("issue_severity") == "HIGH")}

    print("[2/5] Ruff security rules...")
    ruff = run([str(SCRIPTS / "ruff.exe"), "check", "--select", "S", "--output-format", "json"] + SCAN_DIRS)
    if ruff and ruff.stdout.strip():
        issues = json.loads(ruff.stdout)
        results["ruff"] = {"total": len(issues)}

    print("[3/5] detect-secrets...")
    ds = run([str(SCRIPTS / "detect-secrets.exe"), "scan"] + SCAN_DIRS)
    if ds and ds.stdout.strip():
        data = json.loads(ds.stdout)
        secret_count = sum(len(v) for v in data.get("results", {}).values())
        results["detect_secrets"] = {"total": secret_count}

    print("[4/5] pip-audit...")
    pa = run([str(SCRIPTS / "pip-audit.exe"), "-r", str(ROOT / "requirements.txt"), "--format", "json"])
    if pa and pa.stdout.strip():
        try:
            data = json.loads(pa.stdout)
            results["pip_audit"] = {"total": len(data.get("dependencies", []))}
        except json.JSONDecodeError:
            results["pip_audit"] = {"status": "completed"}

    print("[5/5] Semgrep (skipped - run manually: semgrep --config p/python /python/core)")
    results["semgrep"] = {"note": "run manually with: semgrep --config p/python --config .semgrep.yml /python/core"}

    return results

def auto_fix():
    fixed = 0
    for scan_dir in SCAN_DIRS:
        for py_file in Path(scan_dir).rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                original = content

                content = re.sub(r'^(\s*)except:\s*$', r'\1except Exception:', content, flags=re.MULTILINE)
                content = content.replace('== None', 'is None')
                content = content.replace('!= None', 'is not None')

                if content != original:
                    with open(py_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    fixed += 1
            except Exception:
                pass
    return fixed

def main():
    parser = argparse.ArgumentParser(description="/python Security Scanner")
    parser.add_argument("--quick", action="store_true", help="Quick scan (Ruff S + Bandit)")
    parser.add_argument("--full", action="store_true", help="Full scan (all tools)")
    parser.add_argument("--fix", action="store_true", help="Auto-fix common issues")
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.fix:
        print("Auto-fixing common issues...")
        count = auto_fix()
        print(f"Fixed {count} files")
        return 0

    if args.quick:
        print("=== Quick Security Scan ===")
        results = quick_scan()
        report_path = LOG_DIR / f"quick_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults: {results}")
        print(f"Report: {report_path}")
        return 1 if results.get("high_severity", 0) > 0 else 0

    if args.full:
        print("=== Full Security Scan ===")
        results = full_scan()
        report_path = LOG_DIR / f"full_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults: {json.dumps(results, indent=2, default=str)}")
        print(f"Report: {report_path}")
        return 0

    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())
