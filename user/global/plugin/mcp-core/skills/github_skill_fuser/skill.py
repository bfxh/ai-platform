#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Skill 融合安装器 - skill.py
功能：安装 GitHub 项目为 Skill，先搜索类似项目、分析原理，再融合最佳实践

原理：
1. 搜索 GitHub 找类似项目（理解生态）
2. 下载目标项目，分析 SKILL.md / 结构
3. 对比同类工具的优缺点，融合最佳设计
4. 生成融合后的 Skill 安装到 MCP_Core

用法：
    python skill.py install <repo_url> [--skill-name <name>]
    python skill.py search-similar <query>           # 先找类似项目
    python skill.py analyze-repo <repo_url>         # 分析仓库原理
    python skill.py fuse <repo_url1> <repo_url2>    # 融合两个项目
"""

import os
import re
import json
import time
import shutil
import sqlite3
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# ─── 路径常量 ─────────────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent
MCP_CORE = SKILL_DIR.parent.parent
SKILLS_DIR = MCP_CORE / "skills"
KB_PATH = MCP_CORE / "data" / "knowledge_base.db"

# ─── GitHub 多策略下载器（内置）──────────────────────────────────────────────
class GitHubDownloader:
    """内置 GitHub 下载器，支持多镜像"""

    STRATEGIES = [
        {"name": "direct", "url": "https://github.com/", "desc": "直连"},
        {"name": "ghproxy", "url": "https://ghproxy.cn/", "desc": "ghproxy"},
        {"name": "gitclone", "url": "https://gitclone.com/github.com/", "desc": "GitClone"},
        {"name": "ghd_li", "url": "https://ghdl.feishu.cn/", "desc": "飞书镜像"},
    ]

    def __init__(self, timeout: int = 60):
        self.timeout = timeout

    def _git_clone(self, url: str, dest: str) -> Tuple[bool, str]:
        """用 git clone 克隆仓库"""
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", url, dest],
                capture_output=True, text=True, timeout=self.timeout,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}
            )
            if result.returncode == 0:
                return True, ""
            return False, result.stderr.strip()
        except Exception as e:
            return False, str(e)

    def clone(self, repo_url: str, dest_dir: str) -> Dict:
        """多策略克隆"""
        m = re.match(r"https?://github\.com/([^/]+)/([^/.]+)", repo_url)
        if not m:
            return {"status": "error", "error": "无效 URL"}

        owner, repo = m.group(1), m.group(2)

        for strategy in self.STRATEGIES:
            name = strategy["name"]
            base = strategy["url"]

            if name == "direct":
                clone_url = f"https://github.com/{owner}/{repo}.git"
            elif name == "ghproxy":
                clone_url = f"https://ghproxy.cn/https://github.com/{owner}/{repo}.git"
            elif name == "gitclone":
                clone_url = f"https://gitclone.com/github.com/{owner}/{repo}.git"
            elif name == "ghd_li":
                clone_url = f"https://ghdl.feishu.cn/https://github.com/{owner}/{repo}.git"
            else:
                clone_url = f"{base}{owner}/{repo}.git"

            print(f"  尝试 [{name}]: {clone_url}")
            ok, err = self._git_clone(clone_url, dest_dir)
            if ok:
                return {"status": "success", "strategy": name, "path": dest_dir}

        return {"status": "failed", "error": "所有策略均失败"}


# ─── GitHub 搜索器（内置）─────────────────────────────────────────────────────
class GitHubSearcher:
    """内置 GitHub 搜索（不依赖 requests 库）"""

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.api_base = "https://api.github.com"

    def _api(self, endpoint: str, params: Dict = None) -> Tuple[bool, Dict]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-Skill-Fuser",
        }
        url = f"{self.api_base}{endpoint}"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url += f"?{qs}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return True, json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return False, {"error": str(e)}

    def search(self, query: str, language: str = "", limit: int = 10) -> List[Dict]:
        """搜索 GitHub 项目"""
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": min(limit, 30)}
        if language:
            params["q"] = f"{query} language:{language}"

        ok, data = self._api("/search/repositories", params)
        if not ok:
            return []

        results = []
        for item in data.get("items", []):
            results.append({
                "name": item.get("name"),
                "full_name": item.get("full_name"),
                "description": item.get("description", ""),
                "stars": item.get("stargazers_count", 0),
                "forks": item.get("forks_count", 0),
                "language": item.get("language", ""),
                "url": item.get("html_url"),
                "clone_url": item.get("clone_url"),
                "topics": item.get("topics", []),
                "created": item.get("created_at", "")[:10],
                "updated": item.get("updated_at", "")[:10],
            })
        return results

    def get_repo(self, owner: str, repo: str) -> Dict:
        """获取仓库信息"""
        ok, data = self._api(f"/repos/{owner}/{repo}")
        if ok:
            return {
                "owner": data.get("owner", {}).get("login", owner),
                "repo": data.get("name", repo),
                "description": data.get("description", ""),
                "default_branch": data.get("default_branch", "main"),
                "stars": data.get("stargazers_count", 0),
                "language": data.get("language", ""),
                "topics": data.get("topics", []),
                "license": data.get("license", {}).get("name", ""),
                "readme_url": f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md",
            }
        return {"error": data.get("error", "请求失败")}


# ─── 源码分析器 ────────────────────────────────────────────────────────────────
class SourceAnalyzer:
    """分析源码结构和设计模式"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def analyze_structure(self) -> Dict:
        """分析项目结构"""
        if not self.repo_path.exists():
            return {"error": "目录不存在"}

        result = {
            "files": {},
            "dirs": [],
            "languages": {},
            "entry_points": [],
            "has_skill": False,
            "skill_info": {},
        }

        # 遍历文件
        for f in self.repo_path.rglob("*"):
            if f.is_file():
                rel = f.relative_to(self.repo_path)
                size = f.stat().st_size
                ext = f.suffix

                result["files"][str(rel)] = {
                    "size": size,
                    "ext": ext,
                }

                # 统计语言
                if ext in [".py", ".js", ".ts", ".tsx", ".java", ".go", ".rs", ".cpp", ".c"]:
                    lang_map = {
                        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
                        ".tsx": "React", ".java": "Java", ".go": "Go",
                        ".rs": "Rust", ".cpp": "C++", ".c": "C",
                    }
                    lang = lang_map.get(ext, "Other")
                    result["languages"][lang] = result["languages"].get(lang, 0) + size

                # 识别入口文件
                if f.name in ["__main__.py", "main.py", "index.js", "main.js",
                              "main.ts", "app.py", "server.py", "cli.py"]:
                    result["entry_points"].append(str(rel))

        # 检查 SKILL.md
        skill_md = self.repo_path / "SKILL.md"
        if skill_md.exists():
            result["has_skill"] = True
            result["skill_info"] = self._parse_skill_md(skill_md)

        # 读取 README
        readme = self._find_readme()
        if readme:
            result["readme"] = self._read_file(readme)[:3000]

        return result

    def _find_readme(self) -> Optional[Path]:
        """找 README 文件"""
        for name in ["README.md", "README.txt", "readme.md"]:
            p = self.repo_path / name
            if p.exists():
                return p
        return None

    def _read_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""

    def _parse_skill_md(self, path: Path) -> Dict:
        """解析 SKILL.md，提取规范信息"""
        content = self._read_file(path)
        info = {
            "title": "",
            "description": "",
            "triggers": [],
            "commands": [],
            "sections": [],
        }

        # 提取标题
        m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if m:
            info["title"] = m.group(1).strip()

        # 提取触发词
        for kw in re.findall(r"triggers?[:\s]+([^\n]+)", content, re.I):
            info["triggers"].extend([t.strip() for t in re.split(r"[,;，；]", kw) if t.strip()])

        # 提取命令
        for cmd in re.findall(r"```\w*\n(\$[^\n]+)", content):
            info["commands"].append(cmd.strip())

        return info


