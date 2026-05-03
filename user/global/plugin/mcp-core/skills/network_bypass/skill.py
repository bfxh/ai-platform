#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络突破下载系统 - skill.py
功能：突破各种网络限制下载文件/克隆仓库，支持多种备用方案自动切换

原理：
1. GitHub 直连 → ghproxy → gitclone → ghd.li → 镜像站
2. pip/npm/conda 镜像自动切换
3. 单个文件 HTTP 下载失败自动换源
4. 大文件支持断点续传 + 分片下载

用法：
    python skill.py download <url> [--dest <path>]
    python skill.py clone <repo_url> [--dest <path>] [--depth 1]
    python skill.py pip <package> [--mirror tuna|ali|netease]
    python skill.py npm <package> [--mirror taobao|npm]
    python skill.py probe <url>   # 测试哪些源可用
"""

import os
import sys
import re
import json
import time
import shutil
import hashlib
import subprocess
import urllib.request
import urllib.error
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# ─── 路径常量 ─────────────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent
MCP_CORE = SKILL_DIR.parent.parent
KB_PATH = MCP_CORE / "data" / "knowledge_base.db"


# ─── 网络突破策略（按优先级）─────────────────────────────────────────────────
class ProxyStrategy:
    """网络突破策略"""

    # GitHub 克隆可用方案（按优先级）
    GITHUB_CLONE_STRATEGIES = [
        {"name": "direct", "url": "https://github.com/", "desc": "直连"},
        {"name": "ghproxy", "url": "https://ghproxy.cn/", "desc": "ghproxy.cn 镜像"},
        {"name": "gitclone", "url": "https://gitclone.com/github.com/", "desc": "GitClone 镜像"},
        {"name": "ghd_li", "url": "https://ghdl.feishu.cn/", "desc": "飞书镜像"},
        {"name": "mirror_git", "url": "https://mirror.ghproxy.com/https://github.com/", "desc": "ghproxy飞书备用"},
    ]

    # GitHub Raw 可用方案
    GITHUB_RAW_STRATEGIES = [
        {"name": "direct", "url": "https://raw.githubusercontent.com/", "desc": "直连"},
        {"name": "ghproxy", "url": "https://ghproxy.cn/https://raw.githubusercontent.com/", "desc": "ghproxy"},
        {"name": "jsdelivr", "url": "https://cdn.jsdelivr.net/gh/", "desc": "jsDelivr CDN"},
        {"name": "statically", "url": "https://cdn.statically.io/gh/", "desc": "Statically CDN"},
    ]

    # pip 镜像
    PIP_MIRRORS = [
        {"name": "pypi", "url": "https://pypi.org/simple/", "desc": "官方 PyPI"},
        {"name": "tuna", "url": "https://pypi.tuna.tsinghua.edu.cn/simple/", "desc": "清华 tuna"},
        {"name": "ali", "url": "https://mirrors.aliyun.com/pypi/simple/", "desc": "阿里云"},
        {"name": "netease", "url": "https://mirrors.163.com/pypi/simple/", "desc": "网易"},
        {"name": "tencent", "url": "https://mirrors.cloud.tencent.com/pypi/simple/", "desc": "腾讯云"},
    ]

    # npm 镜像
    NPM_MIRRORS = [
        {"name": "npm", "url": "https://registry.npmjs.org/", "desc": "官方 npm"},
        {"name": "taobao", "url": "https://registry.npmmirror.com/", "desc": "淘宝镜像"},
        {"name": "tencent", "url": "https://registry.npmmirror.com/", "desc": "腾讯镜像"},
    ]


class Downloader:
    """通用下载器，支持多策略自动切换"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.success_count = 0
        self.fail_count = 0

    def _make_request(self, url: str, method: str = "GET",
                     headers: Dict = None, data: bytes = None) -> Tuple[bool, str]:
        """发送 HTTP 请求，返回 (成功, 内容/错误)"""
        if headers is None:
            headers = {}
        headers.setdefault("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/120.0.0.0 Safari/537.36")

        try:
            req = urllib.request.Request(url, method=method, headers=headers,
                                         data=data, unverifiable=True)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                content = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
                try:
                    return True, content.decode(charset, errors="replace")
                except Exception:
                    return True, content.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return False, f"URL错误: {e.reason}"
        except Exception as e:
            return False, f"错误: {str(e)}"

    def _make_binary_request(self, url: str) -> Tuple[bool, bytes]:
        """下载二进制内容"""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return True, resp.read()
        except Exception as e:
            return False, str(e).encode()

    def probe_url(self, url: str, max_retries: int = 3) -> Dict:
        """探测 URL 可用性（带重试）"""
        for attempt in range(max_retries):
            ok, _ = self._make_request(url)
            if ok:
                return {"url": url, "status": "available", "attempts": attempt + 1}
            time.sleep(0.5)
        return {"url": url, "status": "unavailable", "attempts": max_retries}

    def download_file(self, url: str, dest_path: str = None,
                      strategies: List[Dict] = None) -> Dict:
        """
        下载文件，自动尝试多个策略
        strategies: 可用策略列表，每个是 {"name": str, "url": str, "desc": str}
        """
        if strategies is None:
            # 默认使用 raw 策略
            strategies = ProxyStrategy.GITHUB_RAW_STRATEGIES

        # 特殊处理：如果是完整的 GitHub 仓库 raw URL
        if "github.com" in url and "/raw/" in url:
            raw_url = url
        elif "raw.githubusercontent.com" in url:
            raw_url = url
            # 尝试替换镜像
            strategies = ProxyStrategy.GITHUB_RAW_STRATEGIES
        elif "github.com" in url and not "/raw/" in url:
            # 不是 raw URL，只尝试直连
            strategies = [{"name": "direct", "url": "", "desc": "直连"}]

        for strategy in strategies:
            name = strategy["name"]
            proxy_base = strategy["url"]

            # 构造实际 URL
            if name == "direct":
                actual_url = raw_url if 'raw_url' in dir() else url
            elif name == "jsdelivr":
                # jsdelivr: https://cdn.jsdelivr.net/gh/user/repo@tag/file
                actual_url = self._to_jsdelivr(url)
            elif name == "statically":
                actual_url = self._to_statically(url)
            elif proxy_base:
                # 代理：替换域名
                actual_url = self._apply_proxy(url, proxy_base)
            else:
                actual_url = url

            print(f"  尝试 [{name}] {strategy['desc']}: {actual_url[:80]}...")

            ok, result = self._make_binary_request(actual_url)
            if ok:
                content = result
                # 保存文件
                if dest_path:
                    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(dest_path, "wb") as f:
                        f.write(content)
                # 写知识库
                self._record_download(url, actual_url, len(content), "success")
                return {
                    "status": "success",
                    "strategy": name,
                    "url": actual_url,
                    "size": len(content),
                    "dest": dest_path,
                }
            else:
                print(f"    失败: {result}")
                self.fail_count += 1

        return {"status": "failed", "url": url, "error": "所有策略均失败"}

    def _to_jsdelivr(self, url: str) -> str:
        """将 GitHub raw URL 转为 jsdelivr URL"""
        # https://raw.githubusercontent.com/user/repo/branch/path → https://cdn.jsdelivr.net/gh/user/repo@branch/path
        m = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)",
                     url)
        if m:
            user, repo, branch, path = m.groups()
            return f"https://cdn.jsdelivr.net/gh/{user}/{repo}@{branch}/{path}"
        return url

    def _to_statically(self, url: str) -> str:
        """将 GitHub URL 转为 statically URL"""
        m = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)",
                     url)
        if m:
            user, repo, branch, path = m.groups()
            return f"https://cdn.statically.io/gh/{user}/{repo}/{branch}/{path}"
        return url

    def _apply_proxy(self, url: str, proxy_base: str) -> str:
        """应用代理前缀"""
        if proxy_base.endswith("/"):
            proxy_base = proxy_base[:-1]
        return f"{proxy_base}/{url}"

    def _record_download(self, original_url: str, actual_url: str,
                         size: int, status: str):
        """记录下载历史到知识库"""
        try:
            conn = sqlite3.connect(str(KB_PATH))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_url TEXT,
                    actual_url TEXT,
                    size INTEGER,
                    status TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(
                "INSERT INTO download_history (original_url, actual_url, size, status) VALUES (?, ?, ?, ?)",
                (original_url, actual_url, size, status)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass


class GitHubDownloader(Downloader):
    """GitHub 专用下载器"""

    def __init__(self, timeout: int = 60):
        super().__init__(timeout)
        self.clone_strategies = ProxyStrategy.GITHUB_CLONE_STRATEGIES

    def probe_github(self, owner: str = None, repo: str = None) -> Dict:
        """探测 GitHub 各策略可用性"""
        results = {}
        test_url = "https://api.github.com/repos/torvalds/linux"
        if owner and repo:
            test_url = f"https://api.github.com/repos/{owner}/{repo}"

        print("=== 探测 GitHub 访问策略 ===")
        for strategy in self.clone_strategies:
            name = strategy["name"]
            proxy_base = strategy["url"]

            # 构造测试 URL
            if name == "direct":
                test_clone = f"https://github.com/torvalds/linux.git"
            elif proxy_base.endswith("github.com/"):
                test_clone = f"{proxy_base}torvalds/linux.git"
            elif proxy_base.endswith("/"):
                test_clone = f"{proxy_base}https://github.com/torvalds/linux.git"
            else:
                test_clone = f"{proxy_base}/https://github.com/torvalds/linux.git"

            # 用 git ls-remote 测试
            ok, out = self._git_ls_remote(test_clone)
            results[name] = {
                "strategy": name,
                "desc": strategy["desc"],
                "status": "ok" if ok else "fail",
                "test_url": test_clone[:80],
                "output": out[:100] if out else "",
            }
            print(f"  [{name}] {strategy['desc']}: {'✓ 可用' if ok else '✗ 失败'}")
            time.sleep(0.3)

        # 找最快的策略
        available = [k for k, v in results.items() if v["status"] == "ok"]
        if not available:
            results["_best"] = {"strategy": "none", "status": "all_failed"}
        else:
            results["_best"] = {"strategy": available[0], "status": "ready"}

        return results

    def _git_ls_remote(self, url: str, timeout: int = 15) -> Tuple[bool, str]:
        """用 git ls-remote 测试仓库是否可访问"""
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--heads", url],
                capture_output=True, text=True, timeout=timeout,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}
            )
            if result.returncode == 0 and result.stdout:
                return True, result.stdout.strip()[:100]
            return False, result.stderr.strip()[:100]
        except Exception as e:
            return False, str(e)

    def clone_repo(self, repo_url: str, dest_dir: str = None,
                   depth: int = 1, branch: str = None) -> Dict:
        """
        克隆仓库，自动尝试多个策略
        """
        # 解析仓库信息
        m = re.match(r"https?://github\.com/([^/]+)/([^/.]+)(?:\.git)?", repo_url)
        if not m:
            return {"status": "error", "error": "无效的 GitHub 仓库 URL"}

        owner, repo = m.group(1), m.group(2)

        # 确定目标目录
        if not dest_dir:
            dest_dir = str(MCP_CORE / "github_projects" / f"{owner}_{repo}")

        # 构造 clone URL（带代理）
        Path(dest_dir).parent.mkdir(parents=True, exist_ok=True)

        print(f"=== 克隆仓库: {owner}/{repo} ===")

        # 探测可用策略
        probe_results = self.probe_github(owner, repo)
        best_strategy = probe_results.get("_best", {}).get("strategy", "direct")

        # 按优先级尝试
        strategies_to_try = sorted(
            self.clone_strategies,
            key=lambda x: (0 if x["name"] == best_strategy else 1, x["name"])
        )

        for strategy in strategies_to_try:
            name = strategy["name"]
            proxy_base = strategy["url"]

            if name == "direct":
                clone_url = f"https://github.com/{owner}/{repo}.git"
            elif name == "ghproxy":
                clone_url = f"https://ghproxy.cn/https://github.com/{owner}/{repo}.git"
            elif name == "gitclone":
                clone_url = f"https://gitclone.com/github.com/{owner}/{repo}.git"
            elif name == "ghd_li":
                clone_url = f"https://ghdl.feishu.cn/https://github.com/{owner}/{repo}.git"
            elif name == "mirror_git":
                clone_url = f"https://mirror.ghproxy.com/https://github.com/{owner}/{repo}.git"
            else:
                clone_url = f"{proxy_base}{owner}/{repo}.git"

            print(f"\n  尝试 [{name}] {strategy['desc']}: {clone_url}")

            cmd = ["git", "clone"]
            if depth > 0:
                cmd += ["--depth", str(depth)]
            if branch:
                cmd += ["--branch", branch]
            cmd += [clone_url, dest_dir]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True, text=True, timeout=120,
                    env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}
                )

                if result.returncode == 0:
                    print(f"  ✓ 成功！")
                    # 记录到知识库
                    self._record_download(repo_url, clone_url, 0, "clone_success")
                    return {
                        "status": "success",
                        "strategy": name,
                        "clone_url": clone_url,
                        "dest_dir": dest_dir,
                        "branch": branch or "main/master",
                    }
                else:
                    err = result.stderr.strip()
                    # 如果目标目录存在，清理后重试
                    if "destination path" in err and "already exists" in err:
                        shutil.rmtree(dest_dir, ignore_errors=True)
                        continue
                    print(f"    失败: {err[:100]}")
            except subprocess.TimeoutExpired:
                print(f"    超时")
            except Exception as e:
                print(f"    错误: {str(e)}")

        return {
            "status": "failed",
            "repo_url": repo_url,
            "error": "所有策略均失败，尝试手动配置代理",
            "suggestion": "设置环境变量: set HTTPS_PROXY=http://127.0.0.1:7890",
        }

    def get_branches(self, owner: str, repo: str) -> List[Dict]:
        """获取仓库的所有分支"""
        api_url = f"https://api.github.com/repos/{owner}/{repo}/branches"

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-Core-Downloader"
        }

        branches = []
        page = 1
        while True:
            try:
                req = urllib.request.Request(
                    f"{api_url}?per_page=100&page={page}",
                    headers=headers
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if not data:
                        break
                    branches.extend([{
                        "name": b["name"],
                        "protected": b.get("protected", False),
                        "commit": b["commit"]["sha"][:8],
                    } for b in data])
                    if len(data) < 100:
                        break
                    page += 1
            except Exception as e:
                print(f"获取分支失败: {e}")
                break

        return branches

    def get_default_branch(self, owner: str, repo: str) -> str:
        """获取仓库默认分支"""
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "MCP-Core"}

        try:
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("default_branch", "main")
        except Exception:
            return "main"

    def analyze_repo(self, repo_url: str) -> Dict:
        """
        分析仓库：默认分支 + 所有分支 + 最新提交 + 语言分布
        """
        m = re.match(r"https?://github\.com/([^/]+)/([^/.]+)", repo_url)
        if not m:
            return {"error": "无效的仓库 URL"}

        owner, repo = m.group(1), m.group(2)

        print(f"分析仓库: {owner}/{repo}")

        # 并行获取
        default_branch = self.get_default_branch(owner, repo)
        branches = self.get_branches(owner, repo)

        # 获取默认分支的最新 commit
        commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?sha={default_branch}&per_page=5"
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "MCP-Core"}
        latest_commits = []
        try:
            req = urllib.request.Request(commits_url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latest_commits = [{
                    "sha": c["sha"][:8],
                    "message": c["commit"]["message"].split("\n")[0],
                    "author": c["commit"]["author"]["name"],
                    "date": c["commit"]["author"]["date"],
                } for c in data]
        except Exception:
            pass

        # 获取语言分布
        lang_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
        languages = {}
        try:
            req = urllib.request.Request(lang_url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                languages = json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass

        result = {
            "owner": owner,
            "repo": repo,
            "url": repo_url,
            "default_branch": default_branch,
            "branches": branches,
            "branch_count": len(branches),
            "latest_commits": latest_commits,
            "languages": languages,
            "timestamp": datetime.now().isoformat(),
        }

        # 打印分析结果
        print(f"\n  默认分支: {default_branch}")
        print(f"  分支总数: {len(branches)}")
        print(f"  语言分布: {json.dumps(languages, ensure_ascii=False)}")
        if latest_commits:
            print(f"  最新提交: {latest_commits[0]['sha']} - {latest_commits[0]['message'][:50]}")

        return result


class PackageDownloader(Downloader):
    """pip/npm/conda 包下载器"""

    def pip_install(self, package: str, mirror: str = "tuna",
                    upgrade: bool = False, target_dir: str = None) -> Dict:
        """pip 安装包，自动切换镜像"""
        mirror_url = None
        for m in ProxyStrategy.PIP_MIRRORS:
            if m["name"] == mirror:
                mirror_url = m["url"]
                break

        if not mirror_url:
            mirror_url = ProxyStrategy.PIP_MIRRORS[1]["url"]  # 默认 tuna

        cmd = [sys.executable, "-m", "pip", "install"]
        if upgrade:
            cmd.append("--upgrade")
        if target_dir:
            cmd += ["-t", target_dir]
        cmd += ["-i", mirror_url, package]

        print(f"pip 安装: {package} (镜像: {mirror})")
        print(f"命令: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print(f"  ✓ 成功")
                return {"status": "success", "package": package, "mirror": mirror}
            else:
                # 尝试其他镜像
                print(f"  安装失败，尝试其他镜像...")
                for m in ProxyStrategy.PIP_MIRRORS:
                    if m["name"] == mirror:
                        continue
                    alt_cmd = cmd[:-2] + ["-i", m["url"]]
                    print(f"  尝试 {m['desc']}...")
                    r = subprocess.run(alt_cmd, capture_output=True, text=True, timeout=120)
                    if r.returncode == 0:
                        print(f"  ✓ 成功")
                        return {"status": "success", "package": package,
                                "mirror": m["name"], "cmd": " ".join(alt_cmd)}
                return {"status": "failed", "error": result.stderr[:200]}
        except subprocess.TimeoutExpired:
            return {"status": "failed", "error": "安装超时（120秒）"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def npm_install(self, package: str, mirror: str = "taobao",
                    global_install: bool = False) -> Dict:
        """npm 安装包，自动切换镜像"""
        for m in ProxyStrategy.NPM_MIRRORS:
            if m["name"] == mirror:
                registry = m["url"]
                break
        else:
            registry = ProxyStrategy.NPM_MIRRORS[1]["url"]

        cmd = ["npm"]
        if global_install:
            cmd.append("-g")
        cmd.extend(["install", "-g", package, "--registry", registry])

        print(f"npm 安装: {package} (镜像: {mirror})")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                return {"status": "success", "package": package, "mirror": mirror}
            else:
                return {"status": "failed", "error": result.stderr[:200]}
        except Exception as e:
            return {"status": "failed", "error": str(e)}


def write_to_kb(data: Dict):
    """写入知识库"""
    try:
        conn = sqlite3.connect(str(KB_PATH))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS network_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_type TEXT,
                url TEXT,
                status TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)
        conn.execute(
            "INSERT INTO network_tools (tool_type, url, status, notes) VALUES (?, ?, ?, ?)",
            (data.get("type"), data.get("url"), data.get("status"), data.get("notes", ""))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ─── 主入口 ────────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        return

    cmd = args[0]

    if cmd == "probe":
        url = args[1] if len(args) > 1 else "https://github.com"
        d = Downloader()
        result = d.probe_url(url)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "probe-github":
        owner = args[1] if len(args) > 1 else None
        repo = args[2] if len(args) > 2 else None
        gh = GitHubDownloader()
        results = gh.probe_github(owner, repo)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    elif cmd == "clone":
        repo_url = args[1] if len(args) > 1 else input("仓库URL: ")
        dest = args[3] if len(args) > 3 and args[2] == "--dest" else None
        depth = 1
        if "--depth" in args:
            idx = args.index("--depth")
            depth = int(args[idx + 1]) if idx + 1 < len(args) else 1
        branch = None
        if "--branch" in args:
            idx = args.index("--branch")
            branch = args[idx + 1] if idx + 1 < len(args) else None

        gh = GitHubDownloader()
        result = gh.clone_repo(repo_url, dest, depth=depth, branch=branch)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        write_to_kb({"type": "clone", "url": repo_url, "status": result["status"],
                     "notes": result.get("strategy", "")})

    elif cmd == "analyze":
        repo_url = args[1] if len(args) > 1 else input("仓库URL: ")
        gh = GitHubDownloader()
        result = gh.analyze_repo(repo_url)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "download":
        url = args[1] if len(args) > 1 else input("下载URL: ")
        dest = args[3] if len(args) > 3 and args[2] == "--dest" else None
        d = Downloader()
        result = d.download_file(url, dest)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "pip":
        package = args[1] if len(args) > 1 else input("包名: ")
        mirror = "tuna"
        if "--mirror" in args:
            idx = args.index("--mirror")
            mirror = args[idx + 1] if idx + 1 < len(args) else "tuna"
        pkg = PackageDownloader()
        result = pkg.pip_install(package, mirror=mirror)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "npm":
        package = args[1] if len(args) > 1 else input("包名: ")
        pkg = PackageDownloader()
        result = pkg.npm_install(package)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
