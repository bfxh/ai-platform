#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用下载器 Skill - 支持下载任何东西

功能:
- 下载文件
- 下载 GitHub 仓库
- 下载 GitHub ZIP
- 下载 AI 模型
- 批量下载
- 支持代理和镜像
"""

import os
import sys
import json
import time
import zipfile
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
import re

sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    import requests
except ImportError:
    print("需要安装 requests: pip install requests")
    requests = None

from skills.base import Skill


class UniversalDownloader(Skill):
    name = "universal_downloader"
    description = "通用下载器 - 支持下载任何东西：文件、GitHub仓库、项目、模型、文档等"
    version = "1.0.0"
    author = "MCP Core Team"

    GITHUB_MIRRORS = [
        "https://github.com/",
        "https://gitclone.com/github.com/",
        "https://ghproxy.cn/https://github.com/",
        "https://ghproxy.com/https://github.com/",
        "https://mirror.ghproxy.com/https://github.com/",
    ]

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.token = os.getenv("GITHUB_TOKEN", self.config.get("token", ""))
        self.session = requests.Session() if requests else None
        self.cache_dir = Path(self.config.get("cache_dir", "/python/downloads"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, action: str, params: Dict) -> Dict:
        if not requests:
            return {"success": False, "error": "requests 库未安装"}
        
        if action == "download_file":
            return self._download_file(params)
        elif action == "download_github":
            return self._download_github(params)
        elif action == "download_github_zip":
            return self._download_github_zip(params)
        elif action == "download_skill":
            return self._download_skill(params)
        elif action == "download_model":
            return self._download_model(params)
        elif action == "batch_download":
            return self._batch_download(params)
        elif action == "clone_repo":
            return self._clone_repo(params)
        else:
            return {"success": False, "error": f"未知动作: {action}"}

    def _get_headers(self) -> Dict:
        headers = {"User-Agent": "UniversalDownloader/1.0"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _download_file(self, params: Dict) -> Dict:
        url = params.get("url")
        target_path = params.get("target_path")
        filename = params.get("filename")
        
        if not url:
            return {"success": False, "error": "缺少 url 参数"}
        
        if not target_path:
            target_path = self.cache_dir / (filename or Path(url).name)
        else:
            target_path = Path(target_path)
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            response = self.session.get(url, headers=self._get_headers(), stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            
            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            return {
                "success": True,
                "path": str(target_path),
                "size": downloaded,
                "url": url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_github_url(self, url: str) -> Optional[tuple]:
        patterns = [
            r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$",
            r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$",
        ]
        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                return match.group(1), match.group(2)
        return None

    def _download_github(self, params: Dict) -> Dict:
        repo_url = params.get("repo_url")
        target_dir = params.get("target_dir")
        branch = params.get("branch", "main")
        
        if not repo_url:
            return {"success": False, "error": "缺少 repo_url 参数"}
        
        parsed = self._parse_github_url(repo_url)
        if not parsed:
            return {"success": False, "error": "无效的 GitHub URL"}
        
        owner, repo = parsed
        
        if not target_dir:
            target_dir = self.cache_dir / repo
        else:
            target_dir = Path(target_dir)
        
        git_url = f"https://github.com/{owner}/{repo}.git"
        
        for mirror in self.GITHUB_MIRRORS:
            try:
                mirror_url = mirror if mirror.endswith("/") else mirror + "/"
                if "github.com" not in mirror or mirror == "https://github.com/":
                    test_url = git_url
                else:
                    test_url = f"{mirror}https://github.com/{owner}/{repo}.git"
                
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", "-b", branch, test_url, str(target_dir)],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "path": str(target_dir),
                        "repo": f"{owner}/{repo}",
                        "branch": branch
                    }
            except Exception as e:
                continue
        
        return {"success": False, "error": "所有镜像源均失败"}

    def _download_github_zip(self, params: Dict) -> Dict:
        repo_full_name = params.get("repo_full_name")
        target_dir = params.get("target_dir", str(self.cache_dir))
        branch = params.get("branch", "main")
        
        if not repo_full_name:
            return {"success": False, "error": "缺少 repo_full_name 参数"}
        
        if "/" not in repo_full_name:
            return {"success": False, "error": "repo_full_name 格式应为 owner/repo"}
        
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        zip_url = f"https://github.com/{repo_full_name}/archive/refs/heads/{branch}.zip"
        
        try:
            response = self.session.get(zip_url, headers=self._get_headers(), timeout=60)
            response.raise_for_status()
            
            zip_path = target_dir / f"{repo_full_name.split('/')[-1]}-{branch}.zip"
            with open(zip_path, "wb") as f:
                f.write(response.content)
            
            extract_dir = target_dir / f"{repo_full_name.split('/')[-1]}-{branch}"
            if zip_path.exists():
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(target_dir)
                zip_path.unlink()
            
            return {
                "success": True,
                "zip_path": str(zip_path),
                "extract_path": str(extract_dir),
                "repo": repo_full_name
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _download_skill(self, params: Dict) -> Dict:
        skill_repo = params.get("skill_repo")
        target_dir = params.get("target_dir", "/python/MCP_Core/skills")
        
        if not skill_repo:
            return {"success": False, "error": "缺少 skill_repo 参数"}
        
        if "/" not in skill_repo:
            skill_repo = f"skill-repo/{skill_repo}"
        
        result = self._download_github_zip({
            "repo_full_name": skill_repo,
            "target_dir": target_dir,
            "branch": "main"
        })
        
        if result.get("success"):
            result["skill_name"] = skill_repo.split("/")[-1]
        
        return result

    def _download_model(self, params: Dict) -> Dict:
        model_url = params.get("model_url")
        target_dir = params.get("target_dir", "/python/models")
        filename = params.get("filename")
        
        if not model_url:
            return {"success": False, "error": "缺少 model_url 参数"}
        
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        if not filename:
            filename = Path(urlparse(model_url).path).name or "model"
        
        return self._download_file({
            "url": model_url,
            "target_path": target_dir / filename
        })

    def _clone_repo(self, params: Dict) -> Dict:
        repo_url = params.get("repo_url")
        target_dir = params.get("target_dir")
        
        if not repo_url:
            return {"success": False, "error": "缺少 repo_url 参数"}
        
        parsed = self._parse_github_url(repo_url)
        if not parsed:
            return {"success": False, "error": "无效的 GitHub URL"}
        
        owner, repo = parsed
        
        if not target_dir:
            target_dir = self.cache_dir / repo
        else:
            target_dir = Path(target_dir)
        
        git_url = f"https://github.com/{owner}/{repo}.git"
        
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", git_url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "path": str(target_dir),
                    "repo": f"{owner}/{repo}"
                }
            else:
                return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _batch_download(self, params: Dict) -> Dict:
        urls = params.get("urls", [])
        target_dir = params.get("target_dir", str(self.cache_dir))
        
        if not urls:
            return {"success": False, "error": "缺少 urls 参数"}
        
        results = []
        for i, url in enumerate(urls):
            print(f"下载 {i+1}/{len(urls)}: {url}")
            
            result = self._download_file({
                "url": url,
                "target_path": Path(target_dir) / Path(urlparse(url).path).name
            })
            
            results.append({
                "url": url,
                "result": result
            })
            
            if i < len(urls) - 1:
                time.sleep(0.5)
        
        success_count = sum(1 for r in results if r["result"].get("success"))
        
        return {
            "success": True,
            "total": len(urls),
            "success_count": success_count,
            "failed_count": len(urls) - success_count,
            "results": results
        }


if __name__ == "__main__":
    skill = UniversalDownloader()
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
        params = {}
        
        if action == "download_file" and len(sys.argv) > 2:
            params = {"url": sys.argv[2]}
        elif action == "download_github" and len(sys.argv) > 2:
            params = {"repo_url": sys.argv[2]}
        elif action == "clone" and len(sys.argv) > 2:
            params = {"repo_url": sys.argv[2]}
        
        result = skill.execute(action, params)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("通用下载器 Skill")
        print("用法:")
        print("  python universal_downloader.py download_file <url>")
        print("  python universal_downloader.py download_github <repo_url>")
        print("  python universal_downloader.py clone <repo_url>")
        print("  python universal_downloader.py batch_download <urls_json>")
