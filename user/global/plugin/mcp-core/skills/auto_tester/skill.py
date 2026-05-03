#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试系统 - 软件修改后自动验证
功能：
- 启动软件并检查是否正常运行
- 自动执行项目测试（Python/Pytest/Node等）
- 验证关键功能节点
- 记录测试结果到知识库
"""

import os
import sys
import json
import time
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# ─── 路径配置 ───────────────────────────────────────────────────────────────
PROJECT_DIR = Path("/python/MCP_Core/data")
TEST_LOG_PATH = PROJECT_DIR / "test_history.json"
KB_PATH = Path("/python/MCP_Core/data/knowledge_base.db")
PROJECT_DIR.mkdir(parents=True, exist_ok=True)

# ─── 软件启动配置 ───────────────────────────────────────────────────────────
SOFTWARE_LAUNCH = {
    "QClaw": {
        "exe": "%SOFTWARE_DIR%/AI/QClaw/QClaw.exe",
        "args": [],
        "wait_sec": 5,
        "check_window": "QClaw",
    },
    "StepFun": {
        "exe": "%SOFTWARE_DIR%/AI/StepFun/StepFun.exe",
        "args": [],
        "wait_sec": 5,
        "check_window": "StepFun",
    },
    "WorkBuddy": {
        "exe": "%SOFTWARE_DIR%/AI/WorkBuddy/WorkBuddy.exe",
        "args": [],
        "wait_sec": 8,
        "check_window": "WorkBuddy",
    },
    "TraeCN": {
        "exe": "%SOFTWARE_DIR%/KF/BC/Trae CN/Trae CN.exe",
        "args": [],
        "wait_sec": 10,
        "check_window": "Trae",
    },
    "VSCode": {
        "exe": "%SOFTWARE_DIR%/KF/BC/VS Code/Microsoft VS Code/Code.exe",
        "args": [],
        "wait_sec": 5,
        "check_window": "Visual Studio Code",
    },
    "Blender": {
        "exe": "%SOFTWARE_DIR%/KF/JM/blender/blender.exe",
        "args": ["--background"],
        "wait_sec": 8,
        "check_window": "Blender",
    },
    "Godot": {
        "exe": "%SOFTWARE_DIR%/KF/JM/Godot_v4.6.1-stable_win64.exe/Godot_v4.6.1-stable_win64.exe",
        "args": ["--headless"],
        "wait_sec": 6,
        "check_window": "Godot",
    },
}

# ─── 项目测试配置 ───────────────────────────────────────────────────────────
PROJECT_TEST_CONFIG = {
    "browser-use-main": {
        "path": "%SOFTWARE_DIR%/LLQ/browser-use-main",
        "type": "python",
        "test_cmd": ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
        "setup_cmd": None,
        "timeout": 120,
    },
    "browser-main": {
        "path": "%SOFTWARE_DIR%/LLQ/browser-main",
        "type": "rust",
        "test_cmd": ["cargo", "test", "--all"],
        "setup_cmd": None,
        "timeout": 180,
    },
    "CalamityMod": {
        "path": "%SOFTWARE_DIR%/KF/FBY/CalamityMod",
        "type": "dotnet",
        "test_cmd": None,
        "verify_file": "build.txt",
    },
    "MCP_Core": {
        "path": "/python/MCP_Core",
        "type": "python",
        "test_cmd": ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
        "setup_cmd": None,
        "timeout": 60,
    },
}


def check_process_running(process_name: str) -> bool:
    """检查进程是否在运行"""
    try:
        result = subprocess.run(
            ["powershell", "-Command", 
             f"Get-Process | Where-Object {{$_.ProcessName -like '*{process_name}*'}}"],
            capture_output=True, text=True, timeout=10
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def start_software(name: str, config: Dict) -> Dict:
    """启动软件并验证"""
    exe = Path(config["exe"])
    
    if not exe.exists():
        return {
            "name": name,
            "status": "failed",
            "error": f"可执行文件不存在: {exe}",
            "startup_time": None,
        }
    
    start_time = time.time()
    
    try:
        # 启动进程
        args = [str(exe)] + config.get("args", [])
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=subprocess.STARTUPINFO()
        )
        
        # 等待
        wait_sec = config.get("wait_sec", 5)
        time.sleep(wait_sec)
        
        elapsed = round(time.time() - start_time, 1)
        process_name = config.get("check_window", exe.stem)
        is_running = check_process_running(process_name)
        
        # 尝试关闭
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        
        return {
            "name": name,
            "status": "passed" if is_running else "warning",
            "launched": True,
            "is_running": is_running,
            "startup_time_sec": elapsed,
            "waited_sec": wait_sec,
            "exe_path": str(exe),
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        return {
            "name": name,
            "status": "failed",
            "error": str(e),
            "startup_time": None,
            "timestamp": datetime.now().isoformat(),
        }


def run_project_test(project_name: str, config: Dict) -> Dict:
    """运行项目测试"""
    project_path = Path(config["path"])
    
    if not project_path.exists():
        return {
            "project": project_name,
            "status": "failed",
            "error": f"项目目录不存在: {project_path}",
        }
    
    test_cmd = config.get("test_cmd")
    setup_cmd = config.get("setup_cmd")
    timeout = config.get("timeout", 120)
    
    # 先运行 setup
    if setup_cmd:
        subprocess.run(setup_cmd, cwd=str(project_path), 
                      capture_output=True, timeout=60)
    
    # 运行测试
    if not test_cmd:
        return {
            "project": project_name,
            "status": "skipped",
            "reason": "没有配置测试命令",
        }
    
    try:
        result = subprocess.run(
            test_cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        
        return {
            "project": project_name,
            "status": "passed" if result.returncode == 0 else "failed",
            "return_code": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
            "timestamp": datetime.now().isoformat(),
        }
        
    except subprocess.TimeoutExpired:
        return {
            "project": project_name,
            "status": "timeout",
            "error": f"测试超时（{timeout}秒）",
        }
    except Exception as e:
        return {
            "project": project_name,
            "status": "error",
            "error": str(e),
        }


def test_all_software() -> List[Dict]:
    """测试所有配置的软件"""
    results = []
    for name, config in SOFTWARE_LAUNCH.items():
        print(f"测试软件: {name}...", end=" ")
        result = start_software(name, config)
        results.append(result)
        print(f"[{result['status']}]")
    return results


def test_project(project_key: str) -> Dict:
    """测试指定项目"""
    if project_key not in PROJECT_TEST_CONFIG:
        return {"error": f"未知项目: {project_key}", "available": list(PROJECT_TEST_CONFIG.keys())}
    
    config = PROJECT_TEST_CONFIG[project_key]
    print(f"运行项目测试: {project_key}")
    return run_project_test(project_key, config)


def save_test_history(results: List[Dict]):
    """保存测试历史"""
    history = []
    if TEST_LOG_PATH.exists():
        try:
            history = json.loads(TEST_LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            history = []
    
    history.extend(results)
    # 只保留最近 500 条
    history = history[-500:]
    
    TEST_LOG_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def write_result_to_kb(result: Dict):
    """将测试结果写入知识库"""
    try:
        conn = sqlite3.connect(str(KB_PATH))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT,
                status TEXT,
                details TEXT,
                timestamp TEXT
            )
        """)
        conn.execute("""
            INSERT INTO test_results (test_name, status, details, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            result.get("name", result.get("project", "unknown")),
            result["status"],
            json.dumps(result, ensure_ascii=False),
            datetime.now().isoformat(),
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"知识库写入失败: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="自动化测试系统")
    parser.add_argument("--mode", choices=["software", "project", "all"], default="all",
                       help="测试模式")
    parser.add_argument("--project", type=str, help="指定项目名称")
    args = parser.parse_args()
    
    print("=== 自动化测试系统 ===\n")
    
    all_results = []
    
    if args.mode in ["software", "all"]:
        print("--- 软件启动测试 ---")
        software_results = test_all_software()
        all_results.extend(software_results)
    
    if args.mode in ["project", "all"]:
        print("\n--- 项目测试 ---")
        for proj_key in PROJECT_TEST_CONFIG:
            print(f"测试: {proj_key}...")
            proj_result = test_project(proj_key)
            all_results.append(proj_result)
    
    # 保存历史
    save_test_history(all_results)
    
    # 写入知识库
    for result in all_results:
        write_result_to_kb(result)
    
    # 打印摘要
    passed = sum(1 for r in all_results if r.get("status") == "passed")
    failed = sum(1 for r in all_results if r.get("status") == "failed")
    print(f"\n测试完成: {passed} 通过, {failed} 失败, {len(all_results)-passed-failed} 其他")
    print(f"历史已保存: {TEST_LOG_PATH}")