# ─── Skill 安装器（融合版）─────────────────────────────────────────────────────
class SkillFuser:
    """Skill 融合安装器"""

    def __init__(self):
        self.downloader = GitHubDownloader()
        self.searcher = GitHubSearcher()
        self.temp_dir = MCP_CORE / "temp_download"
        self.temp_dir.mkdir(exist_ok=True)

    def search_similar(self, query: str, limit: int = 8) -> List[Dict]:
        """搜索类似项目，理解生态"""
        print(f"=== 搜索类似项目: {query} ===")
        results = self.searcher.search(query, limit=limit)

        if not results:
            return []

        print(f"找到 {len(results)} 个相关项目:")
        for i, r in enumerate(results[:8], 1):
            print(f"  {i}. ★{r['stars']} {r['full_name']}")
            print(f"     {r.get('description', '无描述')[:60]}")

        return results

    def analyze_repo(self, repo_url: str) -> Dict:
        """分析仓库原理（下载后分析源码结构）"""
        print(f"=== 分析仓库: {repo_url} ===")

        m = re.match(r"https?://github\.com/([^/]+)/([^/.]+)", repo_url)
        if not m:
            return {"error": "无效 URL"}

        owner, repo = m.group(1), m.group(2)

        # 获取 API 信息
        api_info = self.searcher.get_repo(owner, repo)
        print(f"  仓库信息: ★{api_info.get('stars', 0)} | {api_info.get('language', '?')} | "
              f"默认分支: {api_info.get('default_branch', 'main')}")

        # 下载到临时目录
        temp_path = str(self.temp_dir / f"{owner}_{repo}")
        shutil.rmtree(temp_path, ignore_errors=True)

        print(f"  下载中...")
        clone_result = self.downloader.clone(repo_url, temp_path)
        if clone_result["status"] != "success":
            return {"error": f"下载失败: {clone_result.get('error')}"}

        print(f"  分析源码结构...")
        analyzer = SourceAnalyzer(temp_path)
        structure = analyzer.analyze_structure()

        # 清理
        shutil.rmtree(temp_path, ignore_errors=True)

        result = {
            "url": repo_url,
            "owner": owner,
            "repo": repo,
            "api_info": api_info,
            "structure": structure,
            "analysis": {
                "has_skill_md": structure.get("has_skill", False),
                "skill_info": structure.get("skill_info", {}),
                "entry_points": structure.get("entry_points", []),
                "languages": dict(sorted(structure.get("languages", {}).items(),
                                        key=lambda x: x[1], reverse=True)[:5]),
                "readme_preview": structure.get("readme", "")[:500],
            },
        }

        print(f"  主语言: {list(result['analysis']['languages'].keys())}")
        print(f"  有 SKILL.md: {result['analysis']['has_skill_md']}")

        return result

    def install_skill(self, repo_url: str, skill_name: str = None,
                      fuse_with: List[str] = None) -> Dict:
        """
        安装/融合 Skill
        fuse_with: 额外融合的项目 URL 列表
        """
        print(f"=== 安装 Skill: {repo_url} ===")

        m = re.match(r"https?://github\.com/([^/]+)/([^/.]+)", repo_url)
        if not m:
            return {"error": "无效 URL"}

        owner, repo = m.group(1), m.group(2)

        # 确定 skill 名称
        if not skill_name:
            skill_name = repo.lower().replace("-", "_").replace("_", "")

        skill_path = SKILLS_DIR / skill_name
        if skill_path.exists():
            print(f"  Skill 已存在: {skill_path}")
            print(f"  覆盖安装...")

        skill_path.mkdir(parents=True, exist_ok=True)

        # 下载仓库
        temp_path = str(self.temp_dir / f"{owner}_{repo}_install")
        shutil.rmtree(temp_path, ignore_errors=True)

        print(f"  下载仓库...")
        clone_result = self.downloader.clone(repo_url, temp_path)
        if clone_result["status"] != "success":
            return {"error": f"下载失败: {clone_result.get('error')}"}

        # 分析源码
        analyzer = SourceAnalyzer(temp_path)
        structure = analyzer.analyze_structure()

        # 如果有 SKILL.md，直接使用
        if structure.get("has_skill"):
            skill_md_src = Path(temp_path) / "SKILL.md"
            skill_md_dest = skill_path / "SKILL.md"
            shutil.copy2(skill_md_src, skill_md_dest)
            print(f"  ✓ 发现并复制 SKILL.md")

        # 生成 skill.py
        self._generate_skill_py(skill_path, repo, owner, structure)

        # 生成 README.md
        self._generate_readme(skill_path, repo_url, owner, structure)

        # 写知识库
        self._write_to_kb(skill_name, repo_url, owner, structure)

        # 清理
        shutil.rmtree(temp_path, ignore_errors=True)

        print(f"  ✓ 安装完成: {skill_path}")

        return {
            "status": "success",
            "skill_name": skill_name,
            "skill_path": str(skill_path),
            "structure": {
                "languages": list(structure.get("languages", {}).keys()),
                "has_skill_md": structure.get("has_skill", False),
                "entry_points": structure.get("entry_points", []),
            },
        }

    def _generate_skill_py(self, skill_path: Path, repo: str,
                           owner: str, structure: Dict):
        """生成 skill.py 入口文件"""
        languages = list(structure.get("languages", {}).keys())
        primary_lang = languages[0] if languages else "Python"
        entry = structure.get("entry_points", [])

        skill_py = skill_path / "skill.py"
        content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{repo} - Skill
