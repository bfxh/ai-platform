#!/usr/bin/env python3
"""
/python 统一资源管理器 v2.0
自动加载和管理所有技能、工具、工作流
支持 v2.0 注册表格式（含 mcp_core_skills 和 mcp config）
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List


class ResourceManager:
    """统一资源管理器 v2.0"""

    def __init__(self, registry_path: str = None):
        if registry_path is None:
            _base = Path(os.environ.get("AI_BASE_DIR", Path(__file__).resolve().parent.parent))
            registry_path = str(_base / "resource_registry.json")
        self.registry_path = registry_path
        self.registry = self._load_registry()
        self.resources = {}
        self.version = self.registry.get("version", "1.0")

    def _load_registry(self) -> Dict:
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Cannot load registry: {e}")
            return {}

    def _scan_directory(self, path: str) -> List[str]:
        try:
            p = Path(path)
            if not p.exists():
                return []
            return [str(f) for f in p.rglob("*") if f.is_file()]
        except Exception as e:
            print(f"[WARNING] Cannot scan {path}: {e}")
            return []

    def _count_py_files(self, path: str) -> int:
        try:
            p = Path(path)
            if not p.exists():
                return 0
            return len([f for f in p.rglob("*.py") if f.is_file()])
        except:
            return 0

    def load_all_resources(self) -> bool:
        print("=" * 60)
        print(f"/python Resource Manager v{self.version}")
        print("=" * 60)
        print()

        if not self.registry.get("auto_load", False):
            print("[INFO] Auto-load disabled")
            return False

        total_steps = 7
        print(f"[1/{total_steps}] Loading skills...")
        self._load_skills()

        print(f"[2/{total_steps}] Loading plugins...")
        self._load_plugins()

        print(f"[3/{total_steps}] Loading MCP tools...")
        self._load_mcp()

        print(f"[4/{total_steps}] Loading MCP Core skills...")
        self._load_mcp_core_skills()

        print(f"[5/{total_steps}] Loading workflows...")
        self._load_workflows()

        print(f"[6/{total_steps}] Loading projects...")
        self._load_projects()

        print(f"[7/{total_steps}] Validating MCP config...")
        self._validate_mcp_config()

        print()
        print("=" * 60)
        print("Resource loading complete")
        print("=" * 60)
        self._print_summary()

        return True

    def _load_skills(self):
        skills_path = self.registry.get("resources", {}).get("skills", {}).get("path", "")
        if skills_path:
            files = self._scan_directory(skills_path)
            self.resources["skills"] = files
            py_count = self._count_py_files(skills_path)
            print(f"    Found {len(files)} files ({py_count} Python) in {skills_path}")

    def _load_plugins(self):
        plugins_path = self.registry.get("resources", {}).get("plugins", {}).get("path", "")
        if plugins_path:
            files = self._scan_directory(plugins_path)
            self.resources["plugins"] = files
            py_count = self._count_py_files(plugins_path)
            print(f"    Found {len(files)} files ({py_count} Python) in {plugins_path}")

    def _load_mcp(self):
        mcp_config = self.registry.get("resources", {}).get("mcp", {})
        mcp_path = mcp_config.get("path", "")
        if mcp_path:
            files = self._scan_directory(mcp_path)
            self.resources["mcp"] = files

            categories = mcp_config.get("categories", {})
            for cat_name, cat_path in categories.items():
                cat_files = self._scan_directory(cat_path)
                cat_py = self._count_py_files(cat_path)
                print(f"    [{cat_name}] {len(cat_files)} files ({cat_py} Python) in {cat_path}")

            config_path = mcp_config.get("config", "")
            if config_path and os.path.exists(config_path):
                print(f"    Config: {config_path}")

    def _load_mcp_core_skills(self):
        mcp_core = self.registry.get("resources", {}).get("mcp_core_skills", {})
        skills_path = mcp_core.get("path", "")
        if skills_path:
            files = self._scan_directory(skills_path)
            self.resources["mcp_core_skills"] = files
            py_count = self._count_py_files(skills_path)
            print(f"    Found {len(files)} files ({py_count} Python) in {skills_path}")

            registry_path = mcp_core.get("registry", "")
            if registry_path and os.path.exists(registry_path):
                print(f"    Registry: {registry_path}")

    def _load_workflows(self):
        workflows_path = self.registry.get("resources", {}).get("workflows", {}).get("path", "")
        if workflows_path and os.path.exists(workflows_path):
            files = self._scan_directory(workflows_path)
            self.resources["workflows"] = files
            print(f"    Found {len(files)} workflow files")
        else:
            self.resources["workflows"] = []
            print(f"    No workflows directory found")

    def _load_projects(self):
        projects = self.registry.get("resources", {}).get("projects", {})
        software_path = projects.get("software", "")
        miniprogram_path = projects.get("miniprogram", "")

        software_count = len(self._scan_directory(software_path)) if software_path else 0
        miniprogram_count = len(self._scan_directory(miniprogram_path)) if miniprogram_path else 0

        self.resources["projects"] = {"software": software_count, "miniprogram": miniprogram_count}

        print(f"    Software projects: {software_count}")
        print(f"    Miniprogram projects: {miniprogram_count}")

    def _validate_mcp_config(self):
        mcp_config_path = self.registry.get("resources", {}).get("mcp", {}).get("config", "")
        if not mcp_config_path or not os.path.exists(mcp_config_path):
            print(f"    [WARN] MCP config not found: {mcp_config_path}")
            return

        try:
            with open(mcp_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            servers = config.get("mcpServers", {})
            total = len(servers)
            valid = 0
            invalid_paths = []

            for name, server in servers.items():
                path = server.get("path", "")
                if path and path.endswith(".py"):
                    if os.path.exists(path):
                        valid += 1
                    else:
                        invalid_paths.append(f"{name}: {path}")

            print(f"    MCP servers: {total} total, {valid} valid paths")
            if invalid_paths:
                print(f"    [WARN] {len(invalid_paths)} invalid paths:")
                for ip in invalid_paths[:5]:
                    print(f"      - {ip}")
        except Exception as e:
            print(f"    [ERROR] Failed to validate MCP config: {e}")

    def _print_summary(self):
        print()
        print("Resource Summary:")
        for resource_type, files in self.resources.items():
            if isinstance(files, list):
                print(f"  - {resource_type}: {len(files)} files")
            elif isinstance(files, dict):
                print(f"  - {resource_type}:")
                for sub_type, count in files.items():
                    print(f"      - {sub_type}: {count}")
        print()

        print("Intelligent Features:")
        features = self.registry.get("intelligent_features", {})
        for feature, enabled in features.items():
            status = "ON" if enabled else "OFF"
            print(f"  [{status}] {feature}")
        print()

        print("Python Environment:")
        envs = self.registry.get("python_environments", {})
        for env_name, env_path in envs.items():
            if env_name != "auto_detect":
                exists = "OK" if os.path.exists(env_path) else "MISSING"
                print(f"  [{exists}] {env_name}")
        print()

    def get_resources(self, resource_type: str) -> List[str]:
        return self.resources.get(resource_type, [])

    def search_resources(self, keyword: str) -> Dict[str, List[str]]:
        results = {}
        keyword = keyword.lower()

        for resource_type, files in self.resources.items():
            if isinstance(files, list):
                matched = [f for f in files if keyword in f.lower()]
                if matched:
                    results[resource_type] = matched

        return results


def main():
    manager = ResourceManager()
    success = manager.load_all_resources()

    if success:
        print("[SUCCESS] All resources loaded")
        return 0
    else:
        print("[FAILED] Resource loading failed")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
