import os

BASE = r""

zh_dict_path = os.path.join(BASE, "packages", "core", "i18n", "zh.ts")
with open(zh_dict_path, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace('t("Inbox")', '"Inbox"')
content = content.replace('t("My Issues")', '"My Issues"')
content = content.replace('t("Issues")', '"Issues"')
content = content.replace('t("Projects")', '"Projects"')
content = content.replace('t("Autopilot")', '"Autopilot"')
content = content.replace('t("Agents")', '"Agents"')
content = content.replace('t("Runtimes")', '"Runtimes"')
content = content.replace('t("Skills")', '"Skills"')
content = content.replace('t("Settings")', '"Settings"')
content = content.replace('t("Workspaces")', '"Workspaces"')
content = content.replace('t("Workspace")', '"Workspace"')
content = content.replace('t("Members")', '"Members"')
content = content.replace('t("Cancel")', '"Cancel"')
content = content.replace('t("Delete")', '"Delete"')
content = content.replace('t("Save")', '"Save"')
content = content.replace('t("Edit")', '"Edit"')
content = content.replace('t("Copy")', '"Copy"')
content = content.replace('t("Close")', '"Close"')
content = content.replace('t("Back")', '"Back"')
content = content.replace('t("Profile")', '"Profile"')
content = content.replace('t("Appearance")', '"Appearance"')
content = content.replace('t("General")', '"General"')
content = content.replace('t("Theme")', '"Theme"')
content = content.replace('t("Light")', '"Light"')
content = content.replace('t("Dark")', '"Dark"')
content = content.replace('t("System")', '"System"')
content = content.replace('t("Name")', '"Name"')
content = content.replace('t("Description")', '"Description"')
content = content.replace('t("Status")', '"Status"')
content = content.replace('t("Priority")', '"Priority"')
content = content.replace('t("Assignee")', '"Assignee"')
content = content.replace('t("Labels")', '"Labels"')
content = content.replace('t("Activity")', '"Activity"')
content = content.replace('t("Loading")', '"Loading"')
content = content.replace('t("Restart")', '"Restart"')
content = content.replace('t("Stop")', '"Stop"')
content = content.replace('t("Start")', '"Start"')
content = content.replace('t("Done")', '"Done"')
content = content.replace('t("Create")', '"Create"')
content = content.replace('t("Invite")', '"Invite"')
content = content.replace('t("Revoke")', '"Revoke"')
content = content.replace('t("Confirm")', '"Confirm"')
content = content.replace('t("Owner")', '"Owner"')
content = content.replace('t("Admin")', '"Admin"')
content = content.replace('t("Member")', '"Member"')
content = content.replace('t("Search…")', '"Search…"')
content = content.replace('t("Clear")', '"Clear"')
with open(zh_dict_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed zh.ts dictionary")

test_files = []
for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", "dist", "out", ".next"}]
    for f in files:
        if f.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")):
            test_files.append(os.path.join(root, f))

for tf in test_files:
    try:
        with open(tf, "r", encoding="utf-8") as f:
            content = f.read()
        if 'import { t }' in content or 'import { t,' in content:
            content = content.replace('import { t } from "@multica/core/i18n";\n', '')
            content_lines = content.split('\n')
            new_lines = []
            for line in content_lines:
                if '@multica/core' in line and 'import' in line:
                    line = line.replace(', t', '').replace('t, ', '')
                    if line.strip() == 'import { t } from "@multica/core";' or line.strip() == "import { t } from '@multica/core';":
                        continue
                new_lines.append(line)
            content = '\n'.join(new_lines)
            content = content.replace('t("Inbox")', '"Inbox"')
            content = content.replace('t("My Issues")', '"My Issues"')
            content = content.replace('t("Issues")', '"Issues"')
            content = content.replace('t("Projects")', '"Projects"')
            content = content.replace('t("Autopilot")', '"Autopilot"')
            content = content.replace('t("Agents")', '"Agents"')
            content = content.replace('t("Runtimes")', '"Runtimes"')
            content = content.replace('t("Skills")', '"Skills"')
            content = content.replace('t("Settings")', '"Settings"')
            content = content.replace('t("Workspaces")', '"Workspaces"')
            content = content.replace('t("Workspace")', '"Workspace"')
            content = content.replace('t("Members")', '"Members"')
            content = content.replace('t("Cancel")', '"Cancel"')
            content = content.replace('t("Delete")', '"Delete"')
            content = content.replace('t("Save")', '"Save"')
            content = content.replace('t("Status")', '"Status"')
            content = content.replace('t("Priority")', '"Priority"')
            content = content.replace('t("Assignee")', '"Assignee"')
            content = content.replace('t("Owner")', '"Owner"')
            content = content.replace('t("Admin")', '"Admin"')
            content = content.replace('t("Member")', '"Member"')
            with open(tf, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Reverted test file: {tf}")
    except:
        pass

e2e_dir = os.path.join(BASE, "e2e")
if os.path.exists(e2e_dir):
    for root, dirs, files in os.walk(e2e_dir):
        for f in files:
            if f.endswith((".ts", ".tsx")):
                fp = os.path.join(root, f)
                try:
                    with open(fp, "r", encoding="utf-8") as f2:
                        content = f2.read()
                    if 't("' in content:
                        for key in ["Inbox", "My Issues", "Issues", "Projects", "Agents", "Runtimes", "Skills", "Settings", "Workspaces", "Workspace", "Members", "Cancel", "Delete", "Save", "Status", "Priority", "Assignee", "Owner", "Admin", "Member"]:
                            content = content.replace(f't("{key}")', f'"{key}"')
                        content_lines = content.split('\n')
                        new_lines = []
                        for line in content_lines:
                            if '@multica/core/i18n' in line and 'import' in line:
                                continue
                            if '@multica/core' in line and 'import' in line:
                                line = line.replace(', t', '').replace('t, ', '')
                            new_lines.append(line)
                        content = '\n'.join(new_lines)
                        with open(fp, "w", encoding="utf-8") as f2:
                            f2.write(content)
                        print(f"Reverted e2e file: {fp}")
                except:
                    pass

web_dir = os.path.join(BASE, "apps", "web")
if os.path.exists(web_dir):
    for root, dirs, files in os.walk(os.path.join(web_dir, "features", "landing", "i18n")):
        for f in files:
            if f.endswith((".ts", ".tsx")):
                fp = os.path.join(root, f)
                try:
                    with open(fp, "r", encoding="utf-8") as f2:
                        content = f2.read()
                    if 't("' in content:
                        for key in ["Inbox", "Issues", "Projects", "Agents", "Settings", "Workspace", "Members", "Cancel", "Delete", "Save", "Status", "Priority", "Member", "Dark", "Light"]:
                            content = content.replace(f't("{key}")', f'"{key}"')
                        content_lines = content.split('\n')
                        new_lines = []
                        for line in content_lines:
                            if '@multica/core/i18n' in line and 'import' in line:
                                continue
                            new_lines.append(line)
                        content = '\n'.join(new_lines)
                        with open(fp, "w", encoding="utf-8") as f2:
                            f2.write(content)
                        print(f"Reverted web i18n file: {fp}")
                except:
                    pass

docs_dir = os.path.join(BASE, "apps", "docs")
if os.path.exists(docs_dir):
    for root, dirs, files in os.walk(docs_dir):
        dirs[:] = [d for d in dirs if d not in {"node_modules", ".git"}]
        for f in files:
            if f.endswith((".ts", ".tsx")):
                fp = os.path.join(root, f)
                try:
                    with open(fp, "r", encoding="utf-8") as f2:
                        content = f2.read()
                    if 't("' in content:
                        for key in ["Inbox", "Issues", "Projects", "Agents", "Settings", "Workspace", "Members", "Cancel", "Delete", "Save", "Status", "Priority", "Member", "Dark", "Light", "System"]:
                            content = content.replace(f't("{key}")', f'"{key}"')
                        content_lines = content.split('\n')
                        new_lines = []
                        for line in content_lines:
                            if '@multica/core/i18n' in line and 'import' in line:
                                continue
                            new_lines.append(line)
                        content = '\n'.join(new_lines)
                        with open(fp, "w", encoding="utf-8") as f2:
                            f2.write(content)
                        print(f"Reverted docs file: {fp}")
                except:
                    pass

print("\nCleanup done!")
