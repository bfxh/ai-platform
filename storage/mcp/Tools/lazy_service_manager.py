#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 懒加载服务管理器

功能：
- 按需启动 MCP 服务
- 空闲服务自动停止
- 进程池共享
- 内存优化
- 服务状态监控

用法：
    python lazy_service_manager.py start              # 启动管理器
    python lazy_service_manager.py stop               # 停止管理器
    python lazy_service_manager.py status             # 查看状态
    python lazy_service_manager.py call <tool> <action>  # 调用服务
    python lazy_service_manager.py list               # 列出可用服务

MCP调用：
    {"tool": "lazy_service_manager", "action": "call", "params": {...}}
"""

import json
import sys
import os
import time
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import threading

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
CONFIG_PATH = AI_PATH / "MCP_Skills"

# 服务配置
SERVICE_CONFIG = {
    # 核心服务 - 常驻内存
    "core": {
        "desktop_automation": {
            "cmd": ["python", str(MCP_PATH / "da.py"), "mcp"],
            "memory_limit_mb": 50,
            "essential": True,  # 核心服务不停止
        },
        "net_pro": {
            "cmd": ["python", str(MCP_PATH / "net_pro.py"), "mcp"],
            "memory_limit_mb": 30,
            "essential": True,
        },
    },
    
    # 按需服务 - 懒加载
    "on_demand": {
        "vision_pro": {
            "cmd": ["python", str(MCP_PATH / "vision_pro.py"), "mcp"],
            "memory_limit_mb": 100,
            "idle_timeout": 300,  # 5分钟空闲停止
            "startup_delay": 2,  # 启动延迟2秒
        },
        "screen_eye": {
            "cmd": ["python", str(MCP_PATH / "screen_eye.py"), "mcp"],
            "memory_limit_mb": 80,
            "idle_timeout": 300,
        },
        "github_dl": {
            "cmd": ["python", str(MCP_PATH / "github_dl.py"), "mcp"],
            "memory_limit_mb": 50,
            "idle_timeout": 600,  # 10分钟
        },
        "extract": {
            "cmd": ["python", str(MCP_PATH / "extract.py"), "mcp"],
            "memory_limit_mb": 100,
            "idle_timeout": 300,
        },
        "ue_mcp": {
            "cmd": ["python", str(MCP_PATH / "ue_mcp.py"), "mcp"],
            "memory_limit_mb": 80,
            "idle_timeout": 600,
        },
        "unity_mcp": {
            "cmd": ["python", str(MCP_PATH / "unity_mcp.py"), "mcp"],
            "memory_limit_mb": 80,
            "idle_timeout": 600,
        },
        "ai_software": {
            "cmd": ["python", str(MCP_PATH / "ai_software.py"), "mcp"],
            "memory_limit_mb": 100,
            "idle_timeout": 300,
        },
        "aria2_mcp": {
            "cmd": ["python", str(MCP_PATH / "aria2_mcp.py"), "mcp"],
            "memory_limit_mb": 50,
            "idle_timeout": 0,  # 不自动停止（下载服务）
        },
        "github_accelerator": {
            "cmd": ["python", str(MCP_PATH / "github_accelerator.py"), "mcp"],
            "memory_limit_mb": 30,
            "idle_timeout": 0,
        },
        "browser_download_interceptor": {
            "cmd": ["python", str(MCP_PATH / "browser_download_interceptor.py"), "mcp"],
            "memory_limit_mb": 40,
            "idle_timeout": 0,
        },
        "local_software": {
            "cmd": ["python", str(MCP_PATH / "local_software.py"), "mcp"],
            "memory_limit_mb": 50,
            "idle_timeout": 600,
        },
        "auto_translate": {
            "cmd": ["python", str(MCP_PATH / "auto_translate.py"), "mcp"],
            "memory_limit_mb": 60,
            "idle_timeout": 300,
        },
        "github_auto_commit": {
            "cmd": ["python", str(MCP_PATH / "github_auto_commit.py"), "mcp"],
            "memory_limit_mb": 50,
            "idle_timeout": 600,
        },
        "memory_monitor": {
            "cmd": ["python", str(MCP_PATH / "memory_monitor.py"), "mcp"],
            "memory_limit_mb": 30,
            "idle_timeout": 0,
        },
    }
}

# ============================================================
# 服务信息
# ============================================================
@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    cmd: List[str]
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    status: str = "stopped"  # stopped, starting, running, stopping
    last_used: float = 0
    start_time: Optional[float] = None
    memory_limit_mb: int = 100
    idle_timeout: int = 300
    essential: bool = False
    call_count: int = 0

# ============================================================
# 懒加载服务管理器
# ============================================================
class LazyServiceManager:
    """懒加载服务管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.services: Dict[str, ServiceInfo] = {}
        self._init_services()
        self.cleanup_thread = None
        self.running = False
        
        # 进程池（用于共享进程）
        self._process_pool = None
        self._pool_max_workers = 4
    
    def _init_services(self):
        """初始化服务"""
        # 核心服务
        for name, config in SERVICE_CONFIG["core"].items():
            self.services[name] = ServiceInfo(
                name=name,
                cmd=config["cmd"],
                memory_limit_mb=config.get("memory_limit_mb", 100),
                essential=config.get("essential", False),
                idle_timeout=0  # 核心服务不停止
            )
        
        # 按需服务
        for name, config in SERVICE_CONFIG["on_demand"].items():
            self.services[name] = ServiceInfo(
                name=name,
                cmd=config["cmd"],
                memory_limit_mb=config.get("memory_limit_mb", 100),
                idle_timeout=config.get("idle_timeout", 300),
                essential=False
            )
    
    def get_process_pool(self):
        """获取进程池"""
        if self._process_pool is None:
            # 使用 spawn 模式更省内存
            ctx = mp.get_context('spawn')
            self._process_pool = ProcessPoolExecutor(
                max_workers=self._pool_max_workers,
                mp_context=ctx
            )
        return self._process_pool
    
    def start_service(self, name: str) -> Dict:
        """启动服务"""
        if name not in self.services:
            return {"success": False, "error": f"未知服务: {name}"}
        
        service = self.services[name]
        
        # 检查是否已在运行
        if service.status == "running" and service.process:
            # 检查进程是否真的在运行
            if service.process.poll() is None:
                service.last_used = time.time()
                return {"success": True, "message": "服务已在运行", "pid": service.pid}
            else:
                # 进程已退出，重置状态
                service.status = "stopped"
                service.process = None
        
        # 启动服务
        try:
            service.status = "starting"
            
            # 使用 subprocess 启动
            process = subprocess.Popen(
                service.cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            service.process = process
            service.pid = process.pid
            service.status = "running"
            service.start_time = time.time()
            service.last_used = time.time()
            
            # 等待服务启动
            time.sleep(1)
            
            return {
                "success": True,
                "message": f"服务 {name} 已启动",
                "pid": service.pid,
                "memory_limit_mb": service.memory_limit_mb
            }
        
        except Exception as e:
            service.status = "stopped"
            return {"success": False, "error": str(e)}
    
    def stop_service(self, name: str, force: bool = False) -> Dict:
        """停止服务"""
        if name not in self.services:
            return {"success": False, "error": f"未知服务: {name}"}
        
        service = self.services[name]
        
        # 核心服务不允许停止（除非强制）
        if service.essential and not force:
            return {"success": False, "error": "核心服务不能停止"}
        
        if service.status != "running" or not service.process:
            return {"success": True, "message": "服务未运行"}
        
        try:
            service.status = "stopping"
            
            # 尝试优雅停止
            if os.name == 'nt':
                # Windows
                subprocess.run(["taskkill", "/PID", str(service.pid), "/T", "/F"], 
                             capture_output=True, check=False)
            else:
                # Linux/Mac
                service.process.terminate()
                try:
                    service.process.wait(timeout=5)
                except:
                    service.process.kill()
            
            service.status = "stopped"
            service.process = None
            service.pid = None
            
            return {"success": True, "message": f"服务 {name} 已停止"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def call_service(self, name: str, action: str, params: Dict = None) -> Dict:
        """调用服务"""
        if name not in self.services:
            return {"success": False, "error": f"未知服务: {name}"}
        
        service = self.services[name]
        
        # 确保服务已启动
        if service.status != "running":
            result = self.start_service(name)
            if not result.get("success"):
                return result
            # 等待服务完全启动
            time.sleep(service.startup_delay if hasattr(service, 'startup_delay') else 1)
        
        # 更新最后使用时间
        service.last_used = time.time()
        service.call_count += 1
        
        # 发送 MCP 请求
        try:
            request = {
                "tool": name,
                "action": action,
                "params": params or {}
            }
            
            request_json = json.dumps(request) + "\n"
            
            if service.process and service.process.stdin:
                service.process.stdin.write(request_json.encode())
                service.process.stdin.flush()
                
                # 读取响应
                response_line = service.process.stdout.readline()
                response = json.loads(response_line.decode())
                
                return response
            else:
                return {"success": False, "error": "服务进程不可用"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_service_status(self, name: str = None) -> Dict:
        """获取服务状态"""
        if name:
            if name not in self.services:
                return {"success": False, "error": f"未知服务: {name}"}
            
            service = self.services[name]
            return {
                "success": True,
                "name": name,
                "status": service.status,
                "pid": service.pid,
                "essential": service.essential,
                "call_count": service.call_count,
                "memory_limit_mb": service.memory_limit_mb,
                "idle_timeout": service.idle_timeout
            }
        
        # 返回所有服务状态
        return {
            "success": True,
            "services": [
                {
                    "name": s.name,
                    "status": s.status,
                    "pid": s.pid,
                    "essential": s.essential,
                    "call_count": s.call_count,
                    "memory_limit_mb": s.memory_limit_mb,
                    "idle_timeout": s.idle_timeout
                }
                for s in self.services.values()
            ]
        }
    
    def cleanup_idle_services(self):
        """清理空闲服务"""
        current_time = time.time()
        stopped = []
        
        for name, service in self.services.items():
            # 跳过核心服务和未运行的服务
            if service.essential or service.status != "running":
                continue
            
            # 检查是否超过空闲时间
            if service.idle_timeout > 0:
                idle_time = current_time - service.last_used
                if idle_time > service.idle_timeout:
                    result = self.stop_service(name)
                    if result.get("success"):
                        stopped.append(name)
                        print(f"[懒加载] 停止空闲服务: {name} (空闲 {idle_time:.0f} 秒)")
        
        return stopped
    
    def start_cleanup_thread(self):
        """启动清理线程"""
        self.running = True
        
        def cleanup_loop():
            while self.running:
                self.cleanup_idle_services()
                time.sleep(60)  # 每分钟检查一次
        
        self.cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def stop_all_services(self):
        """停止所有服务"""
        self.running = False
        
        stopped = []
        for name in list(self.services.keys()):
            result = self.stop_service(name, force=True)
            if result.get("success"):
                stopped.append(name)
        
        return stopped
    
    def get_memory_usage(self) -> Dict:
        """获取内存使用情况"""
        total_memory = 0
        service_memory = []
        
        for name, service in self.services.items():
            if service.status == "running" and service.pid:
                try:
                    proc = psutil.Process(service.pid)
                    memory_mb = proc.memory_info().rss / 1024 / 1024
                    total_memory += memory_mb
                    
                    service_memory.append({
                        "name": name,
                        "pid": service.pid,
                        "memory_mb": round(memory_mb, 2),
                        "status": service.status
                    })
                except:
                    pass
        
        return {
            "total_mb": round(total_memory, 2),
            "service_count": len([s for s in service_memory if s["status"] == "running"]),
            "services": sorted(service_memory, key=lambda x: x["memory_mb"], reverse=True)
        }

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.manager = LazyServiceManager()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "start":
            name = params.get("service")
            return self.manager.start_service(name)
        
        elif action == "stop":
            name = params.get("service")
            force = params.get("force", False)
            return self.manager.stop_service(name, force)
        
        elif action == "call":
            name = params.get("service")
            service_action = params.get("service_action", "")
            service_params = params.get("service_params", {})
            return self.manager.call_service(name, service_action, service_params)
        
        elif action == "status":
            name = params.get("service")
            return self.manager.get_service_status(name)
        
        elif action == "memory":
            return {"success": True, **self.manager.get_memory_usage()}
        
        elif action == "cleanup":
            stopped = self.manager.cleanup_idle_services()
            return {"success": True, "stopped_services": stopped}
        
        elif action == "stop_all":
            stopped = self.manager.stop_all_services()
            return {"success": True, "stopped_services": stopped}
        
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
    manager = LazyServiceManager()
    
    if cmd == "start":
        print("启动懒加载服务管理器...")
        manager.start_cleanup_thread()
        
        # 启动核心服务
        print("启动核心服务...")
        for name in SERVICE_CONFIG["core"].keys():
            result = manager.start_service(name)
            status = "✓" if result.get("success") else "✗"
            print(f"  {status} {name}")
        
        print("\n懒加载管理器已启动")
        print("核心服务已启动，其他服务将按需启动")
        print("空闲服务将在5分钟后自动停止")
        print("\n按 Ctrl+C 停止")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n停止所有服务...")
            manager.stop_all_services()
            print("已停止")
    
    elif cmd == "stop":
        print("停止所有服务...")
        stopped = manager.stop_all_services()
        print(f"已停止 {len(stopped)} 个服务")
    
    elif cmd == "status":
        status = manager.get_service_status()
        memory = manager.get_memory_usage()
        
        print("服务状态:")
        print("=" * 80)
        print(f"{'服务名':<25} {'状态':<12} {'PID':<10} {'内存限制':<12} {'调用次数':<10}")
        print("-" * 80)
        
        for s in status.get("services", []):
            pid = str(s.get("pid", "-")) if s.get("pid") else "-"
            print(f"{s['name']:<25} {s['status']:<12} {pid:<10} {s['memory_limit_mb']:<12} {s['call_count']:<10}")
        
        print("-" * 80)
        print(f"\n内存使用: {memory['total_mb']:.1f} MB ({memory['service_count']} 个服务)")
    
    elif cmd == "memory":
        memory = manager.get_memory_usage()
        
        print("内存使用情况:")
        print("=" * 60)
        print(f"总内存: {memory['total_mb']:.1f} MB")
        print(f"运行服务数: {memory['service_count']}")
        print("\n服务详情:")
        print("-" * 60)
        print(f"{'服务名':<25} {'内存(MB)':<15}")
        print("-" * 60)
        
        for s in memory.get("services", []):
            print(f"{s['name']:<25} {s['memory_mb']:<15.1f}")
    
    elif cmd == "call":
        if len(sys.argv) < 4:
            print("用法: lazy_service_manager.py call <service> <action>")
            return
        
        service = sys.argv[2]
        action = sys.argv[3]
        
        print(f"调用 {service}.{action}...")
        result = manager.call_service(service, action)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "list":
        print("可用服务:")
        print("\n核心服务 (常驻):")
        for name in SERVICE_CONFIG["core"].keys():
            print(f"  - {name}")
        
        print("\n按需服务 (懒加载):")
        for name in SERVICE_CONFIG["on_demand"].keys():
            print(f"  - {name}")
    
    elif cmd == "cleanup":
        stopped = manager.cleanup_idle_services()
        if stopped:
            print(f"已停止 {len(stopped)} 个空闲服务:")
            for name in stopped:
                print(f"  - {name}")
        else:
            print("没有空闲服务需要停止")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("懒加载服务管理器 MCP 已启动")
        print("支持操作: start, stop, call, status, memory, cleanup")
        
        # 启动清理线程
        manager.start_cleanup_thread()
        
        # 启动核心服务
        for name in SERVICE_CONFIG["core"].keys():
            manager.start_service(name)
        
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
