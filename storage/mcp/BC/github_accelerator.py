#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 自动加速器

功能：
- 自动检测 GitHub 访问速度
- 智能选择最快的镜像节点
- 自动修改 hosts 文件加速
- 支持 GitHub 网页、API、Git 操作加速
- 自动恢复原始 hosts
- 定时检测和切换

用法：
    python github_accelerator.py check           # 检测当前速度
    python github_accelerator.py speed           # 测试各节点速度
    python github_accelerator.py apply           # 应用最佳加速
    python github_accelerator.py auto            # 自动检测并应用
    python github_accelerator.py restore         # 恢复原始 hosts
    python github_accelerator.py status          # 查看当前状态
    python github_accelerator.py schedule        # 定时自动优化

MCP调用：
    {"tool": "github_accelerator", "action": "auto"}
"""

import json
import sys
import os
import subprocess
import time
import socket
import ssl
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# ============================================================
# 配置
# ============================================================
import sys
sys.path.insert(0, r"\python")
from core.secure_utils import create_ssl_context

AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
CONFIG_PATH = AI_PATH / "MCP_Skills"

# Hosts 文件路径
HOSTS_FILE = Path("C:/Windows/System32/drivers/etc/hosts")
HOSTS_BACKUP = CONFIG_PATH / "hosts.backup"

# GitHub 域名列表
GITHUB_DOMAINS = [
    "github.com",
    "www.github.com",
    "api.github.com",
    "raw.githubusercontent.com",
    "user-images.githubusercontent.com",
    "camo.githubusercontent.com",
    "avatars.githubusercontent.com",
    "avatars0.githubusercontent.com",
    "avatars1.githubusercontent.com",
    "avatars2.githubusercontent.com",
    "avatars3.githubusercontent.com",
    "github.githubassets.com",
    "central.github.com",
    "desktop.githubusercontent.com",
    "assets-cdn.github.com",
    "github.global.ssl.fastly.net",
    "gist.github.com",
    "codeload.github.com",
    "releases.github.com",
    "uploads.github.com",
    "status.github.com",
    "github.io",
    "githubapp.com",
    "github.dev",
    "githubusercontent.com",
]

# GitHub 镜像节点
GITHUB_MIRRORS = {
    "fastgit": {
        "name": "FastGit",
        "domains": {
            "github.com": "hub.fastgit.xyz",
            "raw.githubusercontent.com": "raw.fastgit.org",
        },
        "description": "FastGit 镜像"
    },
    "ghproxy": {
        "name": "GHProxy",
        "url": "https://ghproxy.com/",
        "description": "GHProxy 代理"
    },
    "jsdelivr": {
        "name": "JSDelivr",
        "url": "https://cdn.jsdelivr.net/gh/",
        "description": "JSDelivr CDN"
    },
    "staticaly": {
        "name": "Staticaly",
        "url": "https://cdn.staticaly.com/gh/",
        "description": "Staticaly CDN"
    },
    "kgithub": {
        "name": "KGitHub",
        "domains": {
            "github.com": "github.akams.cn",
        },
        "description": "KGitHub 镜像"
    },
    "cnpmjs": {
        "name": "CNPMJS",
        "domains": {
            "github.com": "github.com.cnpmjs.org",
        },
        "description": "CNPMJS 镜像"
    },
}

# IP 加速节点（定期更新）
GITHUB_IPS = {
    "140.82.113.3": "美国",
    "140.82.113.4": "美国",
    "140.82.114.3": "美国",
    "140.82.114.4": "美国",
    "140.82.116.3": "美国",
    "140.82.116.4": "美国",
    "140.82.121.3": "美国",
    "140.82.121.4": "美国",
    "20.205.243.166": "新加坡",
    "20.27.177.113": "日本",
    "20.200.245.247": "澳大利亚",
}

# 配置文件
CONFIG_FILE = CONFIG_PATH / "github_accelerator.json"

# ============================================================
# GitHub 加速器
# ============================================================
class GitHubAccelerator:
    """GitHub 加速器"""
    
    def __init__(self):
        self.config = self._load_config()
        self.current_hosts = self._read_hosts()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        default_config = {
            "enabled": True,
            "auto_apply": True,
            "test_timeout": 5,
            "preferred_method": "hosts",  # hosts, proxy, mirror
            "custom_ips": {},
            "last_apply": None,
            "speed_results": {}
        }
        
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict):
        """保存配置"""
        CONFIG_PATH.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def _read_hosts(self) -> str:
        """读取 hosts 文件"""
        try:
            with open(HOSTS_FILE, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""
    
    def _write_hosts(self, content: str) -> bool:
        """写入 hosts 文件（需要管理员权限）"""
        try:
            # 备份原文件
            if HOSTS_FILE.exists():
                with open(HOSTS_FILE, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                with open(HOSTS_BACKUP, 'w', encoding='utf-8') as f:
                    f.write(backup_content)
            
            # 写入新内容
            with open(HOSTS_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 刷新 DNS 缓存
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)
            
            return True
        except Exception as e:
            print(f"写入 hosts 失败（需要管理员权限）: {e}")
            return False
    
    def test_speed(self, ip: str = None, domain: str = "github.com") -> Dict:
        """测试连接速度"""
        timeout = self.config.get("test_timeout", 5)
        
        try:
            start_time = time.time()
            
            if ip:
                # 测试特定 IP
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip, 443))
                sock.close()
                
                if result == 0:
                    # 测试 HTTP 响应
                    ctx = create_ssl_context()
                    
                    req = urllib.request.Request(
                        f"https://{domain}",
                        headers={'Host': domain, 'User-Agent': 'Mozilla/5.0'},
                        method='HEAD'
                    )
                    
                    # 使用 IP 连接
                    import socket
                    original_getaddrinfo = socket.getaddrinfo
                    
                    def getaddrinfo_wrapper(host, port, *args, **kwargs):
                        if host == domain:
                            return original_getaddrinfo(ip, port, *args, **kwargs)
                        return original_getaddrinfo(host, port, *args, **kwargs)
                    
                    socket.getaddrinfo = getaddrinfo_wrapper
                    
                    try:
                        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as response:
                            elapsed = time.time() - start_time
                            return {
                                "success": True,
                                "ip": ip,
                                "domain": domain,
                                "latency_ms": round(elapsed * 1000, 2),
                                "status": response.status
                            }
                    finally:
                        socket.getaddrinfo = original_getaddrinfo
                else:
                    return {
                        "success": False,
                        "ip": ip,
                        "domain": domain,
                        "error": f"连接失败 (code: {result})"
                    }
            else:
                # 测试默认连接
                ctx = create_ssl_context()
                
                req = urllib.request.Request(
                    f"https://{domain}",
                    headers={'User-Agent': 'Mozilla/5.0'},
                    method='HEAD'
                )
                
                with urllib.request.urlopen(req, context=ctx, timeout=timeout) as response:
                    elapsed = time.time() - start_time
                    return {
                        "success": True,
                        "domain": domain,
                        "latency_ms": round(elapsed * 1000, 2),
                        "status": response.status
                    }
        
        except Exception as e:
            return {
                "success": False,
                "ip": ip,
                "domain": domain,
                "error": str(e)
            }
    
    def test_all_ips(self) -> List[Dict]:
        """测试所有 IP 节点"""
        print("测试 GitHub IP 节点速度...")
        
        results = []
        
        for ip, location in GITHUB_IPS.items():
            print(f"  测试 {ip} ({location})...", end=" ")
            result = self.test_speed(ip)
            
            if result.get("success"):
                print(f"✓ {result['latency_ms']}ms")
            else:
                print(f"✗ {result.get('error', '失败')}")
            
            results.append(result)
        
        # 按延迟排序
        results.sort(key=lambda x: x.get("latency_ms", float('inf')) if x.get("success") else float('inf'))
        
        return results
    
    def find_best_ip(self) -> Optional[str]:
        """找到最快的 IP"""
        results = self.test_all_ips()
        
        for result in results:
            if result.get("success"):
                return result["ip"]
        
        return None
    
    def apply_hosts_acceleration(self, ip: str = None) -> Dict:
        """应用 hosts 加速"""
        if not ip:
            print("寻找最佳 IP 节点...")
            ip = self.find_best_ip()
            
            if not ip:
                return {"success": False, "error": "未找到可用的 IP 节点"}
            
            print(f"最佳节点: {ip}")
        
        # 读取当前 hosts
        hosts_content = self._read_hosts()
        
        # 移除旧的 GitHub 加速配置
        lines = hosts_content.split('\n')
        new_lines = []
        in_github_section = False
        
        for line in lines:
            if '# GitHub Accelerator Start' in line:
                in_github_section = True
                continue
            if '# GitHub Accelerator End' in line:
                in_github_section = False
                continue
            if not in_github_section:
                new_lines.append(line)
        
        # 添加新的加速配置
        github_section = [
            "",
            "# GitHub Accelerator Start",
            f"# Applied at: {datetime.now().isoformat()}",
            f"# IP: {ip}",
        ]
        
        for domain in GITHUB_DOMAINS:
            github_section.append(f"{ip} {domain}")
        
        github_section.append("# GitHub Accelerator End")
        
        new_hosts = '\n'.join(new_lines + github_section)
        
        # 写入 hosts
        if self._write_hosts(new_hosts):
            # 保存配置
            self.config["last_apply"] = {
                "method": "hosts",
                "ip": ip,
                "time": datetime.now().isoformat()
            }
            self._save_config(self.config)
            
            return {
                "success": True,
                "method": "hosts",
                "ip": ip,
                "domains": len(GITHUB_DOMAINS),
                "message": "Hosts 加速已应用"
            }
        else:
            return {
                "success": False,
                "error": "写入 hosts 失败，请以管理员权限运行"
            }
    
    def restore_hosts(self) -> Dict:
        """恢复原始 hosts"""
        # 读取当前 hosts
        hosts_content = self._read_hosts()
        
        # 移除 GitHub 加速配置
        lines = hosts_content.split('\n')
        new_lines = []
        in_github_section = False
        
        for line in lines:
            if '# GitHub Accelerator Start' in line:
                in_github_section = True
                continue
            if '# GitHub Accelerator End' in line:
                in_github_section = False
                continue
            if not in_github_section:
                new_lines.append(line)
        
        new_hosts = '\n'.join(new_lines)
        
        # 写入 hosts
        if self._write_hosts(new_hosts):
            self.config["last_apply"] = None
            self._save_config(self.config)
            
            return {
                "success": True,
                "message": "Hosts 已恢复"
            }
        else:
            return {
                "success": False,
                "error": "恢复失败，请以管理员权限运行"
            }
    
    def get_mirror_url(self, original_url: str, mirror: str = "fastgit") -> str:
        """获取镜像 URL"""
        if mirror not in GITHUB_MIRRORS:
            return original_url
        
        mirror_config = GITHUB_MIRRORS[mirror]
        
        if "domains" in mirror_config:
            # 域名替换方式
            for original_domain, mirror_domain in mirror_config["domains"].items():
                if original_domain in original_url:
                    return original_url.replace(original_domain, mirror_domain)
        
        if "url" in mirror_config:
            # 代理前缀方式
            if "github.com" in original_url:
                # 提取仓库路径
                match = re.search(r'github\.com/([^/]+/[^/]+)', original_url)
                if match:
                    repo_path = match.group(1)
                    return f"{mirror_config['url']}{repo_path}"
        
        return original_url
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        hosts_content = self._read_hosts()
        
        # 检查是否已应用加速
        is_accelerated = '# GitHub Accelerator Start' in hosts_content
        
        # 获取当前 IP
        current_ip = None
        if is_accelerated:
            match = re.search(r'# IP: ([\d.]+)', hosts_content)
            if match:
                current_ip = match.group(1)
        
        # 测试当前速度
        speed_test = self.test_speed()
        
        return {
            "accelerated": is_accelerated,
            "current_ip": current_ip,
            "speed_test": speed_test,
            "last_apply": self.config.get("last_apply"),
            "mirrors": list(GITHUB_MIRRORS.keys())
        }
    
    def auto_optimize(self) -> Dict:
        """自动优化"""
        print("自动优化 GitHub 访问...")
        
        # 测试当前速度
        print("测试当前连接速度...")
        current_test = self.test_speed()
        
        if current_test.get("success") and current_test.get("latency_ms", 9999) < 500:
            print(f"当前连接良好 ({current_test['latency_ms']}ms)，无需优化")
            return {
                "success": True,
                "optimized": False,
                "reason": "当前连接良好",
                "current_latency": current_test.get("latency_ms")
            }
        
        # 应用加速
        print("应用加速...")
        result = self.apply_hosts_acceleration()
        
        if result.get("success"):
            # 测试加速后速度
            print("测试加速后速度...")
            new_test = self.test_speed()
            
            result["before_latency"] = current_test.get("latency_ms")
            result["after_latency"] = new_test.get("latency_ms") if new_test.get("success") else None
            result["optimized"] = True
        
        return result

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.accelerator = GitHubAccelerator()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "check":
            return self.accelerator.test_speed()
        
        elif action == "speed":
            return {
                "success": True,
                "results": self.accelerator.test_all_ips()
            }
        
        elif action == "apply":
            ip = params.get("ip")
            return self.accelerator.apply_hosts_acceleration(ip)
        
        elif action == "auto":
            return self.accelerator.auto_optimize()
        
        elif action == "restore":
            return self.accelerator.restore_hosts()
        
        elif action == "status":
            return self.accelerator.get_status()
        
        elif action == "mirror":
            url = params.get("url")
            mirror = params.get("mirror", "fastgit")
            return {
                "success": True,
                "original": url,
                "mirror": self.accelerator.get_mirror_url(url, mirror)
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
    accelerator = GitHubAccelerator()
    
    if cmd == "check":
        print("检测 GitHub 连接速度...")
        result = accelerator.test_speed()
        
        if result.get("success"):
            print(f"✓ 连接成功")
            print(f"  延迟: {result['latency_ms']}ms")
            print(f"  状态: {result['status']}")
        else:
            print(f"✗ 连接失败: {result.get('error')}")
    
    elif cmd == "speed":
        results = accelerator.test_all_ips()
        
        print("\n测试结果:")
        print("-" * 60)
        print(f"{'IP':<18} {'位置':<12} {'延迟':<12} {'状态':<10}")
        print("-" * 60)
        
        for r in results:
            ip = r.get("ip", "N/A")
            location = GITHUB_IPS.get(ip, "未知")
            
            if r.get("success"):
                latency = f"{r['latency_ms']}ms"
                status = "✓ 可用"
            else:
                latency = "-"
                status = "✗ 失败"
            
            print(f"{ip:<18} {location:<12} {latency:<12} {status:<10}")
    
    elif cmd == "apply":
        ip = sys.argv[2] if len(sys.argv) > 2 else None
        
        print("应用 GitHub 加速...")
        result = accelerator.apply_hosts_acceleration(ip)
        
        if result.get("success"):
            print(f"✓ {result['message']}")
            print(f"  IP: {result['ip']}")
            print(f"  域名数: {result['domains']}")
        else:
            print(f"✗ 应用失败: {result.get('error')}")
    
    elif cmd == "auto":
        result = accelerator.auto_optimize()
        
        if result.get("success"):
            if result.get("optimized"):
                print(f"✓ 优化完成")
                print(f"  方法: {result.get('method')}")
                print(f"  IP: {result.get('ip')}")
                if result.get("before_latency"):
                    print(f"  优化前: {result['before_latency']}ms")
                if result.get("after_latency"):
                    print(f"  优化后: {result['after_latency']}ms")
            else:
                print(f"- {result.get('reason')}")
        else:
            print(f"✗ 优化失败: {result.get('error')}")
    
    elif cmd == "restore":
        print("恢复原始 hosts...")
        result = accelerator.restore_hosts()
        
        if result.get("success"):
            print(f"✓ {result['message']}")
        else:
            print(f"✗ 恢复失败: {result.get('error')}")
    
    elif cmd == "status":
        status = accelerator.get_status()
        
        print("GitHub 加速状态:")
        print("-" * 40)
        print(f"加速状态: {'已启用' if status['accelerated'] else '未启用'}")
        
        if status['current_ip']:
            print(f"当前 IP: {status['current_ip']}")
        
        speed = status.get('speed_test', {})
        if speed.get('success'):
            print(f"连接延迟: {speed.get('latency_ms')}ms")
        else:
            print(f"连接状态: 失败 ({speed.get('error', '未知错误')})")
        
        if status.get('last_apply'):
            last = status['last_apply']
            print(f"\n上次应用:")
            print(f"  方法: {last.get('method')}")
            print(f"  IP: {last.get('ip')}")
            print(f"  时间: {last.get('time')}")
    
    elif cmd == "mirror":
        if len(sys.argv) < 3:
            print("用法: github_accelerator.py mirror <url> [mirror_name]")
            return
        
        url = sys.argv[2]
        mirror = sys.argv[3] if len(sys.argv) > 3 else "fastgit"
        
        mirror_url = accelerator.get_mirror_url(url, mirror)
        
        print(f"原始 URL: {url}")
        print(f"镜像 URL: {mirror_url}")
        print(f"镜像源: {mirror}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("GitHub 加速器 MCP 服务器已启动")
        
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
