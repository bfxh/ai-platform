#!/usr/bin/env python3
"""
/python 系统维护脚本
功能: 清理临时文件、验证MCP状份配置、查依赖监hosts
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

PYTHON = "{USERPROFILE}/miniconda3/python.exe"
AI_PATH = Path(os.environ.get("AI_BASE_DIR", Path(__file__).resolve().parent.parent))
LOGS_PATH = AI_PATH / "logs"
CONFIG_PATH = AI_PATH / "Config"
BACKUP_PATH = Path("F:/储存/AI备份")
HOSTS_PATH = Path("C:/Windows/System32/drivers/etc/hosts")
MCP_CONFIG = AI_PATH / "storage/mcp/mcp-config.json"
REGISTRY = AI_PATH / "resource_registry.json"

BLOCKED_DOMAINS = [
    "github.com",
    "api.github.com",
    "github.dev",
    "github.githubassets.com",
    "raw.githubusercontent.com",
    "avatars.githubusercontent.com",
    "user-images.githubusercontent.com",
    "objects.githubusercontent.com",
    "pages.github.com",
    "gist.github.com",
    "githubapp.com",
    "github.io",
    "huggingface.co",
]

LOG_FILE = LOGS_PATH / f"maintenance_{datetime.now().strftime('%Y%m%d')}.log"


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOGS_PATH.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def clean_temp_files():
    log("=== 清理临时文件 ===")
    count = 0

    for pycache in AI_PATH.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache)
            log(f"  DEL: {pycache}")
            count += 1
        except Exception as e:
            log(f"  FAIL: {pycache} - {e}", "WARN")

    for pytest_cache in AI_PATH.rglob(".pytest_cache"):
        try:
            shutil.rmtree(pytest_cache)
            log(f"  DEL: {pytest_cache}")
            count += 1
        except Exception as e:
            log(f"  FAIL: {pytest_cache} - {e}", "WARN")

    old_logs = list(LOGS_PATH.glob("*.log")) if LOGS_PATH.exists() else []
    for log_file in old_logs:
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if datetime.now() - mtime > timedelta(days=30):
                log_file.unlink()
                log(f"  DEL old log: {log_file}")
                count += 1
        except:
            pass

    log(f"清理 {count} ")
    return count


def backup_configs():
    log("=== 备份配置文件 ===")
    count = 0
    backup_dir = BACKUP_PATH / "config_backups" / datetime.now().strftime("%Y%m%d")
    backup_dir.mkdir(parents=True, exist_ok=True)

    config_files = [
        REGISTRY,
        MCP_CONFIG,
        AI_PATH / "ai_architecture.json",
        AI_PATH / ".mcp" / "config.json",
        AI_PATH / "user" / "config" / "config.json",
    ]

    for cf in config_files:
        if cf.exists():
            try:
                dest = backup_dir / cf.name
                shutil.copy2(str(cf), str(dest))
                log(f"  BACKUP: {cf.name}")
                count += 1
            except Exception as e:
                log(f"  FAIL: {cf} - {e}", "WARN")

    log(f"备份 {count} 配置文件 {backup_dir}")
    return count


def validate_mcp():
    log("=== 验证 MCP 状 ===")
    if not MCP_CONFIG.exists():
        log("mcp-config.json 不存!", "ERROR")
        return 0

    try:
        with open(MCP_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        log(f"mcp-config.json 解析失败: {e}", "ERROR")
        return 0

    servers = config.get("mcpServers", {})
    total = len(servers)
    valid = 0
    invalid = []

    for name, server in servers.items():
        path = server.get("path", "")
        if path and path.endswith(".py"):
            if os.path.exists(path):
                valid += 1
            else:
                invalid.append(f"{name}: {path}")

    log(f"MCP 服务: {total} 总, {valid} 有效")
    if invalid:
        for inv in invalid[:10]:
            log(f"  [WARN] 无效: {inv}", "WARN")

    return valid


def check_hosts():
    log("===  hosts 文件 ===")
    if not HOSTS_PATH.exists():
        log("hosts 文件不存", "WARN")
        return True

    try:
        content = HOSTS_PATH.read_text(encoding="utf-8")
    except PermissionError:
        log("无法读取 hosts 文件", "WARN")
        return True

    blocked = []
    for domain in BLOCKED_DOMAINS:
        pattern = f"127.0.0.1 {domain}"
        if pattern in content or f"127.0.0.1\t{domain}" in content:
            blocked.append(domain)

    if blocked:
        log(f"[ALERT] hosts 文件 {len(blocked)}  GitHub 域名封锁!", "ERROR")
        for d in blocked:
            log(f"  BLOCKED: {d}", "ERROR")
        log("运 fix_hosts : python /python\\core\\maintenance.py --fix-hosts")
        return False
    else:
        log("hosts 文件正常，GitHub 域名封锁")
        return True


def fix_hosts():
    log("===  hosts 文件 ===")
    if not HOSTS_PATH.exists():
        log("hosts 文件不存", "WARN")
        return False

    try:
        content = HOSTS_PATH.read_text(encoding="utf-8")
    except PermissionError:
        log("要理员权!", "ERROR")
        return False

    backup_path = HOSTS_PATH.parent / f"hosts.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(str(HOSTS_PATH), str(backup_path))
        log(f"备份: {backup_path}")
    except PermissionError:
        pass

    lines = content.split("\n")
    cleaned = []
    removed = 0

    for line in lines:
        should_remove = False
        if "127.0.0.1" in line or "0.0.0.0" in line:
            for domain in BLOCKED_DOMAINS:
                if domain in line:
                    should_remove = True
                    removed += 1
                    break
        if "steampp.net" in line.lower():
            should_remove = True
            removed += 1
        if not should_remove:
            cleaned.append(line)

    new_content = "\n".join(cleaned)
    new_content = re.sub(r"\n{3,}", "\n\n", new_content)

    try:
        HOSTS_PATH.write_text(new_content, encoding="utf-8")
        log(f"移除 {removed} 条封锁录")
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
        log("DNS 缓存已刷")
        return True
    except PermissionError:
        log("要理员权限来写入 hosts 文件!", "ERROR")
        return False


def check_dependencies():
    log("===  Python 依赖 ===")
    required = ["requests", "beautifulsoup4", "lxml"]
    missing = []

    for pkg in required:
        try:
            result = subprocess.run(
                [PYTHON, "-c", f"import {pkg.replace('beautifulsoup4', 'bs4')}; print('OK')"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and "OK" in result.stdout:
                log(f"  [OK] {pkg}")
            else:
                missing.append(pkg)
                log(f"  [MISS] {pkg}", "WARN")
        except Exception as e:
            missing.append(pkg)
            log(f"  [ERROR] {pkg}: {e}", "WARN")

    if missing:
        log(f"缺失 {len(missing)} 依赖: {', '.join(missing)}")
        log(f"安命: {PYTHON} -m pip install {' '.join(missing)}")
    else:
        log("有依赖已安")

    return len(missing)


def check_network():
    log("=== 查网络连通 ===")
    try:
        result = subprocess.run(
            [
                PYTHON,
                "-c",
                "import requests; r = requests.get('https://api.github.com/users/octocat', timeout=10); "
                "print('OK' if r.status_code == 200 else f'FAIL:{r.status_code}')",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if "OK" in result.stdout:
            log("GitHub API: 访问")
            return True
        else:
            log(f"GitHub API: {result.stdout.strip()}", "WARN")
            return False
    except Exception as e:
        log(f"GitHub API: 不可访问 - {e}", "ERROR")
        return False


def health_check():
    log("=" * 60)
    log(f"/python 系统健康 - {datetime.now().isoformat()}")
    log("=" * 60)

    results = {}

    results["hosts_ok"] = check_hosts()
    results["network_ok"] = check_network()
    results["mcp_valid"] = validate_mcp()
    results["missing_deps"] = check_dependencies()

    log("")
    log("=== 健康查结 ===")
    all_ok = results["hosts_ok"] and results["network_ok"] and results["missing_deps"] == 0
    log(f"  hosts: {'OK' if results['hosts_ok'] else 'BLOCKED'}")
    log(f"  网络: {'OK' if results['network_ok'] else 'FAIL'}")
    log(f"  MCP: {results['mcp_valid']} 有效")
    log(f"  依赖: {results['missing_deps']} 缺失")
    log(f"  总体: {'HEALTHY' if all_ok else 'NEEDS ATTENTION'}")

    return all_ok


def full_maintenance():
    log("=" * 60)
    log(f"/python 系统维护 - {datetime.now().isoformat()}")
    log("=" * 60)

    clean_temp_files()
    backup_configs()
    check_hosts()
    validate_mcp()
    check_dependencies()
    check_network()

    log("")
    log("维护完成!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--fix-hosts":
            fix_hosts()
        elif cmd == "--health":
            ok = health_check()
            sys.exit(0 if ok else 1)
        elif cmd == "--clean":
            clean_temp_files()
        elif cmd == "--backup":
            backup_configs()
        elif cmd == "--deps":
            check_dependencies()
        elif cmd == "--network":
            check_network()
        else:
            print(f"用法: python {sys.argv[0]} [--fix-hosts|--health|--clean|--backup|--deps|--network]")
    else:
        full_maintenance()
