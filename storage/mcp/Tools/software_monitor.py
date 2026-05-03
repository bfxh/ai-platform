#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件目录监控与自动整理脚本

功能：
- 监控 D:\rj 和 F:\rj 目录变化
- 自动检测新安装的软件
- 自动整理进 MCP 工作流
- 通知用户整理结果
- 空闲时自动运行，防止忘记

用法：
    python software_monitor.py                    # 运行监控（后台）
    python software_monitor.py --start            # 启动监控服务
    python software_monitor.py --stop             # 停止监控服务
    python software_monitor.py --status           # 查看监控状态
    python software_monitor.py --scan             # 立即扫描一次
    python software_monitor.py --add <path>       # 手动添加软件
    python software_monitor.py --list             # 列出已监控的软件
    python software_monitor.py --idle             # 空闲时运行一次

通知方式：
- 控制台输出
- 日志文件记录
- 生成整理报告
- 系统托盘通知（可选）
"""

import json
import sys
import os
import time
import hashlib
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict

# ============================================================
# 配置
# ============================================================
MONITOR_PATHS = [Path("D:/rj"), Path("F:/rj")]
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
CONFIG_PATH = AI_PATH / "MCP_Skills"
LOG_PATH = AI_PATH / "logs"
PID_FILE = CONFIG_PATH / "software_monitor.pid"

# 状态文件
STATE_FILE = CONFIG_PATH / "software_monitor_state.json"
REPORT_FILE = LOG_PATH / "software_monitor_report.json"

# 空闲检测配置
IDLE_CONFIG = {
    "check_interval": 60,  # 每60秒检查一次空闲状态
    "idle_threshold": 300,  # 空闲5分钟（300秒）后运行
    "cpu_threshold": 10,    # CPU使用率低于10%视为空闲
    "memory_threshold": 80, # 内存使用率低于80%
    "run_once_per_day": True,  # 每天最多运行一次
    "last_run_file": CONFIG_PATH / "last_idle_run.txt"
}

# 软件分类映射
SOFTWARE_CATEGORIES = {
    # 游戏引擎
    "unity": "game_engine",
    "unreal": "game_engine",
    "ue": "game_engine",
    "blender": "game_engine",
    "godot": "game_engine",
    "maya": "game_engine",
    "3dsmax": "game_engine",
    "c4d": "game_engine",
    
    # 开发工具
    "vscode": "dev_tool",
    "visual studio": "dev_tool",
    "pycharm": "dev_tool",
    "idea": "dev_tool",
    "eclipse": "dev_tool",
    "sublime": "dev_tool",
    "notepad": "dev_tool",
    
    # 提取工具
    "fmodel": "extractor",
    "umodel": "extractor",
    "assetripper": "extractor",
    "assetstudio": "extractor",
    "ilspy": "extractor",
    "dnspy": "extractor",
    
    # AI工具
    "stable diffusion": "ai_tool",
    "comfyui": "ai_tool",
    "fooocus": "ai_tool",
    "invokeai": "ai_tool",
    "ollama": "ai_tool",
    "lm studio": "ai_tool",
    
    # 媒体工具
    "ffmpeg": "media",
    "obs": "media",
    "premiere": "media",
    "after effects": "media",
    "davinci": "media",
    "handbrake": "media",
    
    # 下载工具
    "idm": "download",
    "aria2": "download",
    "motrix": "download",
    
    # 系统工具
    "7-zip": "system",
    "everything": "system",
    "powertoys": "system",
    "ditto": "system",
    "snipaste": "system",
    "sharex": "system",
    
    # 网络工具
    "clash": "network",
    "v2ray": "network",
    "shadowsocks": "network",
    "proxifier": "network",
    
    # 浏览器
    "chrome": "browser",
    "firefox": "browser",
    "edge": "browser",
    "brave": "browser",
    
    # 通讯工具
    "qq": "communication",
    "wechat": "communication",
    "discord": "communication",
    "telegram": "communication",
    "slack": "communication",
    
    # 游戏平台
    "steam": "game_platform",
    "epic": "game_platform",
    "gog": "game_platform",
    "origin": "game_platform",
    "uplay": "game_platform",
    "battle.net": "game_platform",
}

# 可执行文件模式
EXE_PATTERNS = ["*.exe", "*.bat", "*.cmd"]

# ============================================================
# 数据结构
# ============================================================
@dataclass
class SoftwareInfo:
    """软件信息"""
    name: str
    path: Path
    category: str
    exe_files: List[str]
    detected_at: str
    size_mb: float
    mcp_ready: bool = False
    integrated: bool = False
    integration_date: Optional[str] = None

# ============================================================
# 系统空闲检测
# ============================================================
class IdleDetector:
    """系统空闲检测器"""
    
    def __init__(self):
        self.config = IDLE_CONFIG
    
    def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except:
            return 0.0
    
    def get_memory_usage(self) -> float:
        """获取内存使用率"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except:
            return 0.0
    
    def get_idle_time(self) -> float:
        """获取系统空闲时间（秒）"""
        try:
            # Windows
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_uint),
                    ("dwTime", ctypes.c_ulong)
                ]
            
            import ctypes
            user32 = ctypes.windll.user32
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            user32.GetLastInputInfo(ctypes.byref(lii))
            
            import time
            idle_time = (ctypes.windll.kernel32.GetTickCount() - lii.dwTime) / 1000.0
            return idle_time
        except:
            return 0.0
    
    def is_system_idle(self) -> bool:
        """检查系统是否空闲"""
        cpu = self.get_cpu_usage()
        memory = self.get_memory_usage()
        idle_time = self.get_idle_time()
        
        return (
            cpu < self.config["cpu_threshold"] and
            memory < self.config["memory_threshold"] and
            idle_time > self.config["idle_threshold"]
        )
    
    def can_run_today(self) -> bool:
        """检查今天是否已经运行过"""
        if not self.config["run_once_per_day"]:
            return True
        
        last_run_file = self.config["last_run_file"]
        
        if not last_run_file.exists():
            return True
        
        try:
            with open(last_run_file, 'r') as f:
                last_run = f.read().strip()
            
            last_date = datetime.fromisoformat(last_run).date()
            today = datetime.now().date()
            
            return last_date < today
        except:
            return True
    
    def mark_run_today(self):
        """标记今天已运行"""
        last_run_file = self.config["last_run_file"]
        last_run_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(last_run_file, 'w') as f:
            f.write(datetime.now().isoformat())

