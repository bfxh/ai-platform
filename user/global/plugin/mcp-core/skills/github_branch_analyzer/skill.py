#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 分支分析器 - skill.py
功能：分析仓库的分支结构，理解各分支的用途、关系和原理

原理：
1. GitHub 分支 = 指针（commit SHA）的引用
2. 默认分支（main/master）= 仓库的主线
3. 分支类型：长期分支（main/dev）、特性分支（feature/）、发布分支（release/）、热修复分支（hotfix/）
4. 分析分支命名规范判断分支用途
5. 对比分支差异（diverged/ahead/behind）

用法：
    python skill.py analyze <repo_url>              # 完整分析
    python skill.py branches <repo_url>             # 只看分支列表
    python skill.py compare <repo_url> <branch1> <branch2>  # 比较分支
    python skill.py tree <repo_url>                 # 显示分支树
"""

import re
import json
import time
import sqlite3
import urllib.request
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# ─── 路径常量 ─────────────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent
MCP_CORE = SKILL_DIR.parent.parent
KB_PATH = MCP_CORE / "data" / "knowledge_base.db"


# ─── 分支类型识别规则 ────────────────────────────────────────────────────────
BRANCH_TYPE_PATTERNS = [
    # (正则, 类型, 优先级, 描述)
    (r"^(main|master|mainline)$", "main", 0, "主分支 - 稳定版本，所有合并的目标"),
    (r"^(dev|development|develop)$", "dev", 1, "开发分支 - 下一版本的集成分支"),
    (r"^release[/v]?(\d+)", "release", 2, "发布分支 - 准备发布的版本快照"),
    (r"^hotfix[/]?", "hotfix", 3, "热修复分支 - 紧急修复，从主分支分出"),
    (r"^feature[/]?", "feature", 4, "特性分支 - 开发新功能的临时分支"),
    (r"^fix[/]?", "fix", 5, "修复分支 - 修复特定问题的临时分支"),
    (r"^refactor[/]?", "refactor", 6, "重构分支 - 代码重构"),
    (r"^test[/]?", "test", 7, "测试分支 - 测试实验"),
    (r"^docs?[/]?", "docs", 8, "文档分支 - 文档更新"),
    (r"^build[/]?|ci[-_]?", "ci_cd", 9, "CI/CD 分支 - 自动化构建"),
    (r"^experiment[/]?", "experiment", 10, "实验分支 - 探索性开发"),
]


def classify_branch(name: str) -> Dict:
    """识别分支类型和用途"""
    for pattern, btype, priority, desc in BRANCH_TYPE_PATTERNS:
        if re.match(pattern, name, re.IGNORECASE):
            return {
                "name": name,
                "type": btype,
                "priority": priority,
                "description": desc,
                "is_long_term": btype in ["main", "dev", "release", "hotfix"],
            }
    return {
        "name": name,
        "type": "unknown",
        "priority": 99,
        "description": "未分类分支",
        "is_long_term": False,
    }


def parse_branch_name(name: str) -> Dict:
    """解析分支名称，提取元信息"""
    info = {
        "original": name,
        "category": "unknown",
        "issue_ref": None,
        "author_prefix": None,
        "description": name,
    }

    # issue 引用
    m = re.match(r"(.+?)[-_]#(\d+)", name)
    if m:
        info["issue_ref"] = int(m.group(2))
        info["description"] = m.group(1).strip("-_")

    # 作者前缀
    m = re.match(r"([a-zA-Z0-9]+)[-_]", name)
    if m:
        info["author_prefix"] = m.group(1)

    # 分类
    cls = classify_branch(name)
    info["category"] = cls["type"]
    info["description"] = cls["description"]

    return info


class GitHubBranchAnalyzer:
    """GitHub 分支分析器"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.api_base = "https://api.github.com"

    def _api_request(self, url: str) -> Tuple[bool, Dict]:
        """发送 GitHub API 请求"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-Branch-Analyzer",
        }

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return True, json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return False, {"error": str(e)}

    def get_repo_info(self, owner: str, repo: str) -> Dict:
        """获取仓库基本信息"""
        url = f"{self.api_base}/repos/{owner}/{repo}"
        ok, data = self._api_request(url)
        if ok:
            return {
                "owner": data.get("owner", {}).get("login", owner),
                "repo": data.get("name", repo),
                "description": data.get("description", ""),
                "default_branch": data.get("default_branch", "main"),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "language": data.get("language", ""),
                "license": data.get("license", {}).get("name", ""),
                "topics": data.get("topics", []),
                "url": data.get("html_url", ""),
            }
        return {"error": data.get("error", "请求失败")}

    def get_all_branches(self, owner: str, repo: str) -> List[Dict]:
        """获取所有分支"""
        branches = []
        page = 1

        while True:
            url = f"{self.api_base}/repos/{owner}/{repo}/branches?per_page=100&page={page}"
            ok, data = self._api_request(url)

            if not ok or not isinstance(data, list):
                break

            for b in data:
                branch_info = {
                    "name": b["name"],
                    "protected": b.get("protected", False),
                    "commit_sha": b["commit"]["sha"][:8],
                }
                # 分类
                cls = classify_branch(b["name"])
                branch_info.update(cls)
                branches.append(branch_info)

            if len(data) < 100:
                break
            page += 1
            time.sleep(0.3)  # 避免触发 rate limit

        return branches

    def get_default_branch(self, owner: str, repo: str) -> str:
        """获取默认分支名"""
        info = self.get_repo_info(owner, repo)
        return info.get("default_branch", "main")

    def compare_branches(self, owner: str, repo: str,
                         base: str, head: str) -> Dict:
        """比较两个分支的差异"""
        url = f"{self.api_base}/repos/{owner}/{repo}/compare/{base}...{head}"
        ok, data = self._api_request(url)

        if not ok:
            return {"error": data.get("error", "比较失败")}

        return {
            "base": base,
            "head": head,
            "status": data.get("status", "unknown"),
            "ahead_by": data.get("ahead_by", 0),
            "behind_by": data.get("behind_by", 0),
            "total_commits": data.get("total_commits", 0),
            "commits": [{
                "sha": c["sha"][:8],
                "message": c["commit"]["message"].split("\n")[0],
                "author": c["commit"]["author"]["name"],
                "date": c["commit"]["author"]["date"],
            } for c in data.get("commits", [])[:10]],
        }

    def get_branch_commits(self, owner: str, repo: str,
                           branch: str, limit: int = 30) -> List[Dict]:
        """获取分支的最近提交"""
        url = f"{self.api_base}/repos/{owner}/{repo}/commits?sha={branch}&per_page={limit}"
        ok, data = self._api_request(url)

        if not ok:
            return []

        return [{
            "sha": c["sha"][:8],
            "message": c["commit"]["message"].split("\n")[0],
            "author": c["commit"]["author"]["name"],
            "date": c["commit"]["author"]["date"],
            "url": c["html_url"],
        } for c in data[:limit]]

    def analyze_workflow(self, owner: str, repo: str) -> Dict:
        """
        分析仓库的分支工作流类型（理解原理）
        """
        branches = self.get_all_branches(owner, repo)
        branch_names = [b["name"] for b in branches]

        workflow_type = "unknown"
        workflow_desc = ""

        # GitFlow 检测
        has_main = any(re.match(r"^(main|master)$", n, re.I) for n in branch_names)
        has_dev = any(re.match(r"^(dev|development)$", n, re.I) for n in branch_names)
        has_release = any(re.match(r"^release", n, re.I) for n in branch_names)
        has_hotfix = any(re.match(r"^hotfix", n, re.I) for n in branch_names)

        if has_main and has_dev and has_release and has_hotfix:
            workflow_type = "gitflow"
            workflow_desc = ("GitFlow 工作流：main(稳定) + dev(开发) + "
                           "release(发布) + hotfix(热修复) + feature(特性)")
        elif has_main and has_dev:
            workflow_type = "trunk_based"
            workflow_desc = ("Trunk-Based 开发：main + dev，频繁集成到主干")
        elif has_main and not has_dev:
            workflow_type = "github_flow"
            workflow_desc = ("GitHub Flow：单一 main 分支，特性分支合并后删除")
        elif all(not has_main for _ in [1]):
            workflow_type = "custom"
            workflow_desc = "自定义分支策略"

        # 分支类型统计
        type_counts = {}
        for b in branches:
            t = b["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "workflow_type": workflow_type,
            "workflow_description": workflow_desc,
            "total_branches": len(branches),
            "branch_type_counts": type_counts,
            "long_term_branches": [b["name"] for b in branches if b["is_long_term"]],
            "feature_branches": [b["name"] for b in branches if b["type"] == "feature"],
        }

    def generate_branch_tree(self, owner: str, repo: str) -> str:
        """生成分支树的可视化文本"""
        branches = self.get_all_branches(owner, repo)
        default = self.get_default_branch(owner, repo)

        # 按类型分组
        groups = {}
        for b in branches:
            t = b["type"]
            if t not in groups:
                groups[t] = []
            groups[t].append(b)

        lines = [f"仓库: {owner}/{repo} (默认分支: {default})",
                 "=" * 50]

        # 按优先级排序
        priority_order = ["main", "dev", "release", "hotfix", "feature",
                         "fix", "refactor", "test", "docs", "ci_cd",
                         "experiment", "unknown"]

        for btype in priority_order:
            if btype not in groups:
                continue
            bs = groups[btype]
            if btype == "main":
                lines.append(f"\n★ 主分支:")
            elif btype == "dev":
                lines.append(f"\n◆ 开发分支:")
            else:
                lines.append(f"\n◇ {btype} ({len(bs)}个):")

            for b in bs[:5]:  # 每类最多显示5个
                marker = "🔒" if b["protected"] else "  "
                lines.append(f"  {marker} {b['name']} → {b['commit_sha']}")
            if len(bs) > 5:
                lines.append(f"  ... 还有 {len(bs) - 5} 个分支")

        return "\n".join(lines)


class BranchAnalyzer:
    """完整的分支分析器（整合工具）"""

    def __init__(self):
        self.github = GitHubBranchAnalyzer()

    def analyze(self, repo_url: str, deep: bool = True) -> Dict:
        """完整分析仓库分支结构"""
        m = re.match(r"https?://github\.com/([^/]+)/([^/.]+)", repo_url)
        if not m:
            return {"error": "无效的 GitHub 仓库 URL"}

        owner, repo = m.group(1), m.group(2)

        result = {
            "url": repo_url,
            "owner": owner,
            "repo": repo,
            "timestamp": datetime.now().isoformat(),
        }

        # 1. 仓库信息
        print("获取仓库信息...")
        result["repo_info"] = self.github.get_repo_info(owner, repo)

        # 2. 所有分支
        print("获取分支列表...")
        branches = self.github.get_all_branches(owner, repo)
        result["branches"] = branches
        result["branch_count"] = len(branches)

        # 3. 分支分类
        print("分析分支类型...")
        type_stats = {}
        for b in branches:
            t = b["type"]
            if t not in type_stats:
                type_stats[t] = {"count": 0, "branches": [], "protected": 0}
            type_stats[t]["count"] += 1
            if b["protected"]:
                type_stats[t]["protected"] += 1
            type_stats[t]["branches"].append(b["name"])

        result["branch_type_stats"] = type_stats

        # 4. 工作流分析
        print("分析工作流模式...")
        result["workflow"] = self.github.analyze_workflow(owner, repo)

        # 5. 默认分支详情
        default = result["repo_info"].get("default_branch", "main")
        result["default_branch_info"] = {
            "name": default,
            "commits": self.github.get_branch_commits(owner, repo, default, 5)
        }

        # 6. 打印摘要
        print("\n" + self.github.generate_branch_tree(owner, repo))

        # 7. 写知识库
        self._write_to_kb(result)

        return result

    def _write_to_kb(self, result: Dict):
        """写入知识库"""
        try:
            conn = sqlite3.connect(str(KB_PATH))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS github_branch_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner TEXT,
                    repo TEXT,
                    url TEXT,
                    default_branch TEXT,
                    branch_count INTEGER,
                    workflow_type TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                INSERT INTO github_branch_analysis
                (owner, repo, url, default_branch, branch_count, workflow_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                result["owner"], result["repo"], result["url"],
                result["repo_info"].get("default_branch", ""),
                result["branch_count"],
                result["workflow"].get("workflow_type", ""),
            ))
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

    if cmd == "analyze":
        url = args[1] if len(args) > 1 else input("仓库URL: ")
        analyzer = BranchAnalyzer()
        result = analyzer.analyze(url)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "branches":
        url = args[1] if len(args) > 1 else input("仓库URL: ")
        m = re.match(r"https?://github\.com/([^/]+)/([^/.]+)", url)
        if not m:
            print("无效 URL")
            return
        owner, repo = m.group(1), m.group(2)
        gh = GitHubBranchAnalyzer()
        branches = gh.get_all_branches(owner, repo)
        print(f"共 {len(branches)} 个分支:")
        for b in branches:
            print(f"  {'🔒' if b['protected'] else '  '} {b['name']} ({b['type']})")

    elif cmd == "compare":
        url = args[1] if len(args) > 1 else input("仓库URL: ")
        b1 = args[2] if len(args) > 2 else input("分支1: ")
        b2 = args[3] if len(args) > 3 else input("分支2: ")
        m = re.match(r"https?://github\.com/([^/]+)/([^/.]+)", url)
        if not m:
            print("无效 URL")
            return
        owner, repo = m.group(1), m.group(2)
        gh = GitHubBranchAnalyzer()
        result = gh.compare_branches(owner, repo, b1, b2)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "tree":
        url = args[1] if len(args) > 1 else input("仓库URL: ")
        m = re.match(r"https?://github\.com/([^/]+)/([^/.]+)", url)
        if not m:
            print("无效 URL")
            return
        owner, repo = m.group(1), m.group(2)
        gh = GitHubBranchAnalyzer()
        tree = gh.generate_branch_tree(owner, repo)
        print(tree)

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
