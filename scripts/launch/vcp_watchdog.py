import socket
import subprocess
import time
import argparse
import os
import sys
from datetime import datetime

VCP_DIR = r"\python\downloads\VCPToolBox\VCPToolBox-main"
LOG_FILE = r"\python\logs\vcp_watchdog.log"
MAX_RETRIES = 3
RETRY_INTERVAL = 10

SERVICES = {
    6005: {"name": "server.js", "script": "server.js"},
    6006: {"name": "adminServer.js", "script": "adminServer.js"},
}


def log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)


def check_port(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=3):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def start_service(script):
    try:
        proc = subprocess.Popen(
            ["node", script],
            cwd=VCP_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        return proc
    except Exception as e:
        log(f"启动 {script} 失败: {e}")
        return None


def restart_service(port, info):
    log(f"端口 {port} ({info['name']}) 无响应，开始重启...")
    for attempt in range(1, MAX_RETRIES + 1):
        proc = start_service(info["script"])
        if proc is None:
            log(f"第 {attempt}/{MAX_RETRIES} 次启动失败")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_INTERVAL)
            continue
        log(f"第 {attempt}/{MAX_RETRIES} 次启动成功 (PID: {proc.pid})，等待端口就绪...")
        time.sleep(RETRY_INTERVAL)
        if check_port(port):
            log(f"端口 {port} 已恢复")
            return True
        log(f"端口 {port} 仍未响应")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_INTERVAL)
    log(f"ALERT: 端口 {port} ({info['name']}) 重启 {MAX_RETRIES} 次后仍无响应，停止重试")
    return False


def check_all():
    for port, info in SERVICES.items():
        if not check_port(port):
            restart_service(port, info)
        else:
            log(f"端口 {port} ({info['name']}) 正常")


def main():
    parser = argparse.ArgumentParser(description="VCPToolBox Process Watchdog")
    parser.add_argument("--once", action="store_true", help="只检查一次")
    parser.add_argument("--interval", type=int, default=30, help="检查间隔秒数 (默认: 30)")
    args = parser.parse_args()

    log(f"看门狗启动 (模式: {'单次' if args.once else '循环'}, 间隔: {args.interval}s)")

    if args.once:
        check_all()
    else:
        while True:
            check_all()
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
