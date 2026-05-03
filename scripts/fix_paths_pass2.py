#!/usr/bin/env python3
"""Second pass: fix ALL old \python / /python references (not followed by CLAUDE)."""
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Patterns that match \python or /python NOT followed by CLAUDE
OLD_DOS = re.compile(r'/python(?![a-zA-Z])(?!\\CLAUDE)', re.IGNORECASE)
OLD_FWD = re.compile(r'/python(?![a-zA-Z])(?!/CLAUDE)', re.IGNORECASE)
OLD_JSON = re.compile(r'D:\\\\AI(?![a-zA-Z])(?!\\\\CLAUDE)', re.IGNORECASE)

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

    # Count old occurrences before modifying
    fixes = len(OLD_DOS.findall(content)) + len(OLD_FWD.findall(content)) + len(OLD_JSON.findall(content))
    if fixes == 0:
        continue

    # Use lambda for safe replacement (avoids regex escape issues in repl string)
    content = OLD_JSON.sub(lambda m: "/python", content)
    content = OLD_DOS.sub(lambda m: "/python", content)
    content = OLD_FWD.sub(lambda m: "/python", content)

    if content != original:
        try:
            file_path.write_text(content, encoding="utf-8")
            total_fixes += fixes
            total_files += 1
            print("  [{}] {}".format(fixes, file_path.relative_to(BASE_DIR)))
        except Exception as e:
            print("  ERROR: {}: {}".format(file_path.relative_to(BASE_DIR), e))

print("\nDone. Fixed {} occurrences in {} files.".format(total_fixes, total_files))
