#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Net Pro MCP - 增强网络工具

在原有Network MCP基础上增加实用的高级功能：

1. 网页抓取 - 抓取网页内容/标题/链接
2. API调用 - 快速调用REST API
3. 批量下载 - 多线程批量下载文件
4. 网速测试 - 测试上传下载速度
5. 代理检测 - 检测代理可用性
6. 域名信息 - WHOIS/DNS全记录
7. 网站监控 - 定时检测网站状态
8. 端口转发 - 简单TCP端口转发
9. 局域网扫描 - 发现局域网设备
10. HTTP服务器 - 一键启动文件共享

用法：
    python net_pro.py <action> [args...]

示例：
    python net_pro.py fetch https://example.com
    python net_pro.py api GET https://api.github.com/repos/4sval/FModel
    python net_pro.py download https://example.com/file.zip D:/output/
    python net_pro.py batch_dl urls.txt D:/output/
    python net_pro.py speed
    python net_pro.py scan_lan
    python net_pro.py serve D:/share 8080
    python net_pro.py whois example.com
    python net_pro.py monitor https://example.com 60
    python net_pro.py proxy_check http://proxy:8080
    python net_pro.py headers https://example.com
    python net_pro.py cert example.com
    python net_pro.py ip
"""

import json
import sys
import os
import ssl
import socket
import struct
import subprocess
import threading
import time
import re
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import HTTPServer, SimpleHTTPRequestHandler

import sys
sys.path.insert(0, r"\python")
from core.secure_utils import create_ssl_context

DOWNLOAD_DIR = Path("D:/搞阶跃的/Downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

ctx = create_ssl_context()

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


# ============================================================
# 1. 网页抓取
# ============================================================
def fetch(url, output=None):
    """抓取网页内容"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        data = resp.read()
        charset = resp.headers.get_content_charset() or 'utf-8'
        text = data.decode(charset, errors='ignore')
        
        # 提取标题
        title_match = re.search(r'<title[^>]*>(.*?)</title>', text, re.I | re.S)
        title = title_match.group(1).strip() if title_match else ""
        
        # 提取链接
        links = re.findall(r'href=["\']([^"\']+)["\']', text)
        
        # 提取文本（去HTML标签）
        clean = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.S)
        clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.S)
        clean = re.sub(r'<[^>]+>', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        result = {
            "url": url,
            "status": resp.status,
            "title": title,
            "content_length": len(data),
            "links_count": len(links),
            "text_preview": clean[:500],
        }
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(text)
            result["saved"] = output
        
        print(f"fetch: {url}")
        print(f"  title: {title}")
        print(f"  status: {resp.status}")
        print(f"  size: {len(data)} bytes")
        print(f"  links: {len(links)}")
        print(f"  text: {clean[:200]}...")
        
        return result
    except Exception as e:
        print(f"fetch error: {e}")
        return {"error": str(e)}


# ============================================================
# 2. API调用
# ============================================================
def api_call(method, url, data=None, headers=None):
    """调用REST API"""
    h = {'User-Agent': UA, 'Accept': 'application/json'}
    if headers:
        h.update(headers)
    
    body = None
    if data:
        if isinstance(data, dict):
            body = json.dumps(data).encode('utf-8')
            h['Content-Type'] = 'application/json'
        else:
            body = data.encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=body, headers=h, method=method.upper())
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        resp_data = resp.read().decode('utf-8', errors='ignore')
        
        try:
            result = json.loads(resp_data)
        except:
            result = resp_data
        
        print(f"API {method.upper()} {url}")
        print(f"  status: {resp.status}")
        if isinstance(result, dict):
            print(f"  response: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
        else:
            print(f"  response: {str(result)[:500]}")
        
        return {"status": resp.status, "data": result}
    except Exception as e:
        print(f"API error: {e}")
        return {"error": str(e)}


# ============================================================
# 3. 文件下载（断点续传+进度）
# ============================================================
def download(url, output_dir=None, filename=None):
    """下载文件，支持断点续传"""
    if output_dir is None:
        output_dir = str(DOWNLOAD_DIR)
    os.makedirs(output_dir, exist_ok=True)
    
    if filename is None:
        filename = url.split('/')[-1].split('?')[0] or "download"
    
    filepath = os.path.join(output_dir, filename)
    
    # 检查已下载大小
    downloaded = 0
    if os.path.exists(filepath):
        downloaded = os.path.getsize(filepath)
    
    headers = {'User-Agent': UA}
    if downloaded > 0:
        headers['Range'] = f'bytes={downloaded}-'
    
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=30, context=ctx)
        
        total = resp.headers.get('Content-Length')
        total = int(total) + downloaded if total else None
        
        mode = 'ab' if downloaded > 0 else 'wb'
        
        print(f"download: {url}")
        print(f"  -> {filepath}")
        if total:
            print(f"  size: {total/1024/1024:.1f}MB (resumed from {downloaded/1024/1024:.1f}MB)")
        
        with open(filepath, mode) as f:
            chunk_size = 64 * 1024
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    sys.stdout.write(f"\r  progress: {pct:.1f}% ({downloaded/1024/1024:.1f}MB)")
                    sys.stdout.flush()
        
        print(f"\n  done: {downloaded/1024/1024:.1f}MB -> {filepath}")
        return {"success": True, "path": filepath, "size": downloaded}
    except Exception as e:
        print(f"download error: {e}")
        return {"error": str(e)}


