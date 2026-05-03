import json, os

BASE = r""

pkg_path = os.path.join(BASE, "packages", "core", "package.json")
with open(pkg_path, "r", encoding="utf-8") as f:
    data = json.load(f)

data["exports"]["./i18n"] = "./i18n/index.tsx"
data["exports"]["./i18n/zh"] = "./i18n/zh.ts"
if "./i18n/index.tsx" in data["exports"]:
    del data["exports"]["./i18n/index.tsx"]

with open(pkg_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("Fixed package.json exports: ./i18n -> ./i18n/index.tsx")

import_pattern = 'from "@multica/core/i18n/index.tsx"'
new_import = 'from "@multica/core/i18n"'

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
        if import_pattern in content:
            content = content.replace(import_pattern, new_import)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            fixed += 1
            print(f"Fixed import in: {fpath}")

core_index = os.path.join(BASE, "packages", "core", "index.ts")
with open(core_index, "r", encoding="utf-8") as f:
    content = f.read()
if './i18n/index.tsx"' in content:
    content = content.replace('./i18n/index.tsx"', './i18n"')
    with open(core_index, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed core/index.ts export")

print(f"\nFixed {fixed} files")
