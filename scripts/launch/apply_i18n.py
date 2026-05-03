import os
import re

BASE = r""

replacements = {
    r"\packages\core\issues\config\status.ts": [
        ('"Backlog"', 't("Backlog")'),
        ('"Todo"', 't("Todo")'),
        ('"In Progress"', 't("In Progress")'),
        ('"In Review"', 't("In Review")'),
        ('"Done"', 't("Done")'),
        ('"Blocked"', 't("Blocked")'),
        ('"Cancelled"', 't("Cancelled")'),
    ],
    r"\packages\core\issues\config\priority.ts": [
        ('"Urgent"', 't("Urgent")'),
        ('"High"', 't("High")'),
        ('"Medium"', 't("Medium")'),
        ('"Low"', 't("Low")'),
        ('"No priority"', 't("No priority")'),
    ],
}

simple_replacements_global = [
    ('"Inbox"', 't("Inbox")'),
    ('"My Issues"', 't("My Issues")'),
    ('"Issues"', 't("Issues")'),
    ('"Projects"', 't("Projects")'),
    ('"Autopilot"', 't("Autopilot")'),
    ('"Agents"', 't("Agents")'),
    ('"Runtimes"', 't("Runtimes")'),
    ('"Skills"', 't("Skills")'),
    ('"Settings"', 't("Settings")'),
    ('"Workspaces"', 't("Workspaces")'),
    ('"Workspace"', 't("Workspace")'),
    ('"Members"', 't("Members")'),
    ('"Cancel"', 't("Cancel")'),
    ('"Delete"', 't("Delete")'),
    ('"Save"', 't("Save")'),
    ('"Edit"', 't("Edit")'),
    ('"Copy"', 't("Copy")'),
    ('"Close"', 't("Close")'),
    ('"Back"', 't("Back")'),
    ('"Profile"', 't("Profile")'),
    ('"Appearance"', 't("Appearance")'),
    ('"General"', 't("General")'),
    ('"Theme"', 't("Theme")'),
    ('"Light"', 't("Light")'),
    ('"Dark"', 't("Dark")'),
    ('"System"', 't("System")'),
    ('"Name"', 't("Name")'),
    ('"Description"', 't("Description")'),
    ('"Status"', 't("Status")'),
    ('"Priority"', 't("Priority")'),
    ('"Assignee"', 't("Assignee")'),
    ('"Labels"', 't("Labels")'),
    ('"Activity"', 't("Activity")'),
    ('"Loading"', 't("Loading")'),
    ('"Restart"', 't("Restart")'),
    ('"Stop"', 't("Stop")'),
    ('"Start"', 't("Start")'),
    ('"Done"', 't("Done")'),
    ('"Create"', 't("Create")'),
    ('"Invite"', 't("Invite")'),
    ('"Revoke"', 't("Revoke")'),
    ('"Confirm"', 't("Confirm")'),
    ('"Search…"', 't("Search…")'),
    ('"Clear"', 't("Clear")'),
    ('"Owner"', 't("Owner")'),
    ('"Admin"', 't("Admin")'),
    ('"Member"', 't("Member")'),
]

skip_dirs = {"node_modules", ".git", "dist", "out", ".next", "bin"}
skip_exts = {".md", ".mdx", ".json", ".css", ".svg", ".png", ".ico", ".lock"}

import_added = set()

def add_import_if_needed(filepath, content):
    if filepath in import_added:
        return content
    if "from \"@multica/core\"" in content or "from '@multica/core'" in content:
        if "t," not in content and ", t" not in content and "t }" not in content:
            content = content.replace(
                'from "@multica/core"',
                'import { t } from "@multica/core";\nimport_old_marker'
            )
            content = content.replace(
                "from '@multica/core'",
                "import { t } from '@multica/core';\nimport_old_marker"
            )
            if "import_old_marker" in content:
                lines = content.split("\n")
                new_lines = []
                for line in lines:
                    if "import_old_marker" in line:
                        bare_import = line.replace("import_old_marker", "").strip()
                        if bare_import.startswith("import {") or bare_import.startswith("import{"):
                            pass
                        new_lines.append(line.replace("import_old_marker", ""))
                    else:
                        new_lines.append(line)
                content = "\n".join(new_lines)

            old_import_match = re.search(r'import\s+\{([^}]+)\}\s+from\s+["\']@multica/core["\']', content)
            if old_import_match:
                old_imports = old_import_match.group(1)
                if "t" not in [x.strip() for x in old_imports.split(",")]:
                    new_imports = "t, " + old_imports
                    content = content.replace(old_import_match.group(0),
                        f'import {{ {new_imports} }} from "@multica/core"')
            import_added.add(filepath)
    elif filepath.endswith(".ts") or filepath.endswith(".tsx"):
        if 'import { t }' not in content and 'import{ t }' not in content:
            first_import = re.search(r'^import\s', content, re.MULTILINE)
            if first_import:
                pos = first_import.start()
                import_line = 'import { t } from "@multica/core/i18n";\n'
                content = content[:pos] + import_line + content[pos:]
                import_added.add(filepath)
    return content

def process_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except:
        return 0

    original = content
    count = 0

    for old, new in simple_replacements_global:
        if old in content:
            new_content = content.replace(old, new)
            if new_content != content:
                content = new_content
                count += 1

    if content != original:
        content = add_import_if_needed(filepath, content)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    return count

total = 0
for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for fname in files:
        ext = os.path.splitext(fname)[1]
        if ext in skip_exts:
            continue
        if ext not in (".ts", ".tsx"):
            continue
        fpath = os.path.join(root, fname)
        if "node_modules" in fpath:
            continue
        c = process_file(fpath)
        if c > 0:
            print(f"  Patched {c} strings in {fpath}")
            total += c

print(f"\nTotal: {total} strings replaced across files")
