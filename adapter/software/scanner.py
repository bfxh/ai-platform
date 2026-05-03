#!/usr/bin/env python3
"""件配 - 描本地已安软"""

import os
from pathlib import Path
from typing import Optional


SOFTWARE_CANDIDATES = {
    "ollama": [
        os.path.expandvars("%OLLAMA_DIR%/ollama.exe"),
        "C:/Program Files/Ollama/ollama.exe",
        os.path.expandvars("%USERPROFILE%/AppData/Local/Programs/Ollama/ollama.exe"),
    ],
    "python": [
        os.path.expandvars("%USERPROFILE%/AppData/Local/Programs/Python/Python310/python.exe"),
        "C:/Python310/python.exe",
        "C:/Python311/python.exe",
        "C:/Python312/python.exe",
    ],
    "node": [
        "C:/Program Files/nodejs/node.exe",
        "C:/nodejs/node.exe",
    ],
    "git": [
        "C:/Program Files/Git/bin/git.exe",
        "C:/Git/bin/git.exe",
    ],
    "ffmpeg": [
        "C:/ffmpeg/bin/ffmpeg.exe",
        os.path.expandvars("%SOFTWARE_DIR%/ffmpeg/bin/ffmpeg.exe"),
    ],
}


def _resolve(path_str: str) -> Path:
    return Path(os.path.expandvars(path_str))


def scan_installed_software() -> dict:
    found = {}
    for name, candidates in SOFTWARE_CANDIDATES.items():
        for candidate in candidates:
            resolved = _resolve(candidate)
            if resolved.exists():
                found[name] = str(resolved).replace("\\", "/")
                break
    return found


def get_software_path(name: str) -> Optional[str]:
    candidates = SOFTWARE_CANDIDATES.get(name, [])
    for candidate in candidates:
        resolved = _resolve(candidate)
        if resolved.exists():
            return str(resolved).replace("\\", "/")
    return None
