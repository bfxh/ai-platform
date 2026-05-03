#!/usr/bin/env python3
"""Fix double-path corruption caused by overly aggressive replacement."""
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Fix patterns like "/python/" -> "/python/"
# and "\python\" -> "\python\"

FIXES = [
    ("/python", "/python"),
    ("D:\\\\AI CLAUDE\\\\CLAUSE\\\\python", "D:\\\\AI CLAUDE\\\\CLAUSE\\\\python"),
    ("D:\\AI CLAUDE\\CLAUSE\\python", "D:\\AI CLAUDE\\CLAUSE\\python"),
]

SKIP_DIRS = {"__pycache__", ".venv", ".git", "node_modules", "target",
             "rust_target", "python_standalone", "CC", ".qoder", ".trae"}
SKIP_NAMES = {".env", ".gitignore"}
EXTENSIONS = {".py", ".json", ".md", ".ps1", ".yaml", ".yml", ".toml",
              ".js", ".ts", ".bat", ".txt", ".cfg", ".ini", ".cfg"}

total_fixes = 0
total_files = 0

for file_path in BASE_DIR.rglob("*"):
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
    for old, new in FIXES:
        content = content.replace(old, new)

    if content != original:
        try:
            file_path.write_text(content, encoding="utf-8")
            total_files += 1
            total_fixes += 1
            print("  FIXED: {}".format(file_path.relative_to(BASE_DIR)))
        except Exception as e:
            print("  ERROR: {}: {}".format(file_path.relative_to(BASE_DIR), e))

print("\nDone. Fixed {} files.".format(total_files))
