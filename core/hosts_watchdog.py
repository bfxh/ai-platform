#!/usr/bin/env python3
"""
/python hosts 文件监控守护
防止 Steam++ 等工具再次封锁 GitHub 域名
后台运行，每 60 秒检查一次 hosts 文件
"""

import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HOSTS_PATH = Path("C:/Windows/System32/drivers/etc/hosts")
_BASE = Path(os.environ.get("AI_BASE_DIR", Path(__file__).resolve().parent.parent))
LOG_PATH = _BASE / "logs" / "hosts_watchdog.log"
AI_PATH = _BASE

BLOCKED_DOMAINS = [
    "github.com",
    "api.github.com",
    "github.dev",
    "github.githubassets.com",
    "support-assets.githubassets.com",
    "education.github.com",
    "resources.github.com",
    "uploads.github.com",
    "archiveprogram.github.com",
    "raw.github.com",
    "githubusercontent.com",
    "raw.githubusercontent.com",
    "camo.githubusercontent.com",
    "cloud.githubusercontent.com",
    "avatars.githubusercontent.com",
    "avatars0.githubusercontent.com",
    "avatars1.githubusercontent.com",
    "avatars2.githubusercontent.com",
    "avatars3.githubusercontent.com",
    "user-images.githubusercontent.com",
    "objects.githubusercontent.com",
    "private-user-images.githubusercontent.com",
    "pages.github.com",
    "gist.github.com",
    "githubapp.com",
    "github.io",
    "www.github.io",
    "huggingface.co",
    "hub.docker.com",
    "greasyfork.org",
    "update.greasyfork.org",
]

CHECK_INTERVAL = 60


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check_hosts():
    try:
        content = HOSTS_PATH.read_text(encoding="utf-8")
    except PermissionError:
        return None
    except FileNotFoundError:
        return []

    blocked = []
    for domain in BLOCKED_DOMAINS:
        if f"127.0.0.1 {domain}" in content or f"127.0.0.1\t{domain}" in content:
            blocked.append(domain)
    return blocked


def auto_fix(blocked_domains):
    log(f"检测到 {len(blocked_domains)} 个域名被封锁，自动修复中...")

    try:
        content = HOSTS_PATH.read_text(encoding="utf-8")
    except PermissionError:
        log("需要管理员权限!", "ERROR")
        return False

    backup_path = HOSTS_PATH.parent / f"hosts.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(str(HOSTS_PATH), str(backup_path))
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
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
        log(f"自动修复完成，移除了 {removed} 条封锁记录")
        return True
    except PermissionError:
        log("需要管理员权限!", "ERROR")
        return False


def watchdog():
    log("hosts 监控守护启动")
    log(f"检查间隔: {CHECK_INTERVAL}秒")
    log(f"监控域名: {len(BLOCKED_DOMAINS)} 个")

    while True:
        try:
            blocked = check_hosts()
            if blocked is None:
                log("无法读取 hosts 文件", "WARN")
            elif len(blocked) > 0:
                log(f"[ALERT] 检测到 {len(blocked)} 个域名被封锁: {', '.join(blocked[:5])}...", "ERROR")
                if auto_fix(blocked):
                    log("自动修复成功")
                else:
                    log("自动修复失败，需要管理员权限", "ERROR")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            log("监控守护停止")
            break
        except Exception as e:
            log(f"异常: {e}", "ERROR")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        blocked = check_hosts()
        if blocked is None:
            print("无法读取 hosts 文件")
            sys.exit(2)
        elif len(blocked) > 0:
            print(f"BLOCKED: {len(blocked)} domains")
            for d in blocked:
                print(f"  - {d}")
            sys.exit(1)
        else:
            print("OK: No GitHub domains blocked")
            sys.exit(0)
    else:
        watchdog()
