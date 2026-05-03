#!/usr/bin/env python3
"""Final pass: replace all remaining \python references with new CLAUSE\python path."""
import re
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # python/
NEW_PATH = r"\python"
OLD_PATTERNS = [
    (re.compile(r"/python\\", re.IGNORECASE), r"/python\\"),
    (re.compile(r"/python/", re.IGNORECASE), r"/python/"),
    (re.compile(r"D:\\\\AI\\\\", re.IGNORECASE), r"D:\\\\AI CLAUDE\\\\CLAUSE\\\\python\\\\"),
    (re.compile(r'"D:\\\\AI\\\\', re.IGNORECASE), r'"D:\\\\AI CLAUDE\\\\CLAUSE\\\\python\\\\'),
]

SKIP_DIRS = {
    "__pycache__", ".venv", ".git", "node_modules", "target",
    "rust_target", "python_standalone", "CC", ".qoder", ".trae",
}
SKIP_NAMES = {".env", ".gitignore", "fix_paths_final.py"}

EXTENSIONS = {".py", ".json", ".md", ".ps1", ".yaml", ".yml", ".toml", ".js", ".ts", ".bat", ".txt", ".cfg", ".ini"}

fixed_count = 0
file_count = 0

for file_path in BASE_DIR.rglob("*"):
    # Skip dirs
    if any(skip in file_path.parts for skip in SKIP_DIRS):
        continue
    if file_path.name in SKIP_NAMES:
        continue
    if file_path.suffix.lower() not in EXTENSIONS:
        continue
    if not file_path.is_file():
        continue

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue

    original = content
    for pattern, replacement in OLD_PATTERNS:
        content = pattern.sub(replacement, content)

    if content != original:
        try:
            file_path.write_text(content, encoding="utf-8")
            fixed_count += sum(1 for _ in re.finditer(OLD_PATTERNS[0][0], original))
            file_count += 1
            print(f"  FIXED: {file_path.relative_to(BASE_DIR)}")
        except Exception as e:
            print(f"  ERROR: {file_path.relative_to(BASE_DIR)}: {e}")

print(f"\nDone. Fixed {fixed_count} occurrences in {file_count} files.")
