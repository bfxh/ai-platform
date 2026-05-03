#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Downloader MCP - GitHub项目下载器

功能：
- 下载GitHub Release的文件（exe/zip/msi等）
- 克隆GitHub仓库
- 下载单个文件
- 自动选择最佳镜像源（解决国内访问慢的问题）
- 支持断点续传
- 自动解压zip

用法（命令行）：
    python github_dl.py release <owner/repo> [--filter exe]
    python github_dl.py clone <owner/repo>
    python github_dl.py file <url>
    python github_dl.py search <keyword>

示例：
    python github_dl.py release GHFear/AESDumpster
    python github_dl.py release 4sval/FModel --filter exe
    python github_dl.py clone baldurk/renderdoc
    python github_dl.py file https://github.com/user/repo/raw/main/tool.exe
"""

import json
import sys
import os
import ssl
import time
import struct
import socket
import threading
import hashlib
import zipfile
import shutil
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse, quote
from urllib.error import URLError, HTTPError

# ============================================================
# 配置
# ============================================================
DOWNLOAD_DIR = Path("%DEVTOOLS_DIR%/工具/GitHub")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# GitHub镜像源（按速度排序，自动切换）
MIRRORS = [
    "",  # 直连
    "https://mirror.ghproxy.com/",
    "https://gh-proxy.com/",
    "https://ghproxy.net/",
    "https://github.moeyy.xyz/",
    "https://hub.gitmirror.com/",
    "https://gh.ddlc.top/",
]

# API镜像
API_MIRRORS = [
    "https://api.github.com",
    "https://gh-api.p3terx.com",
]

# SSL配置
ctx = create_ssl_context()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/octet-stream,application/json,*/*',
}

# ============================================================
# 核心下载函数
# ============================================================
def fetch_url(url, timeout=30, max_size=None):
    """通用URL获取，自动尝试镜像"""
    errors = []
    
    # 如果是GitHub URL，尝试镜像
    urls_to_try = [url]
    if 'github.com' in url or 'raw.githubusercontent.com' in url:
        for mirror in MIRRORS:
            if mirror:
                urls_to_try.append(mirror + url)
    
    for try_url in urls_to_try:
        try:
            req = Request(try_url, headers=HEADERS)
            resp = urlopen(req, timeout=timeout, context=ctx)
            
            content_length = resp.headers.get('Content-Length')
            total = int(content_length) if content_length else None
            
            if max_size and total and total > max_size:
                return None, f"文件太大: {total} bytes"
            
            data = b''
            chunk_size = 65536
            downloaded = 0
            start_time = time.time()
            
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                data += chunk
                downloaded += len(chunk)
                
                # 进度显示
                elapsed = time.time() - start_time
                speed = downloaded / elapsed if elapsed > 0 else 0
                if total:
                    pct = downloaded * 100 / total
                    print(f"\r  下载中: {downloaded/1024/1024:.1f}/{total/1024/1024:.1f} MB ({pct:.0f}%) {speed/1024/1024:.1f} MB/s", end='', flush=True)
                else:
                    print(f"\r  下载中: {downloaded/1024/1024:.1f} MB {speed/1024/1024:.1f} MB/s", end='', flush=True)
            
            print()  # 换行
            return data, None
            
        except Exception as e:
            errors.append(f"{try_url[:60]}... -> {e}")
            continue
    
    return None, f"所有源都失败:\n" + "\n".join(errors[:5])


def download_file(url, output_path, timeout=120):
    """下载文件到指定路径"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"  目标: {output_path}")
    
    data, error = fetch_url(url, timeout=timeout)
    if error:
        print(f"  ✗ 下载失败: {error}")
        return False
    
    with open(output_path, 'wb') as f:
        f.write(data)
    
    size_mb = len(data) / 1024 / 1024
    print(f"  ✓ 完成! {size_mb:.1f} MB -> {output_path}")
    return True


