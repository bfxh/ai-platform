import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class ConvertState:
    """转换状态管理器 - 支持断点续转"""

    def __init__(self, output_dir: Path, model_name: str):
        self.state_file = output_dir / ".convert_state.json"
        self.model_name = model_name
        self.data = {
            "model_name": model_name,
            "started_at": datetime.now().isoformat(),
            "steps_completed": [],
            "steps_failed": [],
            "output_files": {},
            "last_error": None,
        }
        if self.state_file.exists():
            self._load()

    def _load(self):
        try:
            saved = json.loads(self.state_file.read_text(encoding='utf-8'))
            if saved.get("model_name") == self.model_name:
                self.data = saved
        except (json.JSONDecodeError, KeyError):
            pass

    def save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False),
            encoding='utf-8',
        )

    def mark_completed(self, step: str, output_files: Dict[str, str] = None):
        if step not in self.data["steps_completed"]:
            self.data["steps_completed"].append(step)
        if step in self.data["steps_failed"]:
            self.data["steps_failed"].remove(step)
        if output_files:
            self.data["output_files"].update(output_files)
        self.save()

    def mark_failed(self, step: str, error: str):
        if step not in self.data["steps_failed"]:
            self.data["steps_failed"].append(step)
        self.data["last_error"] = error
        self.save()

    def is_completed(self, step: str) -> bool:
        return step in self.data["steps_completed"]

    def get_output_file(self, step: str) -> Optional[str]:
        return self.data["output_files"].get(step)

    def cleanup(self):
        if self.state_file.exists():
            self.state_file.unlink()

    @property
    def has_incomplete(self) -> bool:
        return len(self.data["steps_failed"]) > 0 or (
            len(self.data["steps_completed"]) > 0
            and len(self.data["steps_completed"]) < 4
        )
