#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aria2 下载管理器 MCP

功能：
- 集成 Aria2 下载引擎
- AriaNg Web 界面管理
- 支持 HTTP/HTTPS/FTP/BT/磁力链接
- 多线程下载
- 断点续传
- 下载队列管理
- 自动分类下载文件
- 兼容 MCP 工作流

用法：
    python aria2_mcp.py start                    # 启动 Aria2 服务
    python aria2_mcp.py stop                     # 停止 Aria2 服务
    python aria2_mcp.py status                   # 查看服务状态
    python aria2_mcp.py download <url> [options] # 添加下载任务
    python aria2_mcp.py list                     # 列出下载任务
    python aria2_mcp.py pause <gid>              # 暂停任务
    python aria2_mcp.py resume <gid>             # 恢复任务
    python aria2_mcp.py remove <gid>             # 删除任务
    python aria2_mcp.py config                   # 配置管理

MCP调用：
    {"tool": "aria2_mcp", "action": "download", "params": {"url": "..."}}
"""

import json
import sys
import os
import subprocess
import time
import urllib.request
import xmlrpc.client
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# ============================================================
# 配置
# ============================================================
# 安装路径
ARIA2_DIR = Path("%SOFTWARE_DIR%/GJ/aria2")
ARIA2_BIN = ARIA2_DIR / "aria2c.exe"
ARIA2_CONFIG = ARIA2_DIR / "aria2.conf"
ARIA2_SESSION = ARIA2_DIR / "aria2.session"

# AriaNg 路径
ARIANG_DIR = Path("%SOFTWARE_DIR%/GJ/AriaNg")

# 下载目录
import sys
sys.path.insert(0, r"\python")
from core.secure_utils import create_ssl_context

DOWNLOAD_DIR = Path("D:/Downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 默认配置
DEFAULT_CONFIG = {
    "dir": str(DOWNLOAD_DIR),
    "max-concurrent-downloads": 5,
    "max-connection-per-server": 16,
    "min-split-size": "10M",
    "split": 16,
    "max-overall-download-limit": 0,
    "max-download-limit": 0,
    "continue": "true",
    "remote-time": "true",
    "log-level": "warn",
    "console-log-level": "warn",
    "enable-rpc": "true",
    "rpc-listen-port": 6800,
    "rpc-allow-origin-all": "true",
    "rpc-listen-all": "false",
    "rpc-secret": "",
    "disable-ipv6": "true",
    "save-session": str(ARIA2_SESSION),
    "input-file": str(ARIA2_SESSION),
    "save-session-interval": 60,
    "force-save": "false",
    "bt-stop-timeout": 0,
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "seed-time": 0,
    "bt-tracker": [
        "udp://tracker.opentrackr.org:1337/announce",
        "udp://tracker.openbittorrent.com:6969/announce",
        "udp://tracker.torrent.eu.org:451/announce",
    ]
}

# RPC 连接配置
RPC_URL = "http://localhost:6800/rpc"
RPC_SECRET = ""

# ============================================================
# Aria2 安装器
# ============================================================
class Aria2Installer:
    """Aria2 安装器"""
    
    DOWNLOAD_URLS = {
        "aria2": "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip",
        "ariang": "https://github.com/mayswind/AriaNg/releases/download/1.3.7/AriaNg-1.3.7-AllInOne.zip"
    }
    
    def __init__(self):
        self.aria2_dir = ARIA2_DIR
        self.ariang_dir = ARIANG_DIR
    
    def is_installed(self) -> bool:
        """检查是否已安装"""
        return ARIA2_BIN.exists() and (self.ariang_dir / "index.html").exists()
    
    def install(self) -> Dict:
        """安装 Aria2 和 AriaNg"""
        results = {
            "success": True,
            "aria2": False,
            "ariang": False,
            "messages": []
        }
        
        # 创建目录
        self.aria2_dir.mkdir(parents=True, exist_ok=True)
        self.ariang_dir.mkdir(parents=True, exist_ok=True)
        
        # 安装 Aria2
        if not ARIA2_BIN.exists():
            print("正在下载 Aria2...")
            aria2_result = self._download_and_extract(
                self.DOWNLOAD_URLS["aria2"],
                self.aria2_dir,
                "aria2"
            )
            results["aria2"] = aria2_result["success"]
            results["messages"].append(aria2_result["message"])
        else:
            results["aria2"] = True
            results["messages"].append("Aria2 已安装")
        
        # 安装 AriaNg
        if not (self.ariang_dir / "index.html").exists():
            print("正在下载 AriaNg...")
            ariang_result = self._download_and_extract(
                self.DOWNLOAD_URLS["ariang"],
                self.ariang_dir,
                "ariang"
            )
            results["ariang"] = ariang_result["success"]
            results["messages"].append(ariang_result["message"])
        else:
            results["ariang"] = True
            results["messages"].append("AriaNg 已安装")
        
        # 创建配置文件
        if results["aria2"]:
            self._create_config()
        
        results["success"] = results["aria2"] and results["ariang"]
        return results
    
    def _download_and_extract(self, url: str, extract_to: Path, name: str) -> Dict:
        """下载并解压"""
        import zipfile
        import ssl
        
        try:
            # 创建 SSL 上下文
            ctx = create_ssl_context()
            
            # 下载文件
            zip_path = extract_to / f"{name}.zip"
            
            print(f"  下载 {name}...")
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, context=ctx, timeout=120) as response:
                with open(zip_path, 'wb') as f:
                    f.write(response.read())
            
            print(f"  解压 {name}...")
            # 解压
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            # 删除 zip 文件
            zip_path.unlink()
            
            # 处理 Aria2 的特殊目录结构
            if name == "aria2":
                # 移动文件到根目录
                for item in extract_to.iterdir():
                    if item.is_dir() and "aria2" in item.name.lower():
                        for subitem in item.iterdir():
                            target = extract_to / subitem.name
                            if subitem.is_dir():
                                import shutil
                                if target.exists():
                                    shutil.rmtree(target)
                                shutil.move(str(subitem), str(target))
                            else:
                                if target.exists():
                                    target.unlink()
                                shutil.move(str(subitem), str(target))
                        # 删除空目录
                        item.rmdir()
                        break
            
            return {"success": True, "message": f"{name} 安装成功"}
        
        except Exception as e:
            return {"success": False, "message": f"{name} 安装失败: {e}"}
    
    def _create_config(self):
        """创建 Aria2 配置文件"""
        config_lines = []
        
        for key, value in DEFAULT_CONFIG.items():
            if isinstance(value, list):
                for item in value:
                    config_lines.append(f"{key}={item}")
            elif isinstance(value, bool):
                config_lines.append(f"{key}={'true' if value else 'false'}")
            else:
                config_lines.append(f"{key}={value}")
        
        config_content = "\n".join(config_lines)
        
        with open(ARIA2_CONFIG, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"  配置文件已创建: {ARIA2_CONFIG}")

# ============================================================
# Aria2 服务管理
# ============================================================
class Aria2Service:
    """Aria2 服务管理"""
    
    def __init__(self):
        self.process = None
        self.installer = Aria2Installer()
    
    def is_running(self) -> bool:
        """检查服务是否运行"""
        try:
            # 尝试连接 RPC
            server = xmlrpc.client.ServerProxy(RPC_URL)
            server.aria2.getVersion()
            return True
        except:
            return False
    
    def start(self) -> Dict:
        """启动 Aria2 服务"""
        # 检查安装
        if not self.installer.is_installed():
            print("Aria2 未安装，正在安装...")
            result = self.installer.install()
            if not result["success"]:
                return {"success": False, "error": "安装失败"}
        
        # 检查是否已运行
        if self.is_running():
            return {"success": True, "message": "Aria2 服务已在运行"}
        
        # 创建 session 文件
        ARIA2_SESSION.touch(exist_ok=True)
        
        # 启动服务
        try:
            cmd = [
                str(ARIA2_BIN),
                "--conf-path", str(ARIA2_CONFIG),
                "--daemon"  # 后台运行
            ]
            
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待服务启动
            for _ in range(10):
                time.sleep(0.5)
                if self.is_running():
                    return {
                        "success": True,
                        "message": "Aria2 服务已启动",
                        "rpc_url": RPC_URL,
                        "ariang_url": f"file:///{ARIANG_DIR}/index.html"
                    }
            
            return {"success": False, "error": "服务启动超时"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop(self) -> Dict:
        """停止 Aria2 服务"""
        if not self.is_running():
            return {"success": True, "message": "Aria2 服务未运行"}
        
        try:
            # 通过 RPC 关闭
            server = xmlrpc.client.ServerProxy(RPC_URL)
            server.aria2.shutdown()
            
            return {"success": True, "message": "Aria2 服务已停止"}
        except Exception as e:
            # 强制终止进程
            try:
                subprocess.run(["taskkill", "/F", "/IM", "aria2c.exe"], 
                             capture_output=True, check=False)
                return {"success": True, "message": "Aria2 服务已强制停止"}
            except:
                return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict:
        """获取服务状态"""
        running = self.is_running()
        
        status = {
            "running": running,
            "installed": self.installer.is_installed(),
            "aria2_path": str(ARIA2_BIN) if ARIA2_BIN.exists() else None,
            "ariang_path": str(ARIANG_DIR) if ARIANG_DIR.exists() else None,
            "config_path": str(ARIA2_CONFIG) if ARIA2_CONFIG.exists() else None,
            "download_dir": str(DOWNLOAD_DIR)
        }
        
        if running:
            try:
                server = xmlrpc.client.ServerProxy(RPC_URL)
                version = server.aria2.getVersion()
                status["version"] = version.get("version", "unknown")
                
                # 获取全局统计
                stats = server.aria2.getGlobalStat()
                status["stats"] = {
                    "download_speed": self._format_speed(stats.get("downloadSpeed", "0")),
                    "upload_speed": self._format_speed(stats.get("uploadSpeed", "0")),
                    "active": stats.get("numActive", "0"),
                    "waiting": stats.get("numWaiting", "0"),
                    "stopped": stats.get("numStopped", "0")
                }
            except:
                pass
        
        return status
    
    def _format_speed(self, speed_str: str) -> str:
        """格式化速度"""
        try:
            speed = int(speed_str)
            if speed < 1024:
                return f"{speed} B/s"
            elif speed < 1024 * 1024:
                return f"{speed / 1024:.1f} KB/s"
            else:
                return f"{speed / (1024 * 1024):.1f} MB/s"
        except:
            return "0 B/s"

# ============================================================
# Aria2 下载管理
# ============================================================
class Aria2Manager:
    """Aria2 下载管理"""
    
    def __init__(self):
        self.service = Aria2Service()
        self._ensure_running()
    
    def _ensure_running(self):
        """确保服务运行"""
        if not self.service.is_running():
            self.service.start()
    
    def _get_server(self):
        """获取 RPC 服务器"""
        return xmlrpc.client.ServerProxy(RPC_URL)
    
    def add_download(self, url: str, options: Dict = None) -> Dict:
        """添加下载任务"""
        self._ensure_running()
        
        try:
            server = self._get_server()
            
            # 默认选项
            opts = options or {}
            
            # 添加下载
            if url.startswith("magnet:") or url.endswith(".torrent"):
                # BT/磁力链接
                gid = server.aria2.addUri([url], opts)
            else:
                # 普通下载
                gid = server.aria2.addUri([url], opts)
            
            return {
                "success": True,
                "gid": gid,
                "url": url,
                "message": "下载任务已添加"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_torrent(self, torrent_path: str, options: Dict = None) -> Dict:
        """添加 BT 种子下载"""
        self._ensure_running()
        
        try:
            server = self._get_server()
            
            # 读取种子文件
            with open(torrent_path, 'rb') as f:
                torrent_data = f.read()
            
            # Base64 编码
            import base64
            torrent_base64 = base64.b64encode(torrent_data).decode('utf-8')
            
            opts = options or {}
            gid = server.aria2.addTorrent(torrent_base64, [], opts)
            
            return {
                "success": True,
                "gid": gid,
                "torrent": torrent_path,
                "message": "BT 任务已添加"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_downloads(self, status: str = "all") -> Dict:
        """列出下载任务"""
        self._ensure_running()
        
        try:
            server = self._get_server()
            
            tasks = []
            
            if status in ["all", "active"]:
                active = server.aria2.tellActive()
                for task in active:
                    tasks.append(self._format_task(task, "active"))
            
            if status in ["all", "waiting"]:
                waiting = server.aria2.tellWaiting(0, 100)
                for task in waiting:
                    tasks.append(self._format_task(task, "waiting"))
            
            if status in ["all", "stopped"]:
                stopped = server.aria2.tellStopped(0, 100)
                for task in stopped:
                    tasks.append(self._format_task(task, "stopped"))
            
            return {
                "success": True,
                "count": len(tasks),
                "tasks": tasks
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _format_task(self, task: Dict, status: str) -> Dict:
        """格式化任务信息"""
        gid = task.get("gid", "")
        files = task.get("files", [])
        
        # 获取文件名
        file_name = "Unknown"
        if files:
            file_path = files[0].get("path", "")
            file_name = Path(file_path).name or files[0].get("uris", [{}])[0].get("uri", "Unknown")
        
        # 计算进度
        total_length = int(task.get("totalLength", 0))
        completed_length = int(task.get("completedLength", 0))
        progress = (completed_length / total_length * 100) if total_length > 0 else 0
        
        return {
            "gid": gid,
            "name": file_name,
            "status": status,
            "progress": round(progress, 1),
            "total_size": self._format_size(total_length),
            "completed_size": self._format_size(completed_length),
            "download_speed": self.service._format_speed(task.get("downloadSpeed", "0")),
            "connections": task.get("connections", "0")
        }
    
    def _format_size(self, size: int) -> str:
        """格式化大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
    
    def pause(self, gid: str) -> Dict:
        """暂停任务"""
        try:
            server = self._get_server()
            server.aria2.pause(gid)
            return {"success": True, "message": f"任务 {gid} 已暂停"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def resume(self, gid: str) -> Dict:
        """恢复任务"""
        try:
            server = self._get_server()
            server.aria2.unpause(gid)
            return {"success": True, "message": f"任务 {gid} 已恢复"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def remove(self, gid: str) -> Dict:
        """删除任务"""
        try:
            server = self._get_server()
            # 先停止任务
            try:
                server.aria2.remove(gid)
            except:
                pass
            # 移除结果
            server.aria2.removeDownloadResult(gid)
            return {"success": True, "message": f"任务 {gid} 已删除"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.service = Aria2Service()
        self.manager = Aria2Manager()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "start":
            return self.service.start()
        
        elif action == "stop":
            return self.service.stop()
        
        elif action == "status":
            return self.service.get_status()
        
        elif action == "install":
            return self.service.installer.install()
        
        elif action == "download":
            url = params.get("url")
            options = params.get("options", {})
            return self.manager.add_download(url, options)
        
        elif action == "add_torrent":
            torrent_path = params.get("torrent")
            options = params.get("options", {})
            return self.manager.add_torrent(torrent_path, options)
        
        elif action == "list":
            status = params.get("status", "all")
            return self.manager.list_downloads(status)
        
        elif action == "pause":
            gid = params.get("gid")
            return self.manager.pause(gid)
        
        elif action == "resume":
            gid = params.get("gid")
            return self.manager.resume(gid)
        
        elif action == "remove":
            gid = params.get("gid")
            return self.manager.remove(gid)
        
        elif action == "open_ariang":
            # 打开 AriaNg 界面
            index_path = ARIANG_DIR / "index.html"
            if index_path.exists():
                import webbrowser
                webbrowser.open(f"file:///{index_path}")
                return {"success": True, "message": "AriaNg 已打开"}
            else:
                return {"success": False, "error": "AriaNg 未安装"}
        
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
    service = Aria2Service()
    manager = Aria2Manager()
    
    if cmd == "install":
        print("安装 Aria2 和 AriaNg...")
        result = service.installer.install()
        
        if result["success"]:
            print("✓ 安装成功")
            for msg in result["messages"]:
                print(f"  {msg}")
        else:
            print("✗ 安装失败")
            for msg in result["messages"]:
                print(f"  {msg}")
    
    elif cmd == "start":
        print("启动 Aria2 服务...")
        result = service.start()
        
        if result.get("success"):
            print("✓ 服务已启动")
            print(f"  RPC 地址: {result.get('rpc_url')}")
            print(f"  AriaNg: {result.get('ariang_url')}")
        else:
            print(f"✗ 启动失败: {result.get('error')}")
    
    elif cmd == "stop":
        print("停止 Aria2 服务...")
        result = service.stop()
        
        if result.get("success"):
            print(f"✓ {result.get('message')}")
        else:
            print(f"✗ 停止失败: {result.get('error')}")
    
    elif cmd == "status":
        status = service.get_status()
        
        print("Aria2 状态:")
        print("-" * 40)
        print(f"运行状态: {'运行中' if status['running'] else '已停止'}")
        print(f"已安装: {'是' if status['installed'] else '否'}")
        print(f"安装路径: {status['aria2_path']}")
        print(f"AriaNg 路径: {status['ariang_path']}")
        print(f"下载目录: {status['download_dir']}")
        
        if status.get("version"):
            print(f"版本: {status['version']}")
        
        if status.get("stats"):
            stats = status["stats"]
            print(f"\n下载统计:")
            print(f"  下载速度: {stats['download_speed']}")
            print(f"  上传速度: {stats['upload_speed']}")
            print(f"  活动任务: {stats['active']}")
            print(f"  等待任务: {stats['waiting']}")
            print(f"  已完成: {stats['stopped']}")
    
    elif cmd == "download":
        if len(sys.argv) < 3:
            print("用法: aria2_mcp.py download <url> [options]")
            return
        
        url = sys.argv[2]
        options = {}
        
        # 解析选项
        for arg in sys.argv[3:]:
            if '=' in arg:
                k, v = arg.split('=', 1)
                options[k] = v
        
        print(f"添加下载: {url}")
        result = manager.add_download(url, options)
        
        if result.get("success"):
            print(f"✓ 任务已添加: {result['gid']}")
        else:
            print(f"✗ 添加失败: {result.get('error')}")
    
    elif cmd == "list":
        status = sys.argv[2] if len(sys.argv) > 2 else "all"
        result = manager.list_downloads(status)
        
        if result.get("success"):
            tasks = result.get("tasks", [])
            print(f"下载任务 ({len(tasks)} 个):")
            print("-" * 80)
            print(f"{'GID':<20} {'名称':<30} {'状态':<10} {'进度':<8} {'速度':<15}")
            print("-" * 80)
            
            for task in tasks:
                name = task['name'][:28] + ".." if len(task['name']) > 30 else task['name']
                print(f"{task['gid']:<20} {name:<30} {task['status']:<10} {task['progress']:>6.1f}% {task['download_speed']:<15}")
        else:
            print(f"✗ 获取失败: {result.get('error')}")
    
    elif cmd == "pause":
        if len(sys.argv) < 3:
            print("用法: aria2_mcp.py pause <gid>")
            return
        
        gid = sys.argv[2]
        result = manager.pause(gid)
        print(result.get("message") or result.get("error"))
    
    elif cmd == "resume":
        if len(sys.argv) < 3:
            print("用法: aria2_mcp.py resume <gid>")
            return
        
        gid = sys.argv[2]
        result = manager.resume(gid)
        print(result.get("message") or result.get("error"))
    
    elif cmd == "remove":
        if len(sys.argv) < 3:
            print("用法: aria2_mcp.py remove <gid>")
            return
        
        gid = sys.argv[2]
        result = manager.remove(gid)
        print(result.get("message") or result.get("error"))
    
    elif cmd == "ariang":
        index_path = ARIANG_DIR / "index.html"
        if index_path.exists():
            import webbrowser
            webbrowser.open(f"file:///{index_path}")
            print("AriaNg 已打开")
        else:
            print("AriaNg 未安装，请先运行: aria2_mcp.py install")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("Aria2 MCP 服务器已启动")
        print("支持操作: start, stop, status, install, download, list, pause, resume, remove")
        
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