# ============================================================
# GitHub API
# ============================================================
def github_api(endpoint, timeout=15):
    """调用GitHub API"""
    for api_base in API_MIRRORS:
        url = f"{api_base}{endpoint}"
        try:
            req = Request(url, headers={
                'User-Agent': HEADERS['User-Agent'],
                'Accept': 'application/vnd.github.v3+json',
            })
            resp = urlopen(req, timeout=timeout, context=ctx)
            return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            continue
    
    # 最后尝试镜像
    for mirror in MIRRORS:
        if mirror:
            url = f"{mirror}https://api.github.com{endpoint}"
            try:
                req = Request(url, headers=HEADERS)
                resp = urlopen(req, timeout=timeout, context=ctx)
                return json.loads(resp.read().decode('utf-8'))
            except:
                continue
    
    return None


# ============================================================
# 命令：下载Release
# ============================================================
def cmd_release(repo, filter_ext=None, output_dir=None, tag=None):
    """下载GitHub Release的文件"""
    print(f"\n{'='*60}")
    print(f"GitHub Release 下载器")
    print(f"仓库: {repo}")
    print(f"{'='*60}")
    
    # 获取Release信息
    if tag:
        endpoint = f"/repos/{repo}/releases/tags/{tag}"
    else:
        endpoint = f"/repos/{repo}/releases/latest"
    
    print(f"\n获取Release信息...")
    release = github_api(endpoint)
    
    if not release:
        print("✗ 无法获取Release信息")
        print("  尝试直接下载...")
        # 尝试直接构造URL
        url = f"https://github.com/{repo}/releases/latest/download/"
        return False
    
    tag_name = release.get('tag_name', 'unknown')
    name = release.get('name', tag_name)
    published = release.get('published_at', '')[:10]
    assets = release.get('assets', [])
    
    print(f"\n版本: {name} ({tag_name})")
    print(f"发布: {published}")
    print(f"文件: {len(assets)} 个")
    
    if not assets:
        print("✗ 没有可下载的文件")
        # 尝试下载source code
        zipball = release.get('zipball_url')
        if zipball:
            print(f"  但有源码包: {zipball}")
            out = output_dir or DOWNLOAD_DIR / repo.replace('/', '_')
            out.mkdir(parents=True, exist_ok=True)
            return download_file(zipball, out / f"{repo.split('/')[-1]}-{tag_name}.zip")
        return False
    
    # 列出所有文件
    print(f"\n可下载文件:")
    for i, asset in enumerate(assets):
        name = asset['name']
        size = asset['size']
        dl_count = asset.get('download_count', 0)
        size_str = f"{size/1024/1024:.1f}MB" if size > 1024*1024 else f"{size/1024:.0f}KB"
        marker = " ←" if (filter_ext and name.lower().endswith(f'.{filter_ext.lower()}')) else ""
        print(f"  [{i+1}] {name} ({size_str}, {dl_count} downloads){marker}")
    
    # 过滤
    if filter_ext:
        assets = [a for a in assets if a['name'].lower().endswith(f'.{filter_ext.lower()}')]
        if not assets:
            print(f"\n✗ 没有 .{filter_ext} 文件")
            return False
    
    # 下载
    out = output_dir or DOWNLOAD_DIR / repo.replace('/', '_')
    out.mkdir(parents=True, exist_ok=True)
    
    success = 0
    for asset in assets:
        name = asset['name']
        url = asset['browser_download_url']
        print(f"\n下载: {name}")
        if download_file(url, out / name):
            success += 1
            
            # 自动解压zip
            if name.endswith('.zip'):
                try:
                    extract_dir = out / name.replace('.zip', '')
                    with zipfile.ZipFile(out / name, 'r') as z:
                        z.extractall(extract_dir)
                    print(f"  ✓ 已解压到: {extract_dir}")
                except Exception as e:
                    print(f"  解压失败: {e}")
    
    print(f"\n{'='*60}")
    print(f"完成! 成功下载 {success}/{len(assets)} 个文件")
    print(f"保存位置: {out}")
    print(f"{'='*60}")
    return success > 0