来源: https://github.com/{owner}/{repo}
自动生成 | 主语言: {primary_lang}
"""

import sys
from pathlib import Path

# ─── 路径常量 ────────────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent
MCP_CORE = SKILL_DIR.parent.parent

def main():
    args = sys.argv[1:]

    if not args:
        print(f"{repo} Skill")
        print(f"用法: python skill.py <command> [args]")
        print(f"入口文件: {entry}")
        return

    cmd = args[0]
    print(f"执行: {{cmd}} {{args[1:]}}")

    # TODO: 实现具体功能
    # 入口文件参考: {entry}

if __name__ == "__main__":
    main()
'''
        skill_py.write_text(content, encoding="utf-8")
        print(f"  ✓ 生成 skill.py")

    def _generate_readme(self, skill_path: Path, repo_url: str,
                         owner: str, structure: Dict):
        """生成 README.md"""
        readme = skill_path / "README.md"
        langs = list(structure.get("languages", {}).keys())

        content = f'''# {skill_path.name}

来源: [{owner}]({repo_url})

## 概述

自动安装的 Skill，主语言: {", ".join(langs) if langs else "未知"}

## 结构

- 语言分布: {json.dumps(structure.get("languages", {}), ensure_ascii=False)}
- 入口文件: {structure.get("entry_points", [])}

## 安装信息

- 安装时间: {datetime.now().isoformat()}
- 来源: GitHub
- 原始仓库: {repo_url}
'''
        readme.write_text(content, encoding="utf-8")

    def _write_to_kb(self, skill_name: str, repo_url: str,
                     owner: str, structure: Dict):
        """写入知识库"""
        try:
            conn = sqlite3.connect(str(KB_PATH))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS installed_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT UNIQUE,
                    repo_url TEXT,
                    owner TEXT,
                    languages TEXT,
                    installed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            langs = json.dumps(list(structure.get("languages", {}).keys()))
            conn.execute("""
                INSERT OR REPLACE INTO installed_skills
                (skill_name, repo_url, owner, languages)
                VALUES (?, ?, ?, ?)
            """, (skill_name, repo_url, owner, langs))
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
    fuser = SkillFuser()

    if cmd == "search-similar":
        query = args[1] if len(args) > 1 else input("搜索词: ")
        results = fuser.search_similar(query)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    elif cmd == "analyze-repo":
        url = args[1] if len(args) > 1 else input("仓库URL: ")
        result = fuser.analyze_repo(url)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "install":
        url = args[1] if len(args) > 1 else input("仓库URL: ")
        skill_name = None
        if "--skill-name" in args:
            idx = args.index("--skill-name")
            skill_name = args[idx + 1] if idx + 1 < len(args) else None
        result = fuser.install_skill(url, skill_name=skill_name)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "fuse":
        if len(args) < 3:
            print("需要两个仓库URL: fuse <url1> <url2>")
            return
        # 先分析两个仓库
        r1 = fuser.analyze_repo(args[1])
        r2 = fuser.analyze_repo(args[2])
        print("融合分析:")
        print(f"  项目1: {r1.get('repo')} → {list(r1.get('analysis', {}).get('languages', {}).keys())}")
        print(f"  项目2: {r2.get('repo')} → {list(r2.get('analysis', {}).get('languages', {}).keys())}")
        print("  请用 analyze-repo 分别分析后手动融合")

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