# ============================================================
# 4. 批量下载
# ============================================================
def batch_download(urls_or_file, output_dir=None, workers=4):
    """批量下载"""
    if os.path.isfile(urls_or_file):
        with open(urls_or_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    elif isinstance(urls_or_file, list):
        urls = urls_or_file
    else:
        urls = [urls_or_file]
    
    if output_dir is None:
        output_dir = str(DOWNLOAD_DIR)
    
    print(f"batch download: {len(urls)} files, {workers} workers")
    
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(download, url, output_dir): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({"url": url, "error": str(e)})
    
    success = sum(1 for r in results if r.get("success"))
    print(f"\nbatch done: {success}/{len(urls)} succeeded")
    return results


# ============================================================
# 5. 网速测试
# ============================================================
def speed_test():
    """简单网速测试"""
    # 下载测试
    test_urls = [
        "http://speedtest.tele2.net/1MB.zip",
        "http://speedtest.tele2.net/10MB.zip",
    ]
    
    print("speed test:")
    
    for url in test_urls:
        size_name = url.split('/')[-1]
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            start = time.time()
            resp = urllib.request.urlopen(req, timeout=30, context=ctx)
            data = resp.read()
            elapsed = time.time() - start
            
            speed_mbps = (len(data) * 8) / elapsed / 1000000
            print(f"  {size_name}: {len(data)/1024/1024:.1f}MB in {elapsed:.1f}s = {speed_mbps:.1f} Mbps")
        except Exception as e:
            print(f"  {size_name}: failed ({e})")


# ============================================================
# 6. 局域网扫描
# ============================================================
def scan_lan(subnet=None, timeout=1):
    """扫描局域网设备"""
    if subnet is None:
        # 自动获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
        finally:
            s.close()
        subnet = '.'.join(local_ip.split('.')[:3])
    
    print(f"scanning {subnet}.0/24...")
    
    devices = []
    
    def ping_host(ip):
        result = subprocess.run(
            ['ping', '-n', '1', '-w', str(timeout * 1000), ip],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            # 尝试获取主机名
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = ""
            return {"ip": ip, "hostname": hostname, "alive": True}
        return None
    
    with ThreadPoolExecutor(max_workers=50) as pool:
        futures = {pool.submit(ping_host, f"{subnet}.{i}"): i for i in range(1, 255)}
        for future in as_completed(futures):
            result = future.result()
            if result:
                devices.append(result)
                print(f"  {result['ip']:15s} {result['hostname']}")
    
    devices.sort(key=lambda d: [int(x) for x in d['ip'].split('.')])
    print(f"\nfound {len(devices)} devices")
    return devices


# ============================================================
# 7. HTTP文件服务器
# ============================================================
def serve(directory=".", port=8080):
    """一键启动HTTP文件共享服务器"""
    os.chdir(directory)
    
    # 获取本机IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    
    print(f"serving {directory}")
    print(f"  local:   http://127.0.0.1:{port}")
    print(f"  network: http://{local_ip}:{port}")
    print(f"  press Ctrl+C to stop")
    
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()


# ============================================================
# 8. SSL证书信息
# ============================================================
def cert_info(hostname, port=443):
    """获取SSL证书信息"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                
                subject = dict(x[0] for x in cert.get('subject', []))
                issuer = dict(x[0] for x in cert.get('issuer', []))
                
                not_before = cert.get('notBefore', '')
                not_after = cert.get('notAfter', '')
                
                # 解析过期时间
                try:
                    expire = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                    days_left = (expire - datetime.utcnow()).days
                except:
                    days_left = -1
                
                sans = []
                for san_type, san_value in cert.get('subjectAltName', []):
                    sans.append(san_value)
                
                info = {
                    "hostname": hostname,
                    "subject": subject,
                    "issuer": issuer,
                    "not_before": not_before,
                    "not_after": not_after,
                    "days_left": days_left,
                    "sans": sans[:10],
                    "version": cert.get('version'),
                    "serial": cert.get('serialNumber'),
                }
                
                print(f"cert: {hostname}")
                print(f"  subject: {subject.get('commonName', 'N/A')}")
                print(f"  issuer: {issuer.get('organizationName', 'N/A')}")
                print(f"  expires: {not_after} ({days_left} days left)")
                print(f"  SANs: {', '.join(sans[:5])}")
                
                return info
    except Exception as e:
        print(f"cert error: {e}")
        return {"error": str(e)}


# ============================================================
# 9. HTTP Headers
# ============================================================
def get_headers(url):
    """获取HTTP响应头"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA}, method='HEAD')
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        
        print(f"headers: {url}")
        print(f"  status: {resp.status}")
        for key, value in resp.headers.items():
            print(f"  {key}: {value}")
        
        return dict(resp.headers)
    except Exception as e:
        print(f"headers error: {e}")
        return {"error": str(e)}


# ============================================================
# 10. 公网IP
# ============================================================
def my_ip():
    """获取公网和内网IP"""
    # 内网IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    
    # 公网IP
    public_ip = "unknown"
    for url in ['https://api.ipify.org', 'https://ifconfig.me/ip', 'https://icanhazip.com']:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            resp = urllib.request.urlopen(req, timeout=5, context=ctx)
            public_ip = resp.read().decode('utf-8', errors='ignore').strip()
            break
        except:
            continue
    
    print(f"IP:")
    print(f"  local:  {local_ip}")
    print(f"  public: {public_ip}")
    
    return {"local": local_ip, "public": public_ip}


# ============================================================
# 11. 网站监控
# ============================================================
def monitor_site(url, interval=60, count=0):
    """定时检测网站状态"""
    print(f"monitoring: {url} every {interval}s")
    
    i = 0
    while count == 0 or i < count:
        try:
            start = time.time()
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            resp = urllib.request.urlopen(req, timeout=10, context=ctx)
            elapsed = (time.time() - start) * 1000
            
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"  [{ts}] {resp.status} {elapsed:.0f}ms")
        except Exception as e:
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"  [{ts}] ERROR: {e}")
        
        i += 1
        if count == 0 or i < count:
            time.sleep(interval)