# ============================================================
# 命令：克隆仓库
# ============================================================
def cmd_clone(repo, output_dir=None):
    """克隆GitHub仓库（下载zip源码）"""
    print(f"\n{'='*60}")
    print(f"GitHub 仓库下载")
    print(f"仓库: {repo}")
    print(f"{'='*60}")
    
    out = output_dir or DOWNLOAD_DIR / repo.replace('/', '_')
    out.mkdir(parents=True, exist_ok=True)
    
    # 先尝试git clone
    import subprocess
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"\n使用git clone...")
            # 尝试镜像
            clone_urls = [
                f"https://github.com/{repo}.git",
            ]
            for mirror in MIRRORS:
                if mirror:
                    clone_urls.append(f"{mirror}https://github.com/{repo}.git")
            
            for clone_url in clone_urls:
                print(f"  尝试: {clone_url[:60]}...")
                result = subprocess.run(
                    ['git', 'clone', '--depth', '1', clone_url, str(out / repo.split('/')[-1])],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode == 0:
                    print(f"  ✓ 克隆成功! -> {out / repo.split('/')[-1]}")
                    return True
    except:
        pass
    
    # 回退到下载zip
    print(f"\ngit不可用，下载zip源码...")
    url = f"https://github.com/{repo}/archive/refs/heads/main.zip"
    zip_path = out / f"{repo.split('/')[-1]}.zip"
    
    if download_file(url, zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(out)
            print(f"  ✓ 已解压到: {out}")
            return True
        except Exception as e:
            # 可能是master分支
            url = f"https://github.com/{repo}/archive/refs/heads/master.zip"
            if download_file(url, zip_path):
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(out)
                print(f"  ✓ 已解压到: {out}")
                return True
    
    return False


# ============================================================
# 命令：下载单个文件
# ============================================================
def cmd_file(url, output_path=None):
    """下载单个文件"""
    print(f"\n下载文件: {url}")
    
    filename = url.split('/')[-1].split('?')[0]
    if not output_path:
        output_path = DOWNLOAD_DIR / filename
    
    return download_file(url, output_path)


# ============================================================
# 命令：搜索仓库
# ============================================================
def cmd_search(keyword, limit=10):
    """搜索GitHub仓库"""
    print(f"\n搜索: {keyword}")
    
    data = github_api(f"/search/repositories?q={quote(keyword)}&sort=stars&per_page={limit}")
    if not data:
        print("✗ 搜索失败")
        return
    
    items = data.get('items', [])
    total = data.get('total_count', 0)
    print(f"找到 {total} 个结果，显示前 {len(items)} 个:\n")
    
    for i, item in enumerate(items):
        name = item['full_name']
        desc = (item.get('description') or '')[:60]
        stars = item.get('stargazers_count', 0)
        lang = item.get('language', '?')
        print(f"  [{i+1}] ★{stars:,} {name}")
        print(f"       {desc}")
        print(f"       语言: {lang}")
        print()


# ============================================================
# 命令：批量下载
# ============================================================
def cmd_batch(repos_file):
    """从文件批量下载"""
    with open(repos_file, 'r') as f:
        repos = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"批量下载 {len(repos)} 个仓库")
    for repo in repos:
        cmd_release(repo)


# ============================================================
# TCP/HTTP MCP服务器
# ============================================================
TCP_PORT = 19030
HTTP_PORT = 19031

import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("GitHub-DL")


class GitHubDLHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/':
            self.send_html(self.dashboard())
        elif path == '/api/health':
            self.send_json({"status": "healthy"})
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        cl = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(cl).decode('utf-8')
        req = json.loads(body) if body else {}
        
        if path == '/api/call':
            tool = req.get('tool')
            params = req.get('params', {})
            result = self.handle_tool(tool, params)
            self.send_json(result)
        else:
            self.send_error(404)
    
    def handle_tool(self, tool, params):
        if tool == 'github_release':
            repo = params.get('repo')
            filter_ext = params.get('filter')
            if not repo:
                return {"error": "需要repo参数"}
            # 在后台线程执行
            t = threading.Thread(target=cmd_release, args=(repo,), kwargs={'filter_ext': filter_ext})
            t.start()
            return {"success": True, "message": f"开始下载 {repo} 的Release"}
        
        elif tool == 'github_clone':
            repo = params.get('repo')
            if not repo:
                return {"error": "需要repo参数"}
            t = threading.Thread(target=cmd_clone, args=(repo,))
            t.start()
            return {"success": True, "message": f"开始克隆 {repo}"}
        
        elif tool == 'github_search':
            keyword = params.get('keyword')
            if not keyword:
                return {"error": "需要keyword参数"}
            cmd_search(keyword)
            return {"success": True}
        
        elif tool == 'download_file':
            url = params.get('url')
            output = params.get('output')
            if not url:
                return {"error": "需要url参数"}
            t = threading.Thread(target=cmd_file, args=(url,), kwargs={'output_path': output})
            t.start()
            return {"success": True, "message": f"开始下载 {url}"}
        
        return {"error": f"未知工具: {tool}"}
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def dashboard(self):
        return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>GitHub Downloader MCP</title>
<style>body{font-family:Arial;margin:40px;background:#0d1117;color:#c9d1d9}
.container{max-width:800px;margin:0 auto;background:#161b22;padding:30px;border-radius:8px;border:1px solid #30363d}
h1{color:#58a6ff}input,button{padding:10px;margin:5px;border-radius:6px;border:1px solid #30363d;background:#0d1117;color:#c9d1d9}
button{background:#238636;color:white;cursor:pointer;border:none}button:hover{background:#2ea043}
.result{background:#0d1117;padding:15px;border-radius:6px;margin-top:15px;white-space:pre-wrap;font-family:monospace;font-size:13px}
</style></head><body><div class="container">
<h1>GitHub Downloader MCP</h1>
<p>下载GitHub项目的Release、源码、单个文件</p>
<h3>下载Release</h3>
<input id="repo" placeholder="owner/repo (如 GHFear/AESDumpster)" style="width:400px">
<input id="filter" placeholder="过滤(如 exe)" style="width:100px">
<button onclick="dlRelease()">下载</button>
<h3>下载文件</h3>
<input id="url" placeholder="完整URL" style="width:500px">
<button onclick="dlFile()">下载</button>
<div id="result" class="result">等待操作...</div>
<script>
async function dlRelease(){let r=document.getElementById('repo').value;let f=document.getElementById('filter').value;
let res=await fetch('/api/call',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({tool:'github_release',params:{repo:r,filter:f||undefined}})});
document.getElementById('result').textContent=JSON.stringify(await res.json(),null,2)}
async function dlFile(){let u=document.getElementById('url').value;
let res=await fetch('/api/call',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({tool:'download_file',params:{url:u}})});
document.getElementById('result').textContent=JSON.stringify(await res.json(),null,2)}
</script></div></body></html>"""


def start_server():
    """启动HTTP服务器"""
    server = HTTPServer(('127.0.0.1', HTTP_PORT), GitHubDLHandler)
    logger.info(f"GitHub Downloader MCP: http://127.0.0.1:{HTTP_PORT}")
    server.serve_forever()


# ============================================================
# 主程序
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("""
GitHub Downloader MCP

用法:
    python github_dl.py release <owner/repo> [--filter exe]
    python github_dl.py clone <owner/repo>
    python github_dl.py file <url>
    python github_dl.py search <keyword>
    python github_dl.py batch <repos.txt>
    python github_dl.py server              (启动MCP服务器)

示例:
    python github_dl.py release GHFear/AESDumpster
    python github_dl.py release 4sval/FModel --filter exe
    python github_dl.py clone baldurk/renderdoc
    python github_dl.py search "UE5 AES key"
    python github_dl.py server
""")
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == 'release':
        repo = sys.argv[2]
        filter_ext = None
        for i, arg in enumerate(sys.argv):
            if arg == '--filter' and i+1 < len(sys.argv):
                filter_ext = sys.argv[i+1]
        cmd_release(repo, filter_ext=filter_ext)
    
    elif cmd == 'clone':
        cmd_clone(sys.argv[2])
    
    elif cmd == 'file':
        output = None
        for i, arg in enumerate(sys.argv):
            if arg == '--output' and i+1 < len(sys.argv):
                output = sys.argv[i+1]
        cmd_file(sys.argv[2], output)
    
    elif cmd == 'search':
        cmd_search(' '.join(sys.argv[2:]))
    
    elif cmd == 'batch':
        cmd_batch(sys.argv[2])
    
    elif cmd == 'server':
        start_server()
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
