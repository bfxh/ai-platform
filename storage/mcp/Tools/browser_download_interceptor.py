#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器下载拦截器 - 自动接管浏览器下载

功能：
- 拦截浏览器下载请求
- 自动转发到 Aria2 下载
- 支持 Chrome/Edge/Firefox 等浏览器
- 智能识别下载链接
- 自动分类下载文件
- 下载完成通知
- 支持扩展插件方式集成

用法：
    python browser_download_interceptor.py install    # 安装浏览器扩展
    python browser_download_interceptor.py start      # 启动拦截服务
    python browser_download_interceptor.py stop       # 停止服务
    python browser_download_interceptor.py status     # 查看状态
    python browser_download_interceptor.py config     # 配置管理

MCP调用：
    {"tool": "browser_download_interceptor", "action": "intercept", "params": {...}}
"""

import json
import sys
import os
import subprocess
import re
import winreg
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
CONFIG_PATH = AI_PATH / "MCP_Skills"

# 拦截器配置
INTERCEPTOR_PORT = 16800
CONFIG_FILE = CONFIG_PATH / "browser_download_interceptor.json"

# 下载规则
DOWNLOAD_RULES = {
    "file_extensions": [
        # 压缩包
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
        # 可执行文件
        ".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm",
        # 媒体文件
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
        ".mp3", ".flac", ".wav", ".aac", ".ogg",
        # 文档
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        # 镜像文件
        ".iso", ".img", ".vmdk",
        # 代码/数据
        ".apk", ".ipa", ".torrent",
    ],
    "mime_types": [
        "application/octet-stream",
        "application/zip",
        "application/x-zip-compressed",
        "application/x-rar-compressed",
        "application/x-7z-compressed",
        "application/pdf",
        "application/vnd.android.package-archive",
        "application/x-bittorrent",
        "video/",
        "audio/",
    ],
    "url_patterns": [
        r"\.zip$",
        r"\.rar$",
        r"\.7z$",
        r"\.exe$",
        r"\.msi$",
        r"\.mp4$",
        r"\.mkv$",
        r"\.mp3$",
        r"\.pdf$",
        r"\.torrent$",
        r"\.apk$",
        r"download",
        r"attachment",
    ]
}

# 文件分类规则
CATEGORY_RULES = {
    "software": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".apk", ".ipa"],
    "compressed": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "video": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    "audio": [".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a", ".wma"],
    "document": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
    "image": [".iso", ".img", ".dmg"],
    "torrent": [".torrent"],
}

# ============================================================
# 下载拦截器
# ============================================================
class DownloadInterceptor:
    """下载拦截器"""
    
    def __init__(self):
        self.config = self._load_config()
        self.server = None
        self.is_running = False
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        default_config = {
            "enabled": True,
            "port": INTERCEPTOR_PORT,
            "auto_categorize": True,
            "min_size_mb": 1,  # 小于 1MB 的文件不拦截
            "excluded_hosts": [
                "localhost",
                "127.0.0.1",
            ],
            "excluded_extensions": [
                ".html", ".htm", ".js", ".css", ".json", ".xml"
            ],
            "notification": True,
            "aria2_rpc": "http://localhost:6800/rpc",
            "download_dir": "D:/Downloads"
        }
        
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict):
        """保存配置"""
        CONFIG_PATH.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def is_download_url(self, url: str, headers: Dict = None) -> bool:
        """判断是否是下载链接"""
        url_lower = url.lower()
        
        # 检查排除的域名
        for host in self.config.get("excluded_hosts", []):
            if host in url_lower:
                return False
        
        # 检查文件扩展名
        for ext in DOWNLOAD_RULES["file_extensions"]:
            if url_lower.endswith(ext):
                # 检查是否在排除列表
                if ext in self.config.get("excluded_extensions", []):
                    return False
                return True
        
        # 检查 URL 模式
        for pattern in DOWNLOAD_RULES["url_patterns"]:
            if re.search(pattern, url_lower):
                return True
        
        # 检查 Content-Type
        if headers:
            content_type = headers.get("Content-Type", "").lower()
            for mime in DOWNLOAD_RULES["mime_types"]:
                if mime in content_type:
                    return True
        
        return False
    
    def get_category(self, filename: str) -> str:
        """获取文件分类"""
        ext = Path(filename).suffix.lower()
        
        for category, extensions in CATEGORY_RULES.items():
            if ext in extensions:
                return category
        
        return "other"
    
    def intercept_download(self, url: str, filename: str = None, referer: str = None) -> Dict:
        """拦截下载并转发到 Aria2"""
        # 获取文件名
        if not filename:
            filename = self._extract_filename(url)
        
        # 确定下载目录
        category = self.get_category(filename)
        
        if self.config.get("auto_categorize", True):
            download_dir = Path(self.config.get("download_dir", "D:/Downloads")) / category
        else:
            download_dir = Path(self.config.get("download_dir", "D:/Downloads"))
        
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # 构建 Aria2 选项
        options = {
            "dir": str(download_dir),
            "out": filename,
            "referer": referer or url,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # 调用 Aria2 添加下载
        try:
            import xmlrpc.client
            server = xmlrpc.client.ServerProxy(self.config.get("aria2_rpc", "http://localhost:6800/rpc"))
            gid = server.aria2.addUri([url], options)
            
            return {
                "success": True,
                "gid": gid,
                "url": url,
                "filename": filename,
                "category": category,
                "download_dir": str(download_dir)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def _extract_filename(self, url: str) -> str:
        """从 URL 提取文件名"""
        # 移除查询参数
        url = url.split('?')[0]
        
        # 获取路径部分
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path
        
        # 提取文件名
        filename = Path(path).name
        
        # 如果没有文件名，生成一个
        if not filename or '.' not in filename:
            filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return filename
    
    def install_browser_extension(self) -> Dict:
        """安装浏览器扩展"""
        results = {
            "success": True,
            "browsers": []
        }
        
        # Chrome/Edge 扩展
        chrome_result = self._install_chrome_extension()
        results["browsers"].append(chrome_result)
        
        # Firefox 扩展
        firefox_result = self._install_firefox_extension()
        results["browsers"].append(firefox_result)
        
        return results
    
    def _install_chrome_extension(self) -> Dict:
        """安装 Chrome/Edge 扩展"""
        # 创建扩展目录
        ext_dir = AI_PATH / "browser_extensions" / "download_interceptor"
        ext_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建 manifest.json
        manifest = {
            "manifest_version": 3,
            "name": "Download Interceptor",
            "version": "1.0.0",
            "description": "自动拦截下载并转发到 Aria2",
            "permissions": [
                "downloads",
                "activeTab",
                "storage"
            ],
            "host_permissions": [
                "<all_urls>"
            ],
            "background": {
                "service_worker": "background.js"
            },
            "action": {
                "default_popup": "popup.html",
                "default_icon": {
                    "16": "icon16.png",
                    "48": "icon48.png",
                    "128": "icon128.png"
                }
            },
            "icons": {
                "16": "icon16.png",
                "48": "icon48.png",
                "128": "icon128.png"
            }
        }
        
        with open(ext_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        # 创建 background.js
        background_js = f'''
// Background script for download interceptor

const INTERCEPTOR_URL = 'http://localhost:{INTERCEPTOR_PORT}/intercept';

// 监听下载事件
chrome.downloads.onDeterminingFilename.addListener((downloadItem, suggest) => {{
    // 检查是否应该拦截
    if (shouldIntercept(downloadItem)) {{
        // 取消浏览器下载
        chrome.downloads.cancel(downloadItem.id);
        
        // 发送到拦截器
        fetch(INTERCEPTOR_URL, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                url: downloadItem.url,
                filename: downloadItem.filename,
                referer: downloadItem.referrer
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            console.log('Download intercepted:', data);
            if (data.success) {{
                showNotification('下载已接管', `${{data.filename}} 已添加到 Aria2`);
            }} else {{
                showNotification('下载接管失败', data.error);
            }}
        }})
        .catch(error => {{
            console.error('Error:', error);
            // 如果拦截失败，恢复浏览器下载
            chrome.downloads.download({{url: downloadItem.url}});
        }});
        
        return;
    }}
    
    suggest({{filename: downloadItem.filename}});
}});

// 判断是否应该拦截
function shouldIntercept(downloadItem) {{
    // 文件大小检查（大于 1MB）
    if (downloadItem.fileSize > 0 && downloadItem.fileSize < 1024 * 1024) {{
        return false;
    }}
    
    // 文件类型检查
    const downloadExtensions = {json.dumps(DOWNLOAD_RULES["file_extensions"])};
    const url = downloadItem.url.toLowerCase();
    
    for (const ext of downloadExtensions) {{
        if (url.endsWith(ext)) {{
            return true;
        }}
    }}
    
    // MIME 类型检查
    const mimeTypes = {json.dumps(DOWNLOAD_RULES["mime_types"])};
    const mime = (downloadItem.mime || '').toLowerCase();
    
    for (const mimeType of mimeTypes) {{
        if (mime.includes(mimeType)) {{
            return true;
        }}
    }}
    
    return false;
}}

// 显示通知
function showNotification(title, message) {{
    chrome.notifications.create({{
        type: 'basic',
        iconUrl: 'icon128.png',
        title: title,
        message: message
    }});
}}
'''
        
        with open(ext_dir / "background.js", 'w', encoding='utf-8') as f:
            f.write(background_js)
        
        # 创建 popup.html
        popup_html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { width: 300px; padding: 10px; font-family: Arial, sans-serif; }
        h1 { font-size: 16px; margin-bottom: 10px; }
        .status { padding: 10px; background: #f0f0f0; border-radius: 4px; margin-bottom: 10px; }
        .enabled { color: green; }
        .disabled { color: red; }
        button { width: 100%; padding: 8px; margin-top: 10px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>下载拦截器</h1>
    <div class="status">
        状态: <span id="status" class="enabled">运行中</span>
    </div>
    <p>大于 1MB 的下载文件将自动转发到 Aria2</p>
    <button id="toggle">暂停拦截</button>
    <script src="popup.js"></script>
</body>
</html>'''
        
        with open(ext_dir / "popup.html", 'w', encoding='utf-8') as f:
            f.write(popup_html)
        
        # 创建简单的图标（使用 base64 编码的 PNG）
        # 这里省略图标创建，实际使用时可以添加
        
        return {
            "browser": "Chrome/Edge",
            "success": True,
            "path": str(ext_dir),
            "message": f"扩展已创建: {ext_dir}\\n请手动加载到 Chrome/Edge: chrome://extensions/ -> 开发者模式 -> 加载已解压的扩展"
        }
    
    def _install_firefox_extension(self) -> Dict:
        """安装 Firefox 扩展"""
        # Firefox 扩展目录
        ext_dir = AI_PATH / "browser_extensions" / "download_interceptor_firefox"
        ext_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建 manifest.json (v2 for Firefox)
        manifest = {
            "manifest_version": 2,
            "name": "Download Interceptor",
            "version": "1.0.0",
            "description": "自动拦截下载并转发到 Aria2",
            "permissions": [
                "downloads",
                "activeTab",
                "storage",
                "<all_urls>"
            ],
            "background": {
                "scripts": ["background.js"],
                "persistent": False
            },
            "browser_action": {
                "default_popup": "popup.html",
                "default_icon": {
                    "16": "icon16.png",
                    "48": "icon48.png"
                }
            },
            "icons": {
                "16": "icon16.png",
                "48": "icon48.png",
                "128": "icon128.png"
            }
        }
        
        with open(ext_dir / "manifest.json", 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        # 复制 background.js 和 popup.html
        # ...
        
        return {
            "browser": "Firefox",
            "success": True,
            "path": str(ext_dir),
            "message": f"扩展已创建: {ext_dir}\\n请手动加载到 Firefox: about:debugging -> 此 Firefox -> 临时载入附加组件"
        }

# ============================================================
# HTTP 服务器处理
# ============================================================
class InterceptorHandler(BaseHTTPRequestHandler):
    """拦截器 HTTP 处理器"""
    
    def log_message(self, format, *args):
        # 禁用日志输出
        pass
    
    def do_POST(self):
        """处理 POST 请求"""
        if self.path == '/intercept':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # 创建拦截器实例
                interceptor = DownloadInterceptor()
                
                # 拦截下载
                result = interceptor.intercept_download(
                    url=data.get('url'),
                    filename=data.get('filename'),
                    referer=data.get('referer')
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', 'http://localhost')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "内部错误"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """处理 OPTIONS 请求（CORS 预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'http://localhost')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

