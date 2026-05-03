#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSTACK 服务管理器

功能:
- 监控 TRAE IDE 启动和关闭
- 自动启动/关闭 GSTACK 服务
- 提供服务状态监控
- 与 TRAE 生命周期同步

用法:
    python gstack_service.py start  # 启动服务
    python gstack_service.py stop   # 停止服务
    python gstack_service.py status # 查看状态
"""

import os
import sys
import time
import subprocess
import psutil
import json
from pathlib import Path
import logging
import threading

# 配置
AI_DIR = Path("/python").resolve()
GSTACK_DIR = AI_DIR / "gstack_core"
SERVICE_LOG = AI_DIR / "logs" / "gstack_service.log"
SERVICE_PID = AI_DIR / "logs" / "gstack_service.pid"
TRAE_PROCESS_NAME = "Trae CN.exe"

# 线程锁
_lock = threading.Lock()

# 确保日志目录存在
(SERVICE_LOG.parent).mkdir(parents=True, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(SERVICE_LOG)),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GSTACKService")


class GSTACKService:
    """GSTACK 服务管理器"""
    
    def __init__(self):
        self.running = False
        self.process = None
        
    def is_traae_running(self):
        """检查 TRAE IDE 是否运行"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == TRAE_PROCESS_NAME:
                return True
        return False
    
    def is_gstack_running(self):
        """检查 GSTACK 服务是否运行"""
        with _lock:
            if self.process and self.process.poll() is None:
                return True
            # 检查 PID 文件
            if SERVICE_PID.exists():
                try:
                    with open(SERVICE_PID, 'r') as f:
                        pid = int(f.read().strip())
                    proc = psutil.Process(pid)
                    return proc.is_running()
                except:
                    pass
            return False
    
    def start_gstack(self):
        """启动 GSTACK 服务"""
        if self.is_gstack_running():
            logger.info("GSTACK 服务已经运行")
            return True
        
        try:
            # 启动 GSTACK 服务
            logger.info("启动 GSTACK 服务...")
            
            # 运行自检
            self._run_self_check()
            
            logger.info("GSTACK 服务启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动 GSTACK 服务失败: {e}")
            return False
    
    def stop_gstack(self):
        """停止 GSTACK 服务"""
        if not self.is_gstack_running():
            logger.info("GSTACK 服务未运行")
            return True
        
        try:
            # 停止进程
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=10)
            
            # 检查 PID 文件并终止
            if SERVICE_PID.exists():
                try:
                    with open(SERVICE_PID, 'r') as f:
                        pid = int(f.read().strip())
                    proc = psutil.Process(pid)
                    if proc.is_running():
                        proc.terminate()
                        proc.wait(timeout=10)
                except:
                    pass
                
                # 删除 PID 文件
                SERVICE_PID.unlink(missing_ok=True)
            
            logger.info("GSTACK 服务已停止")
            self.running = False
            self.process = None
            return True
            
        except Exception as e:
            logger.error(f"停止 GSTACK 服务失败: {e}")
            return False
    
    def _run_self_check(self):
        """运行自检"""
        try:
            self_check_script = GSTACK_DIR / "self_check.ps1"
            if self_check_script.exists():
                logger.info("运行 GSTACK 自检...")
                subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(self_check_script)],
                    cwd=str(AI_DIR),
                    capture_output=True,
                    text=True
                )
        except Exception as e:
            logger.error(f"运行自检失败: {e}")
    
    def monitor(self):
        """监控模式 - 与 TRAE 同步"""
        logger.info("启动 GSTACK 服务监控...")
        self.running = True
        
        try:
            while self.running:
                traae_running = self.is_traae_running()
                gstack_running = self.is_gstack_running()
                
                if traae_running and not gstack_running:
                    logger.info("TRAE 已启动，启动 GSTACK 服务...")
                    self.start_gstack()
                elif not traae_running and gstack_running:
                    logger.info("TRAE 已关闭，停止 GSTACK 服务...")
                    self.stop_gstack()
                
                # 每 5 秒检查一次
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("监控被用户中断")
        except Exception as e:
            logger.error(f"监控出错: {e}")
        finally:
            self.stop_gstack()
            logger.info("监控已停止")
    
    def get_status(self):
        """获取服务状态"""
        traae_running = self.is_traae_running()
        gstack_running = self.is_gstack_running()
        
        status = {
            "trae_running": traae_running,
            "gstack_running": gstack_running,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return status


def main():
    """主函数"""
    service = GSTACKService()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python gstack_service.py start   # 启动服务")
        print("  python gstack_service.py stop    # 停止服务")
        print("  python gstack_service.py status  # 查看状态")
        print("  python gstack_service.py monitor # 监控模式")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        service.start_gstack()
    elif command == "stop":
        service.stop_gstack()
    elif command == "status":
        status = service.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    elif command == "monitor":
        service.monitor()
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