# ============================================================
# 服务管理
# ============================================================
class ServiceManager:
    """监控服务管理器"""
    
    @staticmethod
    def is_running() -> bool:
        """检查服务是否正在运行"""
        if not PID_FILE.exists():
            return False
        
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, False, pid)
            
            if handle:
                kernel32.CloseHandle(handle)
                return True
            else:
                # PID文件存在但进程不存在，清理
                PID_FILE.unlink()
                return False
        
        except:
            return False
    
    @staticmethod
    def start() -> bool:
        """启动监控服务"""
        if ServiceManager.is_running():
            print("监控服务已经在运行")
            return False
        
        # 使用后台方式启动
        try:
            import subprocess
            import sys
            
            # 创建后台进程
            if sys.platform == 'win32':
                # Windows: 使用 pythonw 隐藏控制台
                pythonw = Path(sys.executable).parent / 'pythonw.exe'
                if pythonw.exists():
                    subprocess.Popen(
                        [str(pythonw), __file__, '--daemon'],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    subprocess.Popen(
                        [sys.executable, __file__, '--daemon'],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
            else:
                subprocess.Popen(
                    [sys.executable, __file__, '--daemon'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            print("监控服务已启动（后台运行）")
            return True
        
        except Exception as e:
            print(f"启动失败: {e}")
            return False
    
    @staticmethod
    def stop() -> bool:
        """停止监控服务"""
        if not ServiceManager.is_running():
            print("监控服务未在运行")
            return False
        
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            # 终止进程
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, False, pid)
            
            if handle:
                kernel32.TerminateProcess(handle, 0)
                kernel32.CloseHandle(handle)
            
            PID_FILE.unlink()
            print("监控服务已停止")
            return True
        
        except Exception as e:
            print(f"停止失败: {e}")
            return False
    
    @staticmethod
    def save_pid():
        """保存当前进程PID"""
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    
    @staticmethod
    def remove_pid():
        """移除PID文件"""
        if PID_FILE.exists():
            PID_FILE.unlink()

# ============================================================
# 软件监控器
# ============================================================
class SoftwareMonitor:
    """软件目录监控器"""
    
    def __init__(self):
        self.state = self._load_state()
        self.known_software = self.state.get("known_software", {})
        self.integrated_software = self.state.get("integrated_software", [])
        self.running = False
        self.idle_detector = IdleDetector()
    
    def _load_state(self) -> Dict:
        """加载状态"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"known_software": {}, "integrated_software": []}
    
    def _save_state(self):
        """保存状态"""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "known_software": self.known_software,
                "integrated_software": self.integrated_software,
                "last_scan": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def _detect_category(self, name: str) -> str:
        """检测软件类别"""
        name_lower = name.lower()
        
        for keyword, category in SOFTWARE_CATEGORIES.items():
            if keyword in name_lower:
                return category
        
        return "unknown"
    
    def _find_exe_files(self, path: Path) -> List[str]:
        """查找可执行文件"""
        exe_files = []
        
        try:
            for pattern in EXE_PATTERNS:
                for exe in path.rglob(pattern):
                    # 排除卸载程序
                    if "unins" in exe.name.lower() or "uninstall" in exe.name.lower():
                        continue
                    exe_files.append(str(exe.relative_to(path)))
                    if len(exe_files) >= 5:  # 最多5个
                        break
        except:
            pass
        
        return exe_files
    
    def _calculate_size(self, path: Path) -> float:
        """计算目录大小（MB）"""
        total_size = 0
        
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except:
            pass
        
        return round(total_size / (1024 * 1024), 2)
    
    def _generate_id(self, path: Path) -> str:
        """生成软件ID"""
        return hashlib.md5(str(path).encode()).hexdigest()[:12]
    
    def scan_directory(self, directory: Path) -> List[SoftwareInfo]:
        """扫描目录中的软件"""
        software_list = []
        
        if not directory.exists():
            return software_list
        
        for item in directory.iterdir():
            if not item.is_dir():
                continue
            
            # 跳过系统目录
            if item.name.startswith('.') or item.name.startswith('_'):
                continue
            
            software_id = self._generate_id(item)
            
            # 检查是否已存在
            if software_id in self.known_software:
                continue
            
            # 检测软件信息
            category = self._detect_category(item.name)
            exe_files = self._find_exe_files(item)
            size_mb = self._calculate_size(item)
            
            # 只记录有exe文件的目录
            if exe_files:
                info = SoftwareInfo(
                    name=item.name,
                    path=item,
                    category=category,
                    exe_files=exe_files,
                    detected_at=datetime.now().isoformat(),
                    size_mb=size_mb
                )
                software_list.append(info)
        
        return software_list
    
    def scan_all(self) -> List[SoftwareInfo]:
        """扫描所有监控目录"""
        all_software = []
        
        for monitor_path in MONITOR_PATHS:
            software_list = self.scan_directory(monitor_path)
            all_software.extend(software_list)
        
        return all_software
    
    def integrate_to_workflow(self, software: SoftwareInfo) -> Dict:
        """将软件整合进 MCP 工作流"""
        result = {
            "success": False,
            "software": software.name,
            "actions": []
        }
        
        # 1. 添加到 known_software
        software_id = self._generate_id(software.path)
        self.known_software[software_id] = {
            "name": software.name,
            "path": str(software.path),
            "category": software.category,
            "exe_files": software.exe_files,
            "detected_at": software.detected_at,
            "size_mb": software.size_mb,
            "integrated": True,
            "integration_date": datetime.now().isoformat()
        }
        
        # 2. 生成 MCP 适配器建议
        adapter_suggestion = self._generate_adapter_suggestion(software)
        result["adapter_suggestion"] = adapter_suggestion
        
        # 3. 添加到已整合列表
        self.integrated_software.append(software_id)
        
        # 4. 保存状态
        self._save_state()
        
        result["success"] = True
        result["actions"].append("已添加到 known_software")
        result["actions"].append("已生成 MCP 适配器建议")
        
        return result
    
    def _generate_adapter_suggestion(self, software: SoftwareInfo) -> Dict:
        """生成 MCP 适配器建议"""
        # 根据类别生成建议
        category_actions = {
            "game_engine": ["open", "import", "export", "render", "build"],
            "dev_tool": ["open", "edit", "build", "debug"],
            "extractor": ["open", "extract", "analyze"],
            "ai_tool": ["generate", "process", "convert"],
            "media": ["open", "convert", "edit", "export"],
            "download": ["download", "manage", "schedule"],
            "system": ["open", "configure", "optimize"],
            "network": ["connect", "configure", "monitor"],
            "browser": ["open", "navigate", "automation"],
            "communication": ["open", "message", "call"],
            "game_platform": ["open", "launch", "manage"],
            "unknown": ["open", "run"]
        }
        
        actions = category_actions.get(software.category, ["open"])
        main_exe = software.exe_files[0] if software.exe_files else ""
        
        return {
            "software_name": software.name,
            "category": software.category,
            "suggested_name": software.name.lower().replace(' ', '_').replace('-', '_'),
            "main_exe": main_exe,
            "capabilities": actions,
            "adapter_template": f"""# {software.name} MCP Adapter

class {software.name.replace(' ', '')}MCP:
    def __init__(self):
        self.path = r"{software.path}"
        self.exe = "{main_exe}"
    
    def open(self, file=None):
        # 打开软件
        pass
    
""" + "\n".join([f"    def {action}(self, **kwargs):\n        # {action} 操作\n        pass" for action in actions[1:]]),
            "mcp_config_entry": {
                "command": "python",
                "args": [f"/python/MCP/{software.name.lower().replace(' ', '_')}_mcp.py"],
                "description": f"{software.name} 工具 - {', '.join(actions)}",
            }
        }
    
    def generate_report(self, new_software: List[SoftwareInfo]) -> str:
        """生成整理报告"""
        report = []
        report.append("=" * 60)
        report.append("软件监控整理报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        report.append("")
        
        if not new_software:
            report.append("未发现新软件")
            return "\n".join(report)
        
        report.append(f"发现 {len(new_software)} 个新软件:")
        report.append("")
        
        for i, software in enumerate(new_software, 1):
            report.append(f"{i}. {software.name}")
            report.append(f"   路径: {software.path}")
            report.append(f"   类别: {software.category}")
            report.append(f"   大小: {software.size_mb} MB")
            report.append(f"   可执行文件: {', '.join(software.exe_files[:3])}")
            report.append("")
        
        report.append("-" * 60)
        report.append("已自动整合进 MCP 工作流")
        report.append("-" * 60)
        
        return "\n".join(report)
    
    def notify_user(self, message: str):
        """通知用户"""
        print("\n" + "=" * 60)
        print("通知")
        print("=" * 60)
        print(message)
        print("=" * 60 + "\n")
        
        # 保存到日志
        LOG_PATH.mkdir(parents=True, exist_ok=True)
        log_file = LOG_PATH / "software_monitor.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().isoformat()}]\n")
            f.write(message)
            f.write("\n\n")
    
    def run_idle_scan(self):
        """在空闲时运行扫描"""
        if not self.idle_detector.can_run_today():
            print("今天已经运行过空闲扫描，跳过")
            return
        
        print("等待系统空闲...")
        print(f"空闲条件: CPU < {IDLE_CONFIG['cpu_threshold']}%, 内存 < {IDLE_CONFIG['memory_threshold']}%, 空闲时间 > {IDLE_CONFIG['idle_threshold']}秒")
        
        # 等待系统空闲
        while not self.idle_detector.is_system_idle():
            time.sleep(IDLE_CONFIG["check_interval"])
            cpu = self.idle_detector.get_cpu_usage()
            memory = self.idle_detector.get_memory_usage()
            idle_time = self.idle_detector.get_idle_time()
            print(f"  CPU: {cpu:.1f}%, 内存: {memory:.1f}%, 空闲: {idle_time:.0f}s", end="\r")
        
        print("\n系统已空闲，开始扫描...")
        
        # 执行扫描
        new_software = self.scan_all()
        
        if new_software:
            report = self.generate_report(new_software)
            print(report)
            
            for software in new_software:
                result = self.integrate_to_workflow(software)
                if result["success"]:
                    print(f"✓ 已整合: {software.name}")
            
            self.notify_user(report)
        else:
            print("未发现新软件")
        
        # 标记今天已运行
        self.idle_detector.mark_run_today()
        print(f"扫描完成，下次运行时间: 明天")
    
    def run_daemon(self):
        """后台守护进程模式"""
        self.running = True
        ServiceManager.save_pid()
        
        print("监控服务已启动（后台模式）")
        print(f"监控路径: {', '.join(str(p) for p in MONITOR_PATHS)}")
        print("空闲时自动扫描，防止忘记整理")
        print()
        
        try:
            while self.running:
                # 检查是否可以运行（每天一次）
                if self.idle_detector.can_run_today():
                    # 等待系统空闲
                    if self.idle_detector.is_system_idle():
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 系统空闲，开始扫描...")
                        
                        new_software = self.scan_all()
                        
                        if new_software:
                            report = self.generate_report(new_software)
                            
                            for software in new_software:
                                result = self.integrate_to_workflow(software)
                                if result["success"]:
                                    print(f"✓ 已整合: {software.name}")
                            
                            self.notify_user(report)
                        else:
                            print("未发现新软件")
                        
                        # 标记今天已运行
                        self.idle_detector.mark_run_today()
                    else:
                        cpu = self.idle_detector.get_cpu_usage()
                        memory = self.idle_detector.get_memory_usage()
                        idle_time = self.idle_detector.get_idle_time()
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 等待空闲... CPU: {cpu:.1f}%, 内存: {memory:.1f}%, 空闲: {idle_time:.0f}s", end="\r")
                
                time.sleep(IDLE_CONFIG["check_interval"])
        
        except KeyboardInterrupt:
            print("\n监控服务停止中...")
        finally:
            self.running = False
            ServiceManager.remove_pid()
            print("监控服务已停止")

# ============================================================
# 主函数
# ============================================================
def main():
    """主函数"""
    monitor = SoftwareMonitor()
    
    if len(sys.argv) < 2:
        # 显示帮助
        print(__doc__)
        print()
        print("快捷命令:")
        print("  --start    启动后台监控服务（空闲时自动扫描）")
        print("  --stop     停止后台监控服务")
        print("  --status   查看监控服务状态")
        print("  --idle     空闲时运行一次扫描")
        print("  --scan     立即扫描一次")
        print("  --list     列出已监控的软件")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "--start":
        # 启动后台服务
        ServiceManager.start()
    
    elif cmd == "--stop":
        # 停止后台服务
        ServiceManager.stop()
    
    elif cmd == "--status":
        # 查看状态
        if ServiceManager.is_running():
            print("✓ 监控服务正在运行")
            print(f"  PID文件: {PID_FILE}")
        else:
            print("✗ 监控服务未运行")
        
        # 显示上次运行时间
        last_run_file = IDLE_CONFIG["last_run_file"]
        if last_run_file.exists():
            with open(last_run_file, 'r') as f:
                last_run = f.read().strip()
            print(f"  上次空闲扫描: {last_run}")
        
        # 显示已监控软件数量
        print(f"  已监控软件: {len(monitor.known_software)} 个")
    
    elif cmd == "--daemon":
        # 守护进程模式（内部使用）
        monitor.run_daemon()
    
    elif cmd == "--idle":
        # 空闲时运行一次
        monitor.run_idle_scan()
    
    elif cmd == "--scan":
        # 立即扫描
        print("立即扫描...")
        new_software = monitor.scan_all()
        
        if new_software:
            report = monitor.generate_report(new_software)
            print(report)
            
            for software in new_software:
                result = monitor.integrate_to_workflow(software)
                if result["success"]:
                    print(f"✓ 已整合: {software.name}")
            
            monitor.notify_user(report)
        else:
            print("未发现新软件")
    
    elif cmd == "--list":
        # 列出已监控的软件
        print("已监控的软件:")
        print("-" * 60)
        
        if not monitor.known_software:
            print("暂无")
            return
        
        for software_id, info in monitor.known_software.items():
            status = "✓ 已整合" if info.get("integrated") else "○ 未整合"
            print(f"{info['name']:<30} {info['category']:<15} {status}")
    
    elif cmd == "--add" and len(sys.argv) > 2:
        # 手动添加软件
        path = Path(sys.argv[2])
        
        if not path.exists():
            print(f"路径不存在: {path}")
            return
        
        category = monitor._detect_category(path.name)
        exe_files = monitor._find_exe_files(path)
        size_mb = monitor._calculate_size(path)
        
        software = SoftwareInfo(
            name=path.name,
            path=path,
            category=category,
            exe_files=exe_files,
            detected_at=datetime.now().isoformat(),
            size_mb=size_mb
        )
        
        result = monitor.integrate_to_workflow(software)
        
        if result["success"]:
            print(f"✓ 已添加: {software.name}")
            print(f"  类别: {software.category}")
            print(f"  建议适配器: {result['adapter_suggestion']['suggested_name']}_mcp.py")
    
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
