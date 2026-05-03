#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 仓库管理器
GitHub Repository Manager

功能:
- 仓库克隆
- 批量下载
- 仓库分析
- 依赖管理
- 自动同步

用法:
    python github_repo_manager.py clone <repo_url>
    python github_repo_manager.py batch <repos_file>
    python github_repo_manager.py analyze <repo_path>
    python github_repo_manager.py sync <repo_path>
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

AI_ROOT = Path("/python")
GITHUB_DIR = AI_ROOT / "GitHub"
REPOS_DIR = GITHUB_DIR / "repos"
CONFIG_DIR = AI_ROOT / "Config"


class GitHubRepoManager:
    """GitHub仓库管理器"""

    def __init__(self):
        self.config = self._load_config()
        GITHUB_DIR.mkdir(parents=True, exist_ok=True)
        REPOS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict:
        """加载配置"""
        config_file = CONFIG_DIR / "github_config.json"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "default_clone_depth": 1,
            "auto_pull": True,
            "backup_enabled": True,
            "backup_dir": str(GITHUB_DIR / "backups"),
        }

    def _save_config(self):
        """保存配置"""
        config_file = CONFIG_DIR / "github_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def clone_repository(self, repo_url: str, target_dir: str = None, depth: int = None) -> bool:
        """克隆仓库"""
        print("\n" + "=" * 60)
        print("克隆 GitHub 仓库")
        print("=" * 60 + "\n")

        # 解析仓库名称
        parsed = urlparse(repo_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            owner, repo_name = path_parts[0], path_parts[1].replace(".git", "")
        else:
            print(f"错误: 无法解析仓库URL: {repo_url}")
            return False

        # 确定目标目录
        if target_dir is None:
            target_dir = REPOS_DIR / owner / repo_name
        else:
            target_dir = Path(target_dir)

        print(f"仓库: {owner}/{repo_name}")
        print(f"URL: {repo_url}")
        print(f"目标: {target_dir}")

        # 检查目标目录是否已存在
        if target_dir.exists():
            print(f"\n目标目录已存在: {target_dir}")
            response = input("是否更新? (y/n): ").lower()
            if response == "y":
                return self.update_repository(target_dir)
            return False

        # 创建父目录
        target_dir.parent.mkdir(parents=True, exist_ok=True)

        # 克隆参数
        depth = depth or self.config.get("default_clone_depth", 1)

        try:
            cmd = ["git", "clone", "--depth", str(depth)]
            cmd.extend([repo_url, str(target_dir)])

            print(f"\n执行: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f"✅ 克隆成功: {target_dir}")

                # 保存仓库信息
                self._save_repo_info(
                    target_dir,
                    {
                        "url": repo_url,
                        "owner": owner,
                        "name": repo_name,
                        "cloned_at": datetime.now().isoformat(),
                    },
                )

                return True
            else:
                print(f"❌ 克隆失败: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ 克隆超时")
            return False
        except Exception as e:
            print(f"❌ 克隆错误: {e}")
            return False

    def update_repository(self, repo_path: Path) -> bool:
        """更新仓库"""
        print(f"\n更新仓库: {repo_path}")

        if not (repo_path / ".git").exists():
            print("❌ 不是有效的git仓库")
            return False

        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)

            # 获取当前分支
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            current_branch = result.stdout.strip()
            print(f"当前分支: {current_branch}")

            # 拉取更新
            result = subprocess.run(
                ["git", "pull", "origin", current_branch], capture_output=True, text=True
            )

            if result.returncode == 0:
                print(f"✅ 更新成功")
                print(result.stdout)
                return True
            else:
                print(f"❌ 更新失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ 更新错误: {e}")
            return False
        finally:
            os.chdir(original_cwd)

    def batch_clone(self, repos_file: str) -> Dict:
        """批量克隆"""
        print("\n" + "=" * 60)
        print("批量克隆仓库")
        print("=" * 60 + "\n")

        repos_path = Path(repos_file)
        if not repos_path.exists():
            print(f"错误: 文件不存在: {repos_file}")
            return {"success": [], "failed": []}

        # 读取仓库列表
        with open(repos_path, "r", encoding="utf-8") as f:
            repos = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        print(f"找到 {len(repos)} 个仓库\n")

        success = []
        failed = []

        for i, repo_url in enumerate(repos, 1):
            print(f"\n[{i}/{len(repos)}] 处理: {repo_url}")

            if self.clone_repository(repo_url):
                success.append(repo_url)
            else:
                failed.append(repo_url)

        print("\n" + "=" * 60)
        print(f"批量克隆完成: {len(success)} 成功, {len(failed)} 失败")
        print("=" * 60 + "\n")

        return {"success": success, "failed": failed}

    def analyze_repository(self, repo_path: str) -> Dict:
        """分析仓库"""
        print("\n" + "=" * 60)
        print("分析仓库")
        print("=" * 60 + "\n")

        repo_path = Path(repo_path)
        if not repo_path.exists():
            print(f"错误: 路径不存在: {repo_path}")
            return {}

        analysis = {
            "path": str(repo_path),
            "analyzed_at": datetime.now().isoformat(),
            "is_git_repo": (repo_path / ".git").exists(),
            "files": {},
            "languages": {},
            "size_mb": 0,
        }

        # 统计文件
        for item in repo_path.rglob("*"):
            if item.is_file():
                # 跳过.git目录
                if ".git" in str(item):
                    continue

                # 文件类型统计
                suffix = item.suffix.lower()
                if suffix:
                    analysis["files"][suffix] = analysis["files"].get(suffix, 0) + 1

                # 文件大小
                try:
                    analysis["size_mb"] += item.stat().st_size / (1024 * 1024)
                except:
                    pass

        # 语言映射
        lang_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".go": "Go",
            ".rs": "Rust",
            ".md": "Markdown",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".html": "HTML",
            ".css": "CSS",
        }

        for ext, count in analysis["files"].items():
            lang = lang_map.get(ext, "Other")
            analysis["languages"][lang] = analysis["languages"].get(lang, 0) + count

        # 显示结果
        print(f"路径: {analysis['path']}")
        print(f"Git仓库: {'是' if analysis['is_git_repo'] else '否'}")
        print(f"总大小: {analysis['size_mb']:.2f} MB")
        print(f"\n文件类型:")
        for ext, count in sorted(analysis["files"].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ext:10} {count:5} 个文件")

        print(f"\n编程语言:")
        for lang, count in sorted(analysis["languages"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {lang:15} {count:5} 个文件")

        return analysis

    def sync_repository(self, repo_path: str) -> bool:
        """同步仓库"""
        print("\n" + "=" * 60)
        print("同步仓库")
        print("=" * 60 + "\n")

        repo_path = Path(repo_path)

        # 检查是否是git仓库
        if not (repo_path / ".git").exists():
            print("❌ 不是有效的git仓库")
            return False

        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)

            # 获取远程信息
            result = subprocess.run(
                ["git", "remote", "-v"], capture_output=True, text=True, check=True
            )
            print(f"远程仓库:\n{result.stdout}")

            # 获取状态
            result = subprocess.run(
                ["git", "status", "-sb"], capture_output=True, text=True, check=True
            )
            print(f"\n当前状态:\n{result.stdout}")

            # 拉取更新
            print("\n拉取远程更新...")
            result = subprocess.run(["git", "pull"], capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ 同步成功")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                print(f"❌ 同步失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ 同步错误: {e}")
            return False
        finally:
            os.chdir(original_cwd)

    def list_repositories(self) -> List[Dict]:
        """列出所有仓库"""
        print("\n" + "=" * 60)
        print("已克隆的仓库")
        print("=" * 60 + "\n")

        repos = []

        for owner_dir in REPOS_DIR.iterdir():
            if owner_dir.is_dir():
                for repo_dir in owner_dir.iterdir():
                    if repo_dir.is_dir() and (repo_dir / ".git").exists():
                        repo_info = self._load_repo_info(repo_dir)
                        repos.append(
                            {
                                "path": str(repo_dir),
                                "owner": owner_dir.name,
                                "name": repo_dir.name,
                                "info": repo_info,
                            }
                        )

        if repos:
            print(f"找到 {len(repos)} 个仓库:\n")
            for repo in repos:
                print(f"  {repo['owner']}/{repo['name']}")
                print(f"    路径: {repo['path']}")
                if repo["info"]:
                    print(f"    克隆时间: {repo['info'].get('cloned_at', '未知')}")
                print()
        else:
            print("没有找到仓库")

        return repos

    def _save_repo_info(self, repo_path: Path, info: Dict):
        """保存仓库信息"""
        info_file = repo_path / ".repo_info.json"
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)

    def _load_repo_info(self, repo_path: Path) -> Dict:
        """加载仓库信息"""
        info_file = repo_path / ".repo_info.json"
        if info_file.exists():
            with open(info_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def create_batch_file(self, output_file: str = None) -> str:
        """创建批量克隆文件模板"""
        if output_file is None:
            output_file = GITHUB_DIR / "repos_to_clone.txt"

        template = """# GitHub 仓库批量克隆列表
# 每行一个仓库URL
# 以 # 开头的行会被忽略

# AI/ML 相关
https://github.com/microsoft/DeepSpeed
https://github.com/huggingface/transformers
https://github.com/openai/openai-python

# MCP 相关
https://github.com/modelcontextprotocol/python-sdk

# 工具类
https://github.com/yt-dlp/yt-dlp
https://github.com/pytube/pytube
"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(template)

        print(f"批量克隆模板已创建: {output_file}")
        return str(output_file)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python github_repo_manager.py <命令>")
        print("命令:")
        print("  clone <url> [target]     克隆仓库")
        print("  batch <file>            批量克隆")
        print("  analyze <path>          分析仓库")
        print("  sync <path>             同步仓库")
        print("  list                    列出仓库")
        print("  create_batch            创建批量文件模板")
        return

    manager = GitHubRepoManager()
    command = sys.argv[1]

    if command == "clone" and len(sys.argv) >= 3:
        url = sys.argv[2]
        target = sys.argv[3] if len(sys.argv) >= 4 else None
        manager.clone_repository(url, target)

    elif command == "batch" and len(sys.argv) >= 3:
        repos_file = sys.argv[2]
        manager.batch_clone(repos_file)

    elif command == "analyze" and len(sys.argv) >= 3:
        repo_path = sys.argv[2]
        manager.analyze_repository(repo_path)

    elif command == "sync" and len(sys.argv) >= 3:
        repo_path = sys.argv[2]
        manager.sync_repository(repo_path)

    elif command == "list":
        manager.list_repositories()

    elif command == "create_batch":
        manager.create_batch_file()

    else:
        print(f"未知命令或参数不足: {command}")


if __name__ == "__main__":
    main()
