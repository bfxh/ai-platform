#!/usr/bin/env python3
"""Force remove  leftovers using Python (avoids bash/PowerShell mangling)."""
import shutil
import os
import stat
from pathlib import Path

target = Path("")

def remove_readonly(func, path, excinfo):
    """Error handler that removes read-only flag and retries."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

if not target.exists():
    print(" does not exist. Already cleaned!")
else:
    # Count remaining
    remaining = list(target.rglob("*"))
    print(f"Remaining items: {len(remaining)}")
    for p in remaining[:20]:
        print(f"  {p}")

    print("\nAttempting to remove...")
    try:
        shutil.rmtree(target, onerror=remove_readonly)
        print(" fully removed!")
    except Exception as e:
        print(f"Partial removal: {e}")
        
        # Try individual files
        failed = []
        for f in target.rglob("*"):
            try:
                if f.is_file():
                    os.chmod(f, stat.S_IWRITE)
                    f.unlink()
                elif f.is_dir():
                    try:
                        f.rmdir()
                    except:
                        shutil.rmtree(f, onerror=remove_readonly)
            except Exception as e2:
                failed.append((str(f), str(e2)))
        
        if failed:
            print(f"\nFailed to remove {len(failed)} items:")
            for path, err in failed[:10]:
                print(f"  {path}: {err}")
        
        # Check what's left
        left = list(target.rglob("*"))
        print(f"\nItems remaining: {len(left)}")
        for p in left:
            print(f"  {p}")

print("\nDone.")
