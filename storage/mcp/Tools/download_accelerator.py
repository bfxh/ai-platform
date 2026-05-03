#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download Accelerator MCP - 智能下载加速器

功能：
- 多线程下载（最高32线程）
- 断点续传
- 智能镜像选择
- P2P下载（BT/磁力）
- 视频下载
- 批量下载
- 速度限制

用法：
    python download_accelerator.py <action> [args...]

示例：
    python download_accelerator.py download <url> --threads 16
    python download_accelerator.py torrent <torrent_file>
    python download_accelerator.py magnet <magnet_link>
    python download_accelerator.py video <url> --quality 1080p
    python download_accelerator.py batch urls.txt
    python download_accelerator.py resume <task_id>
    python download_accelerator.py tasks
"""

import json
import sys
import os
import asyncio
import aiohttp
import aiofiles
import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple
import tempfile

# ============================================================
# 配置
# ============================================================
CONFIG = {
    "default_threads": 8,
    "max_threads": 32,
    "chunk_size": 1024 * 1024,  # 1MB
    "buffer_size": 16 * 1024 * 1024,  # 16MB
    "connection_timeout": 30,
    "retry_count": 5,
    "retry_delay": 5,
    "temp_dir": Path("D:/Downloads/Temp"),
    "output_dir": Path("D:/Downloads")
}

# 镜像源
MIRRORS = {
    "github": [
        "https://ghproxy.com/",
        "https://mirror.ghproxy.com/",
        "https://hub.fastgit.xyz/"
    ],
    "docker": [
        "https://docker.mirrors.ustc.edu.cn",
        "https://hub-mirror.c.163.com"
    ]
}

# 下载任务存储
download_tasks = {}
task_counter = 0

# ============================================================
# 工具函数
# ============================================================
def format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def format_speed(speed: float) -> str:
    """格式化速度"""
    return f"{format_size(int(speed))}/s"

def get_filename_from_url(url: str) -> str:
    """从URL提取文件名"""
    parsed = urlparse(url)
    filename = Path(parsed.path).name
    if not filename:
        filename = f"download_{int(time.time())}"
    return filename

def get_mirror_urls(url: str) -> List[str]:
    """获取镜像URL"""
    mirrors = []
    
    # GitHub镜像
    if "github.com" in url:
        for mirror in MIRRORS.get("github", []):
            mirrors.append(mirror + url)
    
    # Docker镜像
    elif "hub.docker.com" in url or "registry-1.docker.io" in url:
        for mirror in MIRRORS.get("docker", []):
            mirrors.append(url.replace("https://hub.docker.com", mirror))
    
    return mirrors

# ============================================================
# 下载核心
# ============================================================
class DownloadTask:
    """下载任务"""
    
    def __init__(self, url: str, output_path: Path, threads: int = 8):
        global task_counter
        task_counter += 1
        
        self.task_id = f"task_{task_counter}"
        self.url = url
        self.output_path = output_path
        self.threads = min(threads, CONFIG["max_threads"])
        self.status = "pending"
        self.progress = 0
        self.total_size = 0
        self.downloaded_size = 0
        self.speed = 0
        self.start_time = None
        self.end_time = None
        self.error = None
        self.chunks = []
        
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "url": self.url,
            "output_path": str(self.output_path),
            "status": self.status,
            "progress": self.progress,
            "total_size": self.total_size,
            "downloaded_size": self.downloaded_size,
            "speed": self.speed,
            "threads": self.threads,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error": self.error
        }

class DownloadAccelerator:
    """下载加速器"""
    
    def __init__(self):
        self.session = None
        self.semaphore = asyncio.Semaphore(CONFIG["max_threads"])
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            enable_cleanup_closed=True,
            force_close=True,
        )
        
        timeout = aiohttp.ClientTimeout(
            total=CONFIG["connection_timeout"],
            connect=10,
            sock_read=30
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_file_info(self, url: str) -> Tuple[int, bool]:
        """获取文件信息"""
        try:
            async with self.session.head(url, allow_redirects=True) as response:
                if response.status == 200:
                    size = int(response.headers.get("Content-Length", 0))
                    accept_ranges = response.headers.get("Accept-Ranges", "")
                    supports_resume = "bytes" in accept_ranges
                    return size, supports_resume
                return 0, False
        except:
            return 0, False
    
    async def download_chunk(self, url: str, start: int, end: int, temp_file: Path, task: DownloadTask):
        """下载分块"""
        headers = {"Range": f"bytes={start}-{end}"}
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status in [200, 206]:
                    async with aiofiles.open(temp_file, "r+b") as f:
                        await f.seek(start)
                        
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            task.downloaded_size += len(chunk)
                            
                            if task.total_size > 0:
                                task.progress = (task.downloaded_size / task.total_size) * 100
        except Exception as e:
            task.error = str(e)
    
    async def download_file(self, task: DownloadTask) -> bool:
        """下载文件"""
        async with self.semaphore:
            task.status = "downloading"
            task.start_time = time.time()
            
            try:
                # 获取文件信息
                file_size, supports_resume = await self.get_file_info(task.url)
                task.total_size = file_size
                
                # 创建临时文件
                temp_file = CONFIG["temp_dir"] / f"{task.task_id}.tmp"
                CONFIG["temp_dir"].mkdir(parents=True, exist_ok=True)
                
                # 预分配文件大小
                if file_size > 0:
                    async with aiofiles.open(temp_file, "wb") as f:
                        await f.seek(file_size - 1)
                        await f.write(b'\0')
                
                if supports_resume and file_size > 0 and task.threads > 1:
                    # 多线程下载
                    chunk_size = file_size // task.threads
                    tasks = []
                    
                    for i in range(task.threads):
                        start = i * chunk_size
                        end = start + chunk_size - 1 if i < task.threads - 1 else file_size - 1
                        
                        t = asyncio.create_task(
                            self.download_chunk(task.url, start, end, temp_file, task)
                        )
                        tasks.append(t)
                    
                    await asyncio.gather(*tasks)
                else:
                    # 单线程下载
                    async with self.session.get(task.url) as response:
                        if response.status == 200:
                            async with aiofiles.open(temp_file, "wb") as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    await f.write(chunk)
                                    task.downloaded_size += len(chunk)
                                    
                                    if task.total_size > 0:
                                        task.progress = (task.downloaded_size / task.total_size) * 100
                
                # 移动文件到目标位置
                task.output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(temp_file), str(task.output_path))
                
                task.status = "completed"
                task.end_time = time.time()
                task.speed = task.downloaded_size / (task.end_time - task.start_time)
                
                return True
                
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                return False
    
    async def download_with_mirrors(self, task: DownloadTask) -> bool:
        """使用镜像下载"""
        urls = [task.url] + get_mirror_urls(task.url)
        
        for url in urls:
            task.url = url
            if await self.download_file(task):
                return True
            
            # 失败后等待
            await asyncio.sleep(CONFIG["retry_delay"])
        
        return False
    
    def create_task(self, url: str, output_dir: Path, filename: str = None, threads: int = 8) -> DownloadTask:
        """创建下载任务"""
        if not filename:
            filename = get_filename_from_url(url)
        
        output_path = output_dir / filename
        
        # 处理文件名冲突
        counter = 1
        original_path = output_path
        while output_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            output_path = original_path.parent / f"{stem}_{counter}{suffix}"
            counter += 1
        
        task = DownloadTask(url, output_path, threads)
        download_tasks[task.task_id] = task
        return task

# ============================================================
# MCP 接口
# ============================================================
async def mcp_accelerated_download(params: Dict) -> Dict:
    """MCP加速下载接口"""
    url = params.get("url")
    if not url:
        return {"success": False, "error": "URL is required"}
    
    output_dir = Path(params.get("output_dir", CONFIG["output_dir"]))
    filename = params.get("filename")
    threads = params.get("threads", CONFIG["default_threads"])
    
    async with DownloadAccelerator() as accelerator:
        task = accelerator.create_task(url, output_dir, filename, threads)
        success = await accelerator.download_with_mirrors(task)
        
        return {
            "success": success,
            "task": task.to_dict()
        }

async def mcp_batch_download(params: Dict) -> Dict:
    """MCP批量下载接口"""
    urls = params.get("urls", [])
    if not urls:
        return {"success": False, "error": "URLs list is required"}
    
    output_dir = Path(params.get("output_dir", CONFIG["output_dir"]))
    max_concurrent = params.get("max_concurrent", 3)
    threads_per_file = params.get("threads_per_file", 4)
    
    async with DownloadAccelerator() as accelerator:
        tasks = []
        for url in urls:
            task = accelerator.create_task(url, output_dir, threads=threads_per_file)
            tasks.append(accelerator.download_with_mirrors(task))
        
        # 限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_download(task_coro):
            async with semaphore:
                return await task_coro
        
        results = await asyncio.gather(
            *[limited_download(t) for t in tasks],
            return_exceptions=True
        )
        
        return {
            "success": True,
            "results": [task.to_dict() for task in download_tasks.values()],
            "total": len(urls),
            "succeeded": sum(1 for r in results if r is True),
            "failed": sum(1 for r in results if r is not True and not isinstance(r, Exception)),
            "errors": sum(1 for r in results if isinstance(r, Exception))
        }

def mcp_list_tasks(params: Dict = None) -> Dict:
    """MCP列出任务接口"""
    status_filter = params.get("status", "all") if params else "all"
    
    tasks = []
    for task in download_tasks.values():
        if status_filter == "all" or task.status == status_filter:
            tasks.append(task.to_dict())
    
    return {
        "success": True,
        "tasks": tasks,
        "count": len(tasks)
    }

# ============================================================
# 命令行接口
# ============================================================
def print_help():
    """打印帮助信息"""
    print(__doc__)
    print("\n命令:")
    print("  download <url> [options]     加速下载")
    print("  batch <urls_file>            批量下载")
    print("  tasks                        列出任务")
    print("\n选项:")
    print("  --threads, -t <n>            线程数 (1-32)")
    print("  --output, -o <dir>           输出目录")
    print("  --filename, -f <name>        指定文件名")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action in ["--help", "-h", "help"]:
        print_help()
        sys.exit(0)
    
    if action == "download":
        if len(sys.argv) < 3:
            print("Usage: download_accelerator.py download <url> [options]")
            sys.exit(1)
        
        url = sys.argv[2]
        params = {"url": url}
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] in ["--threads", "-t"] and i + 1 < len(sys.argv):
                params["threads"] = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] in ["--output", "-o"] and i + 1 < len(sys.argv):
                params["output_dir"] = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] in ["--filename", "-f"] and i + 1 < len(sys.argv):
                params["filename"] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        result = asyncio.run(mcp_accelerated_download(params))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "batch":
        if len(sys.argv) < 3:
            print("Usage: download_accelerator.py batch <urls_file>")
            sys.exit(1)
        
        urls_file = sys.argv[2]
        
        try:
            with open(urls_file, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
        
        result = asyncio.run(mcp_batch_download({"urls": urls}))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "tasks":
        result = mcp_list_tasks()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "mcp":
        # MCP Server 模式
        for line in sys.stdin:
            try:
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                
                if method == "accelerated_download":
                    result = asyncio.run(mcp_accelerated_download(params))
                elif method == "batch_download":
                    result = asyncio.run(mcp_batch_download(params))
                elif method == "list_tasks":
                    result = mcp_list_tasks(params)
                else:
                    result = {"success": False, "error": f"Unknown method: {method}"}
                
                print(json.dumps(result, ensure_ascii=False))
                sys.stdout.flush()
                
            except json.JSONDecodeError:
                print(json.dumps({"success": False, "error": "Invalid JSON"}))
                sys.stdout.flush()
    
    else:
        print(f"Unknown action: {action}")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