# ============================================================
# 服务管理
# ============================================================
class InterceptorService:
    """拦截器服务"""
    
    def __init__(self):
        self.server = None
        self.thread = None
        self.is_running = False
    
    def start(self) -> Dict:
        """启动服务"""
        if self.is_running:
            return {"success": True, "message": "服务已在运行"}
        
        try:
            self.server = HTTPServer(('localhost', INTERCEPTOR_PORT), InterceptorHandler)
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            self.is_running = True
            
            return {
                "success": True,
                "message": "拦截器服务已启动",
                "port": INTERCEPTOR_PORT,
                "url": f"http://localhost:{INTERCEPTOR_PORT}"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop(self) -> Dict:
        """停止服务"""
        if not self.is_running:
            return {"success": True, "message": "服务未运行"}
        
        try:
            if self.server:
                self.server.shutdown()
                self.server = None
            
            self.is_running = False
            return {"success": True, "message": "服务已停止"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "running": self.is_running,
            "port": INTERCEPTOR_PORT,
            "url": f"http://localhost:{INTERCEPTOR_PORT}" if self.is_running else None
        }

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.interceptor = DownloadInterceptor()
        self.service = InterceptorService()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "install":
            return self.interceptor.install_browser_extension()
        
        elif action == "start":
            return self.service.start()
        
        elif action == "stop":
            return self.service.stop()
        
        elif action == "status":
            return self.service.get_status()
        
        elif action == "intercept":
            url = params.get("url")
            filename = params.get("filename")
            referer = params.get("referer")
            return self.interceptor.intercept_download(url, filename, referer)
        
        elif action == "check_url":
            url = params.get("url")
            is_download = self.interceptor.is_download_url(url)
            return {
                "success": True,
                "url": url,
                "is_download": is_download
            }
        
        elif action == "config":
            return {
                "success": True,
                "config": self.interceptor.config
            }
        
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
    interceptor = DownloadInterceptor()
    service = InterceptorService()
    
    if cmd == "install":
        print("安装浏览器扩展...")
        result = interceptor.install_browser_extension()
        
        for browser in result.get("browsers", []):
            print(f"\n{browser['browser']}:")
            print(f"  状态: {'成功' if browser['success'] else '失败'}")
            print(f"  路径: {browser['path']}")
            print(f"  说明: {browser['message']}")
    
    elif cmd == "start":
        print("启动拦截器服务...")
        result = service.start()
        
        if result.get("success"):
            print(f"✓ {result['message']}")
            print(f"  端口: {result['port']}")
            print(f"  URL: {result['url']}")
        else:
            print(f"✗ 启动失败: {result.get('error')}")
    
    elif cmd == "stop":
        print("停止拦截器服务...")
        result = service.stop()
        
        if result.get("success"):
            print(f"✓ {result['message']}")
        else:
            print(f"✗ 停止失败: {result.get('error')}")
    
    elif cmd == "status":
        status = service.get_status()
        
        print("拦截器状态:")
        print("-" * 40)
        print(f"运行状态: {'运行中' if status['running'] else '已停止'}")
        print(f"端口: {status['port']}")
        if status['url']:
            print(f"URL: {status['url']}")
    
    elif cmd == "test":
        if len(sys.argv) < 3:
            print("用法: browser_download_interceptor.py test <url>")
            return
        
        url = sys.argv[2]
        is_download = interceptor.is_download_url(url)
        
        print(f"URL: {url}")
        print(f"是否是下载链接: {'是' if is_download else '否'}")
        
        if is_download:
            print("\n正在拦截并转发到 Aria2...")
            result = interceptor.intercept_download(url)
            
            if result.get("success"):
                print(f"✓ 拦截成功")
                print(f"  GID: {result['gid']}")
                print(f"  文件名: {result['filename']}")
                print(f"  分类: {result['category']}")
                print(f"  下载目录: {result['download_dir']}")
            else:
                print(f"✗ 拦截失败: {result.get('error')}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("浏览器下载拦截器 MCP 服务器已启动")
        
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
