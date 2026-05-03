#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 插件市场

功能:
- 插件搜索和安装
- 版本管理
- 用户评价系统
- 自动更新
"""

import json
import os
import shutil
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
import hashlib
import requests


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    rating: float = 0.0
    download_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    icon: str = ""
    homepage: str = ""
    repository: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "rating": self.rating,
            "download_count": self.download_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "icon": self.icon,
            "homepage": self.homepage,
            "repository": self.repository,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PluginMetadata":
        return cls(**data)


@dataclass
class PluginReview:
    """插件评价"""
    user: str
    rating: int
    comment: str
    created_at: str

    def to_dict(self) -> dict:
        return {
            "user": self.user,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at,
        }


class PluginRepository:
    """插件仓库"""

    def __init__(self, repo_url: str = None):
        self.repo_url = repo_url or "https://mcp-marketplace.example.com"
        self.plugins: Dict[str, PluginMetadata] = {}
        self.reviews: Dict[str, List[PluginReview]] = {}
        self._load_local_cache()

    def _load_local_cache(self):
        """加载本地缓存"""
        cache_file = Path("plugin_cache.json")
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for name, meta in data.get("plugins", {}).items():
                        self.plugins[name] = PluginMetadata.from_dict(meta)
            except Exception as e:
                print(f"加载缓存失败: {e}")

    def _save_local_cache(self):
        """保存本地缓存"""
        try:
            data = {
                "plugins": {
                    name: meta.to_dict() for name, meta in self.plugins.items()
                }
            }
            with open("plugin_cache.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")

    def search_plugins(
        self,
        query: str = "",
        category: str = None,
        tags: List[str] = None,
        min_rating: float = 0.0,
    ) -> List[PluginMetadata]:
        """搜索插件"""
        results = []

        for name, meta in self.plugins.items():
            # 关键词匹配
            if query and query.lower() not in name.lower():
                if query.lower() not in meta.description.lower():
                    continue

            # 分类过滤
            if category and meta.category != category:
                continue

            # 标签过滤
            if tags and not all(tag in meta.tags for tag in tags):
                continue

            # 评分过滤
            if meta.rating < min_rating:
                continue

            results.append(meta)

        # 按评分和下载量排序
        results.sort(key=lambda x: (x.rating, x.download_count), reverse=True)
        return results

    def get_plugin(self, name: str) -> Optional[PluginMetadata]:
        """获取插件信息"""
        return self.plugins.get(name)

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for meta in self.plugins.values():
            categories.add(meta.category)
        return sorted(list(categories))

    def get_tags(self) -> List[str]:
        """获取所有标签"""
        tags = set()
        for meta in self.plugins.values():
            tags.update(meta.tags)
        return sorted(list(tags))

    def add_plugin(self, metadata: PluginMetadata):
        """添加插件到仓库"""
        self.plugins[metadata.name] = metadata
        self._save_local_cache()

    def update_plugin(self, name: str, metadata: PluginMetadata):
        """更新插件信息"""
        if name in self.plugins:
            self.plugins[name] = metadata
            self._save_local_cache()

    def remove_plugin(self, name: str):
        """从仓库移除插件"""
        if name in self.plugins:
            del self.plugins[name]
            self._save_local_cache()


class PluginInstaller:
    """插件安装器"""

    def __init__(self, install_dir: str = "plugins"):
        self.install_dir = Path(install_dir)
        self.install_dir.mkdir(exist_ok=True)
        self.temp_dir = Path("temp_plugins")
        self.temp_dir.mkdir(exist_ok=True)

    def install(self, plugin_name: str, source: str, progress_callback: Callable = None) -> dict:
        """安装插件"""
        try:
            if progress_callback:
                progress_callback("downloading", 0)

            # 下载插件
            download_path = self._download_plugin(source, plugin_name)

            if progress_callback:
                progress_callback("extracting", 50)

            # 解压插件
            extract_dir = self._extract_plugin(download_path, plugin_name)

            if progress_callback:
                progress_callback("installing", 75)

            # 安装到目标目录
            target_dir = self.install_dir / plugin_name
            if target_dir.exists():
                shutil.rmtree(target_dir)

            shutil.move(str(extract_dir), str(target_dir))

            if progress_callback:
                progress_callback("completed", 100)

            # 清理临时文件
            download_path.unlink(missing_ok=True)

            return {
                "success": True,
                "message": f"插件 '{plugin_name}' 安装成功",
                "install_path": str(target_dir),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"安装失败: {str(e)}",
            }

    def uninstall(self, plugin_name: str) -> dict:
        """卸载插件"""
        target_dir = self.install_dir / plugin_name

        if not target_dir.exists():
            return {
                "success": False,
                "error": f"插件 '{plugin_name}' 未安装",
            }

        try:
            shutil.rmtree(target_dir)
            return {
                "success": True,
                "message": f"插件 '{plugin_name}' 已卸载",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"卸载失败: {str(e)}",
            }

    def update(self, plugin_name: str, source: str, progress_callback: Callable = None) -> dict:
        """更新插件"""
        # 先卸载旧版本
        uninstall_result = self.uninstall(plugin_name)
        if not uninstall_result["success"]:
            return uninstall_result

        # 安装新版本
        return self.install(plugin_name, source, progress_callback)

    def _download_plugin(self, source: str, plugin_name: str) -> Path:
        """下载插件"""
        if source.startswith("http"):
            # 从 URL 下载
            response = requests.get(source, stream=True, timeout=60)
            response.raise_for_status()

            download_path = self.temp_dir / f"{plugin_name}.zip"
            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return download_path
        else:
            # 本地文件
            return Path(source)

    def _extract_plugin(self, zip_path: Path, plugin_name: str) -> Path:
        """解压插件"""
        extract_dir = self.temp_dir / plugin_name

        if extract_dir.exists():
            shutil.rmtree(extract_dir)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        return extract_dir

    def list_installed(self) -> List[dict]:
        """列出已安装的插件"""
        installed = []

        for item in self.install_dir.iterdir():
            if item.is_dir():
                # 尝试读取插件信息
                manifest_file = item / "manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                            installed.append({
                                "name": item.name,
                                "version": manifest.get("version", "unknown"),
                                "description": manifest.get("description", ""),
                                "install_time": manifest.get("install_time", ""),
                            })
                    except Exception:
                        installed.append({
                            "name": item.name,
                            "version": "unknown",
                            "description": "",
                        })

        return installed


class PluginUpdater:
    """插件更新器"""

    def __init__(self, repository: PluginRepository, installer: PluginInstaller):
        self.repository = repository
        self.installer = installer

    def check_updates(self) -> List[dict]:
        """检查可用更新"""
        updates = []
        installed = self.installer.list_installed()

        for plugin in installed:
            name = plugin["name"]
            current_version = plugin["version"]

            # 获取仓库中的最新版本
            repo_plugin = self.repository.get_plugin(name)
            if repo_plugin and repo_plugin.version != current_version:
                updates.append({
                    "name": name,
                    "current_version": current_version,
                    "latest_version": repo_plugin.version,
                    "description": repo_plugin.description,
                })

        return updates

    def update_all(self, progress_callback: Callable = None) -> dict:
        """更新所有插件"""
        updates = self.check_updates()
        results = []

        for update in updates:
            if progress_callback:
                progress_callback(f"updating_{update['name']}", 0)

            result = self.installer.update(
                update["name"],
                f"{self.repository.repo_url}/plugins/{update['name']}.zip",
            )
            results.append({
                "name": update["name"],
                "result": result,
            })

        return {
            "success": all(r["result"]["success"] for r in results),
            "results": results,
        }


class PluginMarketplace:
    """插件市场主类"""

    def __init__(self):
        self.repository = PluginRepository()
        self.installer = PluginInstaller()
        self.updater = PluginUpdater(self.repository, self.installer)

    def search(
        self,
        query: str = "",
        category: str = None,
        tags: List[str] = None,
        min_rating: float = 0.0,
    ) -> List[PluginMetadata]:
        """搜索插件"""
        return self.repository.search_plugins(query, category, tags, min_rating)

    def install(self, plugin_name: str, source: str = None, progress_callback: Callable = None) -> dict:
        """安装插件"""
        if source is None:
            source = f"{self.repository.repo_url}/plugins/{plugin_name}.zip"
        return self.installer.install(plugin_name, source, progress_callback)

    def uninstall(self, plugin_name: str) -> dict:
        """卸载插件"""
        return self.installer.uninstall(plugin_name)

    def update(self, plugin_name: str, progress_callback: Callable = None) -> dict:
        """更新插件"""
        source = f"{self.repository.repo_url}/plugins/{plugin_name}.zip"
        return self.installer.update(plugin_name, source, progress_callback)

    def check_updates(self) -> List[dict]:
        """检查更新"""
        return self.updater.check_updates()

    def update_all(self, progress_callback: Callable = None) -> dict:
        """更新所有插件"""
        return self.updater.update_all(progress_callback)

    def get_installed(self) -> List[dict]:
        """获取已安装插件列表"""
        return self.installer.list_installed()

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return self.repository.get_categories()

    def get_tags(self) -> List[str]:
        """获取所有标签"""
        return self.repository.get_tags()

    def add_review(self, plugin_name: str, user: str, rating: int, comment: str) -> dict:
        """添加评价"""
        if plugin_name not in self.repository.plugins:
            return {"success": False, "error": "插件不存在"}

        review = PluginReview(
            user=user,
            rating=rating,
            comment=comment,
            created_at=datetime.now().isoformat(),
        )

        if plugin_name not in self.repository.reviews:
            self.repository.reviews[plugin_name] = []

        self.repository.reviews[plugin_name].append(review)

        # 更新平均评分
        reviews = self.repository.reviews[plugin_name]
        avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
        self.repository.plugins[plugin_name].rating = avg_rating

        return {"success": True, "message": "评价已添加"}

    def get_reviews(self, plugin_name: str) -> List[dict]:
        """获取插件评价"""
        reviews = self.repository.reviews.get(plugin_name, [])
        return [r.to_dict() for r in reviews]


# 使用示例
if __name__ == "__main__":
    marketplace = PluginMarketplace()

    # 添加一些示例插件
    marketplace.repository.add_plugin(
        PluginMetadata(
            name="ai_assistant",
            version="1.0.0",
            description="AI 助手插件",
            author="MCP Team",
            category="AI",
            tags=["ai", "assistant", "chat"],
            rating=4.5,
            download_count=1000,
        )
    )

    marketplace.repository.add_plugin(
        PluginMetadata(
            name="file_manager",
            version="2.1.0",
            description="文件管理插件",
            author="Dev Team",
            category="Tools",
            tags=["file", "manager", "utility"],
            rating=4.8,
            download_count=5000,
        )
    )

    # 搜索插件
    print("搜索 'ai' 插件:")
    results = marketplace.search("ai")
    for plugin in results:
        print(f"  - {plugin.name}: {plugin.description} (评分: {plugin.rating})")

    # 列出已安装插件
    print("\n已安装插件:")
    installed = marketplace.get_installed()
    for plugin in installed:
        print(f"  - {plugin['name']} v{plugin['version']}")

    # 获取分类
    print("\n插件分类:")
    categories = marketplace.get_categories()
    for category in categories:
        print(f"  - {category}")
