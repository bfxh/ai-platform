import os, re, json

BASE = r""

os.rename(
    os.path.join(BASE, "packages", "core", "i18n", "index.ts"),
    os.path.join(BASE, "packages", "core", "i18n", "index.tsx")
)
print("Renamed i18n/index.ts -> i18n/index.tsx")

pkg_path = os.path.join(BASE, "packages", "core", "package.json")
with open(pkg_path, "r", encoding="utf-8") as f:
    data = json.load(f)
data["exports"]["./i18n"] = "./i18n/index.tsx"
with open(pkg_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("Updated package.json exports")

core_index = os.path.join(BASE, "packages", "core", "index.ts")
with open(core_index, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace('./i18n";', './i18n/index.tsx";')
with open(core_index, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated core/index.ts import path")

fix_count = 0
for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", "dist", "out", ".next", "bin"}]
    for fname in files:
        if not fname.endswith((".ts", ".tsx")):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except:
            continue
        original = content
        content = content.replace('from "@multica/core/i18n"', 'from "@multica/core/i18n/index.tsx"')
        if content != original:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            fix_count += 1
            print(f"Fixed import path in: {fpath}")

heading_pattern = re.compile(r'heading=t\("([^"]+)"\)')
fixed = 0
for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", "dist", "out", ".next", "bin"}]
    for fname in files:
        if not fname.endswith((".ts", ".tsx")):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except:
            continue
        original = content
        content = heading_pattern.sub(r'heading={t("\1")}', content)
        if content != original:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            fixed += 1
            print(f"Fixed heading= in: {fpath}")

print(f"\nFixed {fix_count} import paths and {fixed} heading attributes")
