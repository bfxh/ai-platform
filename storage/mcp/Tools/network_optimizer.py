#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Optimizer MCP - 网络优化工具

功能：
- 代理测试和管理
- DNS测速和优化
- 网络诊断
- 网速测试
- 路由追踪
- CDN测速
- 连接优化

用法：
    python network_optimizer.py <action> [args...]

示例：
    python network_optimizer.py proxy test <proxy_url>
    python network_optimizer.py dns benchmark
    python network_optimizer.py diagnose <host>
    python network_optimizer.py speedtest
    python network_optimizer.py trace <host>
    python network_optimizer.py cdn test <url>
"""

import json
import sys
import os
import subprocess
import socket
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error

# ============================================================
# 配置
# ============================================================
CONFIG = {
    "dns_servers": [
        "8.8.8.8",        # Google
        "1.1.1.1",        # Cloudflare
        "223.5.5.5",      # AliDNS
        "119.29.29.29",   # DNSPod
        "114.114.114.114", # 114DNS
    ],
    "timeout": 5,
    "retry_count": 3
}

# ============================================================
# 工具函数
# ============================================================
def ping_host(host: str, count: int = 4) -> Dict:
    """Ping主机"""
    try:
        result = subprocess.run(
            ["ping", "-n", str(count), host],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        
        # 解析结果
        if result.returncode == 0:
            # 提取平均延迟
            avg_match = re.search(r"平均\s*=\s*(\d+)ms", output)
            if not avg_match:
                avg_match = re.search(r"Average\s*=\s*(\d+)ms", output)
            
            avg_latency = int(avg_match.group(1)) if avg_match else 0
            
            # 提取丢包率
            loss_match = re.search(r"(\d+)%", output)
            loss_rate = int(loss_match.group(1)) if loss_match else 0
            
            return {
                "success": True,
                "host": host,
                "avg_latency": avg_latency,
                "loss_rate": loss_rate,
                "output": output
            }
        else:
            return {
                "success": False,
                "host": host,
                "error": "Ping failed",
                "output": output
            }
    except Exception as e:
        return {
            "success": False,
            "host": host,
            "error": str(e)
        }

def test_dns_server(server: str, domain: str = "www.google.com") -> Dict:
    """测试DNS服务器"""
    try:
        import dns.resolver
        
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [server]
        resolver.timeout = CONFIG["timeout"]
        
        start_time = time.time()
        answers = resolver.resolve(domain, "A")
        elapsed = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "server": server,
            "domain": domain,
            "response_time": round(elapsed, 2),
            "records": [str(rdata) for rdata in answers]
        }
    except Exception as e:
        return {
            "success": False,
            "server": server,
            "error": str(e)
        }

def test_proxy(proxy_url: str, target: str = "https://www.google.com") -> Dict:
    """测试代理"""
    try:
        proxy_handler = urllib.request.ProxyHandler({
            "http": proxy_url,
            "https": proxy_url
        })
        opener = urllib.request.build_opener(proxy_handler)
        
        start_time = time.time()
        response = opener.open(target, timeout=CONFIG["timeout"])
        elapsed = time.time() - start_time
        
        return {
            "success": True,
            "proxy": proxy_url,
            "target": target,
            "response_time": round(elapsed * 1000, 2),
            "status": response.getcode()
        }
    except Exception as e:
        return {
            "success": False,
            "proxy": proxy_url,
            "error": str(e)
        }

def trace_route(host: str, max_hops: int = 30) -> List[Dict]:
    """路由追踪"""
    hops = []
    
    try:
        result = subprocess.run(
            ["tracert", "-d", "-h", str(max_hops), host],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        lines = result.stdout.split("\n")
        for line in lines:
            # 解析每一跳
            match = re.search(r"(\d+)\s+(\d+)\s+ms\s+(\d+)\s+ms\s+(\d+)\s+ms\s+(.+)", line)
            if match:
                hop_num = int(match.group(1))
                latency1 = int(match.group(2))
                latency2 = int(match.group(3))
                latency3 = int(match.group(4))
                ip = match.group(5).strip()
                
                hops.append({
                    "hop": hop_num,
                    "ip": ip,
                    "latency": round((latency1 + latency2 + latency3) / 3, 2)
                })
        
        return hops
    except Exception as e:
        return [{"error": str(e)}]

def speed_test() -> Dict:
    """网速测试"""
    # 简化的网速测试
    test_urls = [
        "https://speed.cloudflare.com/__down?bytes=10000000",  # 10MB
        "https://speed.cloudflare.com/__up?bytes=1000000"       # 1MB
    ]
    
    results = {
        "download_speed": 0,
        "upload_speed": 0,
        "latency": 0
    }
    
    # 测试下载速度
    try:
        start_time = time.time()
        response = urllib.request.urlopen(test_urls[0], timeout=30)
        data = response.read()
        elapsed = time.time() - start_time
        
        if elapsed > 0:
            speed_bps = len(data) * 8 / elapsed
            results["download_speed"] = round(speed_bps / 1000000, 2)  # Mbps
    except:
        pass
    
    # 测试延迟
    try:
        start_time = time.time()
        response = urllib.request.urlopen("https://www.google.com", timeout=5)
        elapsed = time.time() - start_time
        results["latency"] = round(elapsed * 1000, 2)
    except:
        pass
    
    return results

# ============================================================
# 网络优化器
# ============================================================
class NetworkOptimizer:
    """网络优化器"""
    
    def __init__(self):
        pass
    
    def benchmark_dns(self, params: Dict) -> Dict:
        """DNS测速"""
        servers = params.get("servers", CONFIG["dns_servers"])
        test_domain = params.get("test_domain", "www.google.com")
        count = params.get("count", 10)
        
        results = []
        for server in servers:
            times = []
            for _ in range(count):
                result = test_dns_server(server, test_domain)
                if result.get("success"):
                    times.append(result["response_time"])
            
            if times:
                results.append({
                    "server": server,
                    "avg_time": round(sum(times) / len(times), 2),
                    "min_time": round(min(times), 2),
                    "max_time": round(max(times), 2),
                    "success_rate": len(times) / count * 100
                })
        
        # 排序
        results.sort(key=lambda x: x["avg_time"])
        
        return {
            "success": True,
            "results": results,
            "best_server": results[0]["server"] if results else None
        }
    
    def test_proxy(self, params: Dict) -> Dict:
        """测试代理"""
        proxy_url = params.get("proxy_url")
        target = params.get("target", "https://www.google.com")
        
        if not proxy_url:
            return {"success": False, "error": "Proxy URL is required"}
        
        return test_proxy(proxy_url, target)
    
    def diagnose(self, params: Dict) -> Dict:
        """网络诊断"""
        target = params.get("target")
        port = params.get("port", 80)
        
        if not target:
            return {"success": False, "error": "Target is required"}
        
        results = {
            "target": target,
            "tests": {}
        }
        
        # DNS解析测试
        try:
            ip = socket.gethostbyname(target)
            results["tests"]["dns"] = {
                "success": True,
                "ip": ip
            }
        except Exception as e:
            results["tests"]["dns"] = {
                "success": False,
                "error": str(e)
            }
        
        # Ping测试
        results["tests"]["ping"] = ping_host(target)
        
        # 端口连通性测试
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((target, port))
            sock.close()
            
            results["tests"]["port"] = {
                "success": result == 0,
                "port": port,
                "open": result == 0
            }
        except Exception as e:
            results["tests"]["port"] = {
                "success": False,
                "error": str(e)
            }
        
        # HTTP测试
        try:
            url = f"http://{target}:{port}" if port != 80 else f"http://{target}"
            response = urllib.request.urlopen(url, timeout=10)
            results["tests"]["http"] = {
                "success": True,
                "status": response.getcode()
            }
        except Exception as e:
            results["tests"]["http"] = {
                "success": False,
                "error": str(e)
            }
        
        return {
            "success": True,
            **results
        }
    
    def speed_test(self, params: Dict = None) -> Dict:
        """网速测试"""
        return {
            "success": True,
            **speed_test()
        }
    
    def trace_route(self, params: Dict) -> Dict:
        """路由追踪"""
        host = params.get("host")
        max_hops = params.get("max_hops", 30)
        
        if not host:
            return {"success": False, "error": "Host is required"}
        
        hops = trace_route(host, max_hops)
        
        return {
            "success": True,
            "host": host,
            "hops": hops,
            "hop_count": len(hops)
        }

# ============================================================
# MCP 接口
# ============================================================
optimizer = NetworkOptimizer()

def mcp_benchmark_dns(params: Dict) -> Dict:
    """MCP DNS测速接口"""
    return optimizer.benchmark_dns(params)

def mcp_test_proxy(params: Dict) -> Dict:
    """MCP代理测试接口"""
    return optimizer.test_proxy(params)

def mcp_diagnose(params: Dict) -> Dict:
    """MCP诊断接口"""
    return optimizer.diagnose(params)

def mcp_speed_test(params: Dict = None) -> Dict:
    """MCP网速测试接口"""
    return optimizer.speed_test(params)

def mcp_trace_route(params: Dict) -> Dict:
    """MCP路由追踪接口"""
    return optimizer.trace_route(params)

# ============================================================
# 命令行接口
# ============================================================
def print_help():
    """打印帮助信息"""
    print(__doc__)
    print("\n命令:")
    print("  proxy test <url>             测试代理")
    print("  dns benchmark                DNS测速")
    print("  diagnose <host>              网络诊断")
    print("  speedtest                    网速测试")
    print("  trace <host>                 路由追踪")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action in ["--help", "-h", "help"]:
        print_help()
        sys.exit(0)
    
    if action == "proxy":
        if len(sys.argv) < 4:
            print("Usage: network_optimizer.py proxy test <proxy_url>")
            sys.exit(1)
        
        subcommand = sys.argv[2]
        if subcommand == "test":
            result = mcp_test_proxy({"proxy_url": sys.argv[3]})
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Unknown proxy subcommand: {subcommand}")
            sys.exit(1)
    
    elif action == "dns":
        if len(sys.argv) < 3:
            print("Usage: network_optimizer.py dns benchmark")
            sys.exit(1)
        
        subcommand = sys.argv[2]
        if subcommand == "benchmark":
            result = mcp_benchmark_dns({})
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Unknown dns subcommand: {subcommand}")
            sys.exit(1)
    
    elif action == "diagnose":
        if len(sys.argv) < 3:
            print("Usage: network_optimizer.py diagnose <host>")
            sys.exit(1)
        
        result = mcp_diagnose({"target": sys.argv[2]})
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "speedtest":
        result = mcp_speed_test()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "trace":
        if len(sys.argv) < 3:
            print("Usage: network_optimizer.py trace <host>")
            sys.exit(1)
        
        result = mcp_trace_route({"host": sys.argv[2]})
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif action == "mcp":
        # MCP Server 模式
        for line in sys.stdin:
            try:
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                
                handlers = {
                    "benchmark_dns": mcp_benchmark_dns,
                    "test_proxy": mcp_test_proxy,
                    "diagnose": mcp_diagnose,
                    "speed_test": mcp_speed_test,
                    "trace_route": mcp_trace_route
                }
                
                handler = handlers.get(method)
                if handler:
                    result = handler(params)
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
