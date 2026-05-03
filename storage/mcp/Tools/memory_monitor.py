#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 内存监控器 (无 psutil 版本)

功能：
- 监控 MCP 服务内存使用
- 使用 Windows API 获取内存信息
- 生成内存使用报告
"""

import json
import sys
import os
import time
import sqlite3
import subprocess
import ctypes
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
import threading

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
CONFIG_PATH = AI_PATH / "MCP_Skills"
LOG_PATH = AI_PATH / "logs"

# 数据库
MEMORY_DB = CONFIG_PATH / "memory_monitor.db"

# 默认配置
DEFAULT_CONFIG = {
    "check_interval": 5,
    "alert_threshold_mb": 500,
    "max_history_days": 7,
    "log_to_db": True,
    "print_to_console": True
}

# ============================================================
# Windows 内存 API
# ============================================================
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]

def get_system_memory() -> Dict:
    """获取系统内存信息"""
    kernel32 = ctypes.windll.kernel32
    
    mem_status = MEMORYSTATUSEX()
    mem_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_status))
    
    total_mb = mem_status.ullTotalPhys / 1024 / 1024
    avail_mb = mem_status.ullAvailPhys / 1024 / 1024
    used_mb = total_mb - avail_mb
    
    return {
        "total_mb": round(total_mb, 2),
        "used_mb": round(used_mb, 2),
        "free_mb": round(avail_mb, 2),
        "percent": mem_status.dwMemoryLoad
    }

def get_process_memory(pid: int) -> Optional[Dict]:
    """获取进程内存信息"""
    try:
        kernel32 = ctypes.windll.kernel32
        
        # 打开进程
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        
        h_process = kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
            False,
            pid
        )
        
        if not h_process:
            return None
        
        # 获取内存信息
        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        
        result = kernel32.GetProcessMemoryInfo(
            h_process,
            ctypes.byref(pmc),
            pmc.cb
        )
        
        kernel32.CloseHandle(h_process)
        
        if result:
            return {
                "working_set_mb": round(pmc.WorkingSetSize / 1024 / 1024, 2),
                "peak_working_set_mb": round(pmc.PeakWorkingSetSize / 1024 / 1024, 2),
                "pagefile_usage_mb": round(pmc.PagefileUsage / 1024 / 1024, 2)
            }
        
        return None
    except:
        return None

# ============================================================
# 内存监控器
# ============================================================
@dataclass
class ProcessInfo:
    """进程信息"""
    pid: int
    name: str
    cmdline: str
    memory_mb: float
    status: str

class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self):
        self.config = self._load_config()
        self.db = self._init_db()
        self.running = False
        self.monitor_thread = None
    
    def _load_config(self) -> Dict:
        """加载配置"""
        config_file = CONFIG_PATH / "memory_monitor.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except:
                pass
        return DEFAULT_CONFIG
    
    def _init_db(self) -> sqlite3.Connection:
        """初始化数据库"""
        CONFIG_PATH.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(MEMORY_DB))
        
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                pid INTEGER,
                name TEXT,
                memory_mb REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                total_memory_mb REAL,
                used_memory_mb REAL,
                free_memory_mb REAL,
                percent_used REAL
            )
        ''')
        
        conn.commit()
        return conn
    
    def get_mcp_processes(self) -> List[ProcessInfo]:
        """获取所有 MCP 相关进程"""
        processes = []
        
        try:
            # 使用 tasklist 获取进程列表
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.strip().split('\n'):
                parts = line.split('","')
                if len(parts) >= 2:
                    name = parts[0].strip('"')
                    pid_str = parts[1].strip('"')
                    
                    try:
                        pid = int(pid_str)
                        
                        # 检查是否是 Python 进程
                        if 'python' in name.lower():
                            # 获取内存信息
                            mem_info = get_process_memory(pid)
                            if mem_info:
                                memory_mb = mem_info['working_set_mb']
                                
                                # 检查是否是 MCP 进程（通过命令行）
                                try:
                                    cmd_result = subprocess.run(
                                        ["wmic", "process", "where", f"ProcessId={pid}", 
                                         "get", "CommandLine", "/value"],
                                        capture_output=True,
                                        text=True
                                    )
                                    cmdline = cmd_result.stdout
                                    
                                    if '/python/MCP' in cmdline or '/python\\MCP' in cmdline:
                                        processes.append(ProcessInfo(
                                            pid=pid,
                                            name=name,
                                            cmdline=cmdline[:200],
                                            memory_mb=memory_mb,
                                            status="running"
                                        ))
                                except:
                                    pass
                    except:
                        pass
        
        except Exception as e:
            print(f"获取进程列表失败: {e}")
        
        return processes
    
    def log_to_db(self, processes: List[ProcessInfo], system: Dict):
        """记录到数据库"""
        if not self.config.get("log_to_db", True):
            return
        
        timestamp = datetime.now().isoformat()
        cursor = self.db.cursor()
        
        # 记录进程信息
        for proc in processes:
            cursor.execute('''
                INSERT INTO memory_logs 
                (timestamp, pid, name, memory_mb)
                VALUES (?, ?, ?, ?)
            ''', (timestamp, proc.pid, proc.name, proc.memory_mb))
        
        # 记录系统信息
        cursor.execute('''
            INSERT INTO system_logs 
            (timestamp, total_memory_mb, used_memory_mb, free_memory_mb, percent_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, system['total_mb'], system['used_mb'], 
              system['free_mb'], system['percent']))
        
        self.db.commit()
    
    def monitor_once(self):
        """执行一次监控"""
        processes = self.get_mcp_processes()
        system = get_system_memory()
        
        # 记录到数据库
        self.log_to_db(processes, system)
        
        return processes, system
    
    def start_monitoring(self):
        """开始监控"""
        self.running = True
        interval = self.config.get("check_interval", 5)
        
        print(f"内存监控已启动 (检查间隔: {interval}秒)")
        print("按 Ctrl+C 停止")
        print("-" * 80)
        
        try:
            while self.running:
                processes, system = self.monitor_once()
                
                if self.config.get("print_to_console", True):
                    self._print_status(processes, system)
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n监控已停止")
            self.running = False
    
    def _print_status(self, processes: List[ProcessInfo], system: Dict):
        """打印状态"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 80)
        print(f"MCP 内存监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 系统内存
        print(f"\n系统内存:")
        print(f"  总计: {system['total_mb']:.0f} MB")
        print(f"  已用: {system['used_mb']:.0f} MB ({system['percent']}%)")
        print(f"  可用: {system['free_mb']:.0f} MB")
        
        # MCP 进程
        print(f"\nMCP 进程 ({len(processes)} 个):")
        print("-" * 80)
        print(f"{'PID':<10} {'名称':<25} {'内存(MB)':<15}")
        print("-" * 80)
        
        # 按内存排序
        processes_sorted = sorted(processes, key=lambda p: p.memory_mb, reverse=True)
        
        for proc in processes_sorted:
            name = proc.name[:23] if len(proc.name) > 23 else proc.name
            print(f"{proc.pid:<10} {name:<25} {proc.memory_mb:<15.1f}")
        
        # 总计
        total_mcp = sum(p.memory_mb for p in processes)
        print("-" * 80)
        print(f"{'总计':<36} {total_mcp:<15.1f} MB")
        print(f"\n按 Ctrl+C 停止监控")
    
    def get_current_status(self) -> Dict:
        """获取当前状态"""
        processes, system = self.monitor_once()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": system,
            "mcp_processes": [
                {
                    "pid": p.pid,
                    "name": p.name,
                    "memory_mb": p.memory_mb,
                    "status": p.status
                }
                for p in processes
            ],
            "mcp_total_mb": sum(p.memory_mb for p in processes),
            "process_count": len(processes)
        }

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.monitor = MemoryMonitor()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        
        if action == "status":
            return {"success": True, **self.monitor.get_current_status()}
        
        else:
            return {"success": False, "error": f"未知操作: {action}"}

# ============================================================
# 命令行接口
# ============================================================
def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    monitor = MemoryMonitor()
    
    if cmd == "start" or cmd == "monitor":
        monitor.start_monitoring()
    
    elif cmd == "status":
        status = monitor.get_current_status()
        
        print("MCP 内存状态:")
        print("-" * 60)
        print(f"时间: {status['timestamp']}")
        print(f"\n系统内存:")
        print(f"  总计: {status['system']['total_mb']:.0f} MB")
        print(f"  已用: {status['system']['used_mb']:.0f} MB ({status['system']['percent']}%)")
        print(f"\nMCP 进程 ({status['process_count']} 个):")
        print(f"  总内存: {status['mcp_total_mb']:.1f} MB")
        
        for proc in status['mcp_processes']:
            print(f"  - {proc['name']} (PID:{proc['pid']}): {proc['memory_mb']:.1f} MB")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("内存监控 MCP 服务器已启动")
        
        mcp = MCPInterface()
        
        import select
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line)
                    response = mcp.handle(request)
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print(json.dumps({"success": False, "error": "无效的JSON"}))
                    sys.stdout.flush()
    
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
