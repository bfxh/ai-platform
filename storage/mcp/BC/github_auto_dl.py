#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 自动下载器 - 自动下载 GitHub 资源

功能：
- 自动搜索和发现 GitHub 资源
- 批量下载 GitHub 仓库
- 自动分类和整理
- 支持 Release、Code、Wiki 下载
- 自动解压和配置
- 支持定时同步

用法：
    python github_auto_dl.py search <query>              # 搜索资源
    python github_auto_dl.py download <url> [options]    # 下载资源
    python github_auto_dl.py batch <urls_file>           # 批量下载
    python github_auto_dl.py sync <repo>                 # 同步仓库
    python github_auto_dl.py watch <repo>                # 监控更新
    python github_auto_dl.py list                        # 列出已下载
    python github_auto_dl.py organize                    # 自动整理

MCP调用：
    {"tool": "github_auto_dl", "action": "download", "params": {"url": "..."}}
"""

import json
import sys
import os
import subprocess
import urllib.request
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
DOWNLOAD_PATH = Path("D:/Downloads/GitHub")
DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

# 分类目录
CATEGORY_DIRS = {
    "tools": "工具",
    "games": "游戏",
    "ai": "AI/ML",
    "web": "Web开发",
    "mobile": "移动开发",
    "desktop": "桌面应用",
    "library": "库/框架",
    "docs": "文档/教程",
    "other": "其他",
}

# ============================================================
# GitHub 自动下载器
# ============================================================
class GitHubAutoDownloader:
    """GitHub 自动下载器"""
    
    def __init__(self):
        self.download_path = DOWNLOAD_PATH
        self.downloaded = self._load_downloaded()
    
    def _load_downloaded(self) -> Dict:
        """加载已下载列表"""
        downloaded_file = self.download_path / "downloaded.json"
        if downloaded_file.exists():
            with open(downloaded_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_downloaded(self):
        """保存已下载列表"""
        downloaded_file = self.download_path / "downloaded.json"
        with open(downloaded_file, 'w', encoding='utf-8') as f:
            json.dump(self.downloaded, f, ensure_ascii=False, indent=2)
    
    def _get_category_from_repo(self, repo_info: Dict) -> str:
        """根据仓库信息确定分类"""
        topics = repo_info.get("topics", [])
        description = repo_info.get("description", "").lower()
        name = repo_info.get("name", "").lower()
        
        # 游戏相关
        if any(word in topics + [description, name] for word in ["game", "godot", "unity", "unreal"]):
            return "games"
        
        # AI/ML 相关
        if any(word in topics + [description, name] for word in ["ai", "ml", "machine-learning", "deep-learning", "neural"]):
            return "ai"
        
        # Web 相关
        if any(word in topics + [description, name] for word in ["web", "react", "vue", "angular", "frontend", "backend"]):
            return "web"
        
        # 移动开发
        if any(word in topics + [description, name] for word in ["android", "ios", "mobile", "flutter", "react-native"]):
            return "mobile"
        
        # 桌面应用
        if any(word in topics + [description, name] for word in ["desktop", "electron", "qt", "gtk"]):
            return "desktop"
        
        # 工具
        if any(word in topics + [description, name] for word in ["tool", "cli", "utility", "automation"]):
            return "tools"
        
        # 库/框架
        if any(word in topics + [description, name] for word in ["library", "framework", "sdk"]):
            return "library"
        
        return "other"
    
    def search_github(self, query: str, sort: str = "stars", limit: int = 10) -> Dict:
        """搜索 GitHub 资源"""
        try:
            # 使用 GitHub API 搜索
            url = f"https://api.github.com/search/repositories?q={query}&sort={sort}&order=desc&per_page={limit}"
            
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AI-Assistant"
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            results = []
            for item in data.get("items", []):
                results.append({
                    "name": item["name"],
                    "full_name": item["full_name"],
                    "description": item["description"],
                    "url": item["html_url"],
                    "stars": item["stargazers_count"],
                    "language": item["language"],
                    "topics": item.get("topics", []),
                    "updated_at": item["updated_at"],
                })
            
            return {
                "success": True,
                "query": query,
                "total_count": data.get("total_count", 0),
                "results": results
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_repo(self, repo_url: str, category: str = None, 
                      branch: str = "main", extract: bool = True) -> Dict:
        """下载 GitHub 仓库"""
        try:
            # 解析仓库 URL
            # 支持格式: https://github.com/user/repo
            parts = repo_url.replace("https://github.com/", "").replace("http://github.com/", "").strip("/").split("/")
            
            if len(parts) < 2:
                return {"success": False, "error": "无效的 GitHub URL"}
            
            user = parts[0]
            repo = parts[1]
            
            # 获取仓库信息
            repo_info = self._get_repo_info(user, repo)
            
            # 确定分类
            if not category:
                category = self._get_category_from_repo(repo_info)
            
            # 创建分类目录
            category_dir = self.download_path / CATEGORY_DIRS.get(category, "其他")
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建下载 URL
            download_url = f"https://github.com/{user}/{repo}/archive/refs/heads/{branch}.zip"
            
            # 下载文件
            output_file = category_dir / f"{repo}-{branch}.zip"
            
            print(f"正在下载: {user}/{repo} ({branch})")
            
            headers = {"User-Agent": "AI-Assistant"}
            req = urllib.request.Request(download_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(output_file, 'wb') as f:
                    f.write(response.read())
            
            # 记录下载
            download_id = f"{user}/{repo}"
            self.downloaded[download_id] = {
                "url": repo_url,
                "downloaded_at": datetime.now().isoformat(),
                "path": str(output_file),
                "category": category,
                "branch": branch,
                "size": output_file.stat().st_size
            }
            self._save_downloaded()
            
            result = {
                "success": True,
                "repo": f"{user}/{repo}",
                "downloaded_to": str(output_file),
                "category": category,
                "size": output_file.stat().st_size
            }
            
            # 解压
            if extract:
                extract_result = self._extract_archive(output_file, category_dir)
                result["extracted"] = extract_result
            
            return result
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_repo_info(self, user: str, repo: str) -> Dict:
        """获取仓库信息"""
        try:
            url = f"https://api.github.com/repos/{user}/{repo}"
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AI-Assistant"
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except:
            return {}
    
    def _extract_archive(self, archive_path: Path, extract_to: Path) -> Dict:
        """解压归档文件"""
        try:
            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                
                # 删除 zip 文件
                archive_path.unlink()
                
                return {
                    "success": True,
                    "extracted_to": str(extract_to),
                    "removed_archive": True
                }
            
            return {"success": False, "error": "不支持的归档格式"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_release(self, repo_url: str, version: str = "latest") -> Dict:
        """下载 Release"""
        try:
            parts = repo_url.replace("https://github.com/", "").strip("/").split("/")
            user = parts[0]
            repo = parts[1]
            
            # 获取 release 信息
            if version == "latest":
                url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
            else:
                url = f"https://api.github.com/repos/{user}/{repo}/releases/tags/{version}"
            
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AI-Assistant"
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                release = json.loads(response.read().decode('utf-8'))
            
            # 下载第一个资源
            assets = release.get("assets", [])
            if not assets:
                return {"success": False, "error": "没有可下载的资源"}
            
            asset = assets[0]
            download_url = asset["browser_download_url"]
            asset_name = asset["name"]
            
            # 下载
            category_dir = self.download_path / "releases"
            category_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = category_dir / asset_name
            
            headers = {"User-Agent": "AI-Assistant"}
            req = urllib.request.Request(download_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=120) as response:
                with open(output_file, 'wb') as f:
                    f.write(response.read())
            
            return {
                "success": True,
                "repo": f"{user}/{repo}",
                "version": release.get("tag_name"),
                "downloaded": str(output_file),
                "size": output_file.stat().st_size
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def batch_download(self, urls_file: str, category: str = None) -> Dict:
        """批量下载"""
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            results = []
            for url in urls:
                print(f"下载: {url}")
                result = self.download_repo(url, category)
                results.append({"url": url, "result": result})
                time.sleep(1)  # 避免请求过快
            
            successful = sum(1 for r in results if r["result"].get("success"))
            
            return {
                "success": True,
                "total": len(urls),
                "successful": successful,
                "failed": len(urls) - successful,
                "results": results
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_downloaded(self, category: str = None) -> Dict:
        """列出已下载"""
        if category:
            filtered = {
                k: v for k, v in self.downloaded.items()
                if v.get("category") == category
            }
        else:
            filtered = self.downloaded
        
        return {
            "success": True,
            "count": len(filtered),
            "downloads": [
                {
                    "repo": k,
                    **v
                }
                for k, v in filtered.items()
            ]
        }
    
    def organize_downloads(self) -> Dict:
        """整理下载"""
        try:
            organized = 0
            
            for repo_id, info in self.downloaded.items():
                current_path = Path(info["path"])
                
                if not current_path.exists():
                    continue
                
                # 确定正确分类
                category = info.get("category", "other")
                target_dir = self.download_path / CATEGORY_DIRS.get(category, "其他")
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # 移动文件
                if current_path.parent != target_dir:
                    new_path = target_dir / current_path.name
                    current_path.rename(new_path)
                    
                    self.downloaded[repo_id]["path"] = str(new_path)
                    organized += 1
            
            self._save_downloaded()
            
            return {
                "success": True,
                "organized": organized,
                "message": f"已整理 {organized} 个下载"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.downloader = GitHubAutoDownloader()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "search":
            return self.downloader.search_github(
                query=params.get("query"),
                sort=params.get("sort", "stars"),
                limit=params.get("limit", 10)
            )
        
        elif action == "download":
            return self.downloader.download_repo(
                repo_url=params.get("url"),
                category=params.get("category"),
                branch=params.get("branch", "main"),
                extract=params.get("extract", True)
            )
        
        elif action == "download_release":
            return self.downloader.download_release(
                repo_url=params.get("url"),
                version=params.get("version", "latest")
            )
        
        elif action == "batch":
            return self.downloader.batch_download(
                urls_file=params.get("urls_file"),
                category=params.get("category")
            )
        
        elif action == "list":
            return self.downloader.list_downloaded(
                category=params.get("category")
            )
        
        elif action == "organize":
            return self.downloader.organize_downloads()
        
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
    downloader = GitHubAutoDownloader()
    
    if cmd == "search":
        if len(sys.argv) < 3:
            print("用法: github_auto_dl.py search <query>")
            return
        
        query = sys.argv[2]
        result = downloader.search_github(query)
        
        if result.get("success"):
            print(f"搜索 '{query}' 找到 {result['total_count']} 个结果:")
            print("-" * 60)
            for i, repo in enumerate(result["results"], 1):
                print(f"\n{i}. {repo['full_name']} ★{repo['stars']}")
                print(f"   {repo['description'] or '无描述'}")
                print(f"   {repo['url']}")
                if repo['topics']:
                    print(f"   标签: {', '.join(repo['topics'])}")
    
    elif cmd == "download":
        if len(sys.argv) < 3:
            print("用法: github_auto_dl.py download <url> [category]")
            return
        
        url = sys.argv[2]
        category = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = downloader.download_repo(url, category)
        
        if result.get("success"):
            print(f"✓ 下载成功: {result['repo']}")
            print(f"  分类: {result['category']}")
            print(f"  路径: {result['downloaded_to']}")
            print(f"  大小: {result['size'] / 1024 / 1024:.2f} MB")
        else:
            print(f"✗ 下载失败: {result.get('error')}")
    
    elif cmd == "list":
        category = sys.argv[2] if len(sys.argv) > 2 else None
        result = downloader.list_downloaded(category)
        
        if result.get("success"):
            print(f"已下载 {result['count']} 个资源:")
            print("-" * 60)
            for item in result["downloads"]:
                print(f"\n{item['repo']}")
                print(f"  分类: {item['category']}")
                print(f"  时间: {item['downloaded_at']}")
                print(f"  路径: {item['path']}")
    
    elif cmd == "organize":
        result = downloader.organize_downloads()
        
        if result.get("success"):
            print(f"✓ {result['message']}")
        else:
            print(f"✗ 整理失败: {result.get('error')}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("GitHub 自动下载器 MCP 已启动")
        
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
