#!/usr/bin/env python3
"""适配层 - OS 适配与软件对接"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional


class PathMapper:
    """路径格式统一"""

    @staticmethod
    def to_posix(p: str) -> str:
        return Path(p).as_posix()

    @staticmethod
    def to_native(p: str) -> str:
        return str(Path(p))

    @staticmethod
    def resolve_external(external_path: str, project_dir: str) -> Path:
        ext = Path(external_path)
        if ext.is_absolute():
            return ext
        return (Path(project_dir) / ext).resolve()


class SoftwareAdapter:
    """软件适配：扫描外部工作区，生成路径映射"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.environ.get("AI_BASE_DIR", os.getcwd())
        self.base_dir = Path(base_dir)

    def scan_software(self, software_config: list, external_root: Path) -> dict:
        mapping = {}
        for item in software_config:
            name = item.get("name", "")
            rel_path = item.get("path", "")
            version = item.get("version", "")

            full_path = external_root / rel_path if not Path(rel_path).is_absolute() else Path(rel_path)

            exists = full_path.exists()
            mapping[name] = {
                "path": str(full_path),
                "version": version,
                "exists": exists,
                "params": item.get("params", []),
            }
        return mapping

    def validate_workspace(self, plugin_config: dict, project_dir: str) -> dict:
        workspace = plugin_config.get("workspace", {})
        external_path = workspace.get("external_path", "")
        if not external_path:
            return {"valid": False, "error": "plugin.toml 缺少 [workspace] external_path"}

        ext_root = PathMapper.resolve_external(external_path, project_dir)
        if not ext_root.exists():
            return {"valid": False, "error": f"外部工作区不存在: {ext_root}"}

        software = plugin_config.get("software", {}).get("items", [])
        mapping = self.scan_software(software, ext_root)

        missing = [n for n, m in mapping.items() if not m["exists"]]
        if missing:
            return {
                "valid": False,
                "error": f"软件路径不存在: {', '.join(missing)}",
                "mapping": mapping,
            }

        return {"valid": True, "mapping": mapping, "external_root": str(ext_root)}


class OSAdapter:
    """操作系统适配"""

    @staticmethod
    def get_platform() -> str:
        return platform.system().lower()

    @staticmethod
    def get_env_var(name: str) -> Optional[str]:
        return os.environ.get(name)

    @staticmethod
    def set_env_var(name: str, value: str):
        os.environ[name] = value

    @staticmethod
    def find_executable(name: str) -> Optional[str]:
        result = subprocess.run(
            ["where" if platform.system() == "Windows" else "which", name],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
        return None
