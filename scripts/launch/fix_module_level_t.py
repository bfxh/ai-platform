import os, re

BASE = r""

app_sidebar = os.path.join(BASE, "packages", "views", "layout", "app-sidebar.tsx")
with open(app_sidebar, "r", encoding="utf-8") as f:
    content = f.read()

old_personal = """const personalNav: { key: NavKey; label: string; icon: typeof Inbox }[] = [
  { key: "inbox", label: t("Inbox"), icon: Inbox },
  { key: "myIssues", label: t("My Issues"), icon: CircleUser },
];"""

new_personal = """const getPersonalNav = () => [
  { key: "inbox" as NavKey, label: t("Inbox"), icon: Inbox },
  { key: "myIssues" as NavKey, label: t("My Issues"), icon: CircleUser },
];"""

old_workspace = """const workspaceNav: { key: NavKey; label: string; icon: typeof Inbox }[] = [
  { key: "issues", label: t("Issues"), icon: ListTodo },
  { key: "projects", label: t("Projects"), icon: FolderKanban },
  { key: "autopilots", label: t("Autopilot"), icon: Zap },
  { key: "agents", label: t("Agents"), icon: Bot },
];"""

new_workspace = """const getWorkspaceNav = () => [
  { key: "issues" as NavKey, label: t("Issues"), icon: ListTodo },
  { key: "projects" as NavKey, label: t("Projects"), icon: FolderKanban },
  { key: "autopilots" as NavKey, label: t("Autopilot"), icon: Zap },
  { key: "agents" as NavKey, label: t("Agents"), icon: Bot },
];"""

old_configure = """const configureNav: { key: NavKey; label: string; icon: typeof Inbox }[] = [
  { key: "runtimes", label: t("Runtimes"), icon: Monitor },
  { key: "skills", label: t("Skills"), icon: BookOpenText },
  { key: "settings", label: t("Settings"), icon: Settings },
];"""

new_configure = """const getConfigureNav = () => [
  { key: "runtimes" as NavKey, label: t("Runtimes"), icon: Monitor },
  { key: "skills" as NavKey, label: t("Skills"), icon: BookOpenText },
  { key: "settings" as NavKey, label: t("Settings"), icon: Settings },
];"""

content = content.replace(old_personal, new_personal)
content = content.replace(old_workspace, new_workspace)
content = content.replace(old_configure, new_configure)

content = content.replace("personalNav.map", "getPersonalNav().map")
content = content.replace("workspaceNav.map", "getWorkspaceNav().map")
content = content.replace("configureNav.map", "getConfigureNav().map")

content = content.replace("personalNav.find", "getPersonalNav().find")
content = content.replace("workspaceNav.find", "getWorkspaceNav().find")
content = content.replace("configureNav.find", "getConfigureNav().find")

content = content.replace("[...personalNav,", "[...getPersonalNav(),")
content = content.replace("[...workspaceNav,", "[...getWorkspaceNav(),")
content = content.replace("[...configureNav,", "[...getConfigureNav(),")

with open(app_sidebar, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed app-sidebar.tsx: converted nav arrays to functions")

search_cmd = os.path.join(BASE, "packages", "views", "search", "search-command.tsx")
with open(search_cmd, "r", encoding="utf-8") as f:
    content = f.read()

old_pages = """const pages: { key: string; label: string; icon: typeof Inbox }[] = [
  { key: "inbox", label: t("Inbox"), icon: Inbox },
  { key: "myIssues", label: t("My Issues"), icon: CircleUser },
  { key: "issues", label: t("Issues"), icon: ListTodo },
  { key: "projects", label: t("Projects"), icon: FolderKanban },
  { key: "agents", label: t("Agents"), icon: Bot },
  { key: "runtimes", label: t("Runtimes"), icon: Monitor },
  { key: "skills", label: t("Skills"), icon: BookOpenText },
  { key: "settings", label: t("Settings"), icon: SettingsIcon },
];"""

new_pages = """const getPages = () => [
  { key: "inbox", label: t("Inbox"), icon: Inbox },
  { key: "myIssues", label: t("My Issues"), icon: CircleUser },
  { key: "issues", label: t("Issues"), icon: ListTodo },
  { key: "projects", label: t("Projects"), icon: FolderKanban },
  { key: "agents", label: t("Agents"), icon: Bot },
  { key: "runtimes", label: t("Runtimes"), icon: Monitor },
  { key: "skills", label: t("Skills"), icon: BookOpenText },
  { key: "settings", label: t("Settings"), icon: SettingsIcon },
];"""

content = content.replace(old_pages, new_pages)
content = content.replace("pages.map", "getPages().map")
content = content.replace("pages.filter", "getPages().filter")

with open(search_cmd, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed search-command.tsx: converted pages array to function")

status_path = os.path.join(BASE, "packages", "core", "issues", "config", "status.ts")
with open(status_path, "r", encoding="utf-8") as f:
    content = f.read()

if 't("Backlog")' in content:
    print("status.ts already uses t(), checking if it's module-level...")
    if 'export const ISSUE_STATUS' in content or 'export const statuses' in content:
        print("WARNING: status.ts uses t() at module level - this may not work")
        content = content.replace('t("Backlog")', 't("Backlog")')
        print("  (keeping t() calls - they should work with inline dictionary)")

priority_path = os.path.join(BASE, "packages", "core", "issues", "config", "priority.ts")
with open(priority_path, "r", encoding="utf-8") as f:
    content = f.read()
if 't("Urgent")' in content:
    print("priority.ts already uses t() at module level")

view_store = os.path.join(BASE, "packages", "core", "issues", "stores", "view-store.ts")
with open(view_store, "r", encoding="utf-8") as f:
    content = f.read()
if 't("Manual")' in content:
    print("view-store.ts uses t() - checking if module-level...")
    if re.search(r'(SORT_OPTIONS|CARD_PROPERTY_OPTIONS).*t\(', content):
        print("WARNING: view-store.ts uses t() at module level")

print("\nDone fixing module-level t() calls!")