# ============================================================
# CLI
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("""Net Pro MCP - 增强网络工具

用法: python net_pro.py <action> [args...]

动作:
  fetch <url> [output]          抓取网页
  api <METHOD> <url> [data]     调用API
  download <url> [dir] [name]   下载文件
  batch_dl <file|url> [dir]     批量下载
  speed                         网速测试
  scan_lan [subnet]             局域网扫描
  serve [dir] [port]            文件共享服务器
  cert <hostname>               SSL证书信息
  headers <url>                 HTTP响应头
  ip                            公网/内网IP
  monitor <url> [interval]      网站监控""")
        return
    
    action = sys.argv[1]
    args = sys.argv[2:]
    
    if action == "fetch":
        fetch(args[0], args[1] if len(args) > 1 else None)
    elif action == "api":
        data = json.loads(args[2]) if len(args) > 2 else None
        api_call(args[0], args[1], data)
    elif action == "download":
        download(args[0], args[1] if len(args) > 1 else None, args[2] if len(args) > 2 else None)
    elif action == "batch_dl":
        batch_download(args[0], args[1] if len(args) > 1 else None)
    elif action == "speed":
        speed_test()
    elif action == "scan_lan":
        scan_lan(args[0] if args else None)
    elif action == "serve":
        serve(args[0] if args else ".", int(args[1]) if len(args) > 1 else 8080)
    elif action == "cert":
        cert_info(args[0])
    elif action == "headers":
        get_headers(args[0])
    elif action == "ip":
        my_ip()
    elif action == "monitor":
        monitor_site(args[0], int(args[1]) if len(args) > 1 else 60, int(args[2]) if len(args) > 2 else 0)
    else:
        print(f"未知动作: {action}")


if __name__ == '__main__':
    main()
