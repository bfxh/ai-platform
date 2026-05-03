#!/usr/bin/env python3
"""Git 版本管理"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


class GitManager:
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.environ.get("AI_BASE_DIR", str(Path(__file__).resolve().parent.parent))
        self.base_dir = Path(base_dir)

    def _run_git(self, *args, cwd=None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git"] + list(args),
            cwd=cwd or self.base_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def init_repo(self) -> bool:
        if (self.base_dir / ".git").exists():
            return True
        result = self._run_git("init")
        if result.returncode != 0:
            return False
        self._run_git("config", "user.name", "AI-Platform")
        self._run_git("config", "user.email", "platform@local")
        return True

    def commit_daily(self, date_str: Optional[str] = None) -> bool:
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        daily_file = self.base_dir / "storage" / "daily" / f"{date_str}.json"
        if not daily_file.exists():
            return False

        self._run_git("add", str(daily_file))
        self._run_git("add", "storage/")
        self._run_git("add", "projects/")
        self._run_git("add", "specifications/")
        self._run_git("add", "core/")

        result = self._run_git("commit", "-m", f"daily: {date_str}")
        return result.returncode == 0

    def is_lfs_installed(self) -> bool:
        result = self._run_git("lfs", "version")
        return result.returncode == 0

    def setup_lfs(self) -> bool:
        if not self.is_lfs_installed():
            return False
        self._run_git("lfs", "install")
        self._run_git("lfs", "track", "storage/trash/*.snapshot")
        self._run_git("add", ".gitattributes")
        return True

    def get_status(self) -> dict:
        result = self._run_git("status", "--porcelain")
        if result.returncode != 0:
            return {"error": result.stderr}

        files = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            status = line[:2].strip()
            filepath = line[3:].strip()
            files.append({"status": status, "path": filepath})

        return {"total": len(files), "files": files}

    def get_log(self, count: int = 10) -> list:
        result = self._run_git("log", f"-{count}", "--oneline")
        if result.returncode != 0:
            return []

        entries = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(" ", 1)
            entries.append({"hash": parts[0], "message": parts[1] if len(parts) > 1 else ""})
        return entries
