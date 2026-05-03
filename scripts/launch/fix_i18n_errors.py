import os, re

BASE = r""

pkg_json = os.path.join(BASE, "packages", "core", "package.json")
with open(pkg_json, "r", encoding="utf-8") as f:
    content = f.read()

if '"./i18n"' not in content:
    if '"exports"' in content:
        content = content.replace(
            '"./i18n":',
            '"./i18n": "./i18n/index.ts",'
        )
    else:
        if '"main"' in content:
            content = content.replace(
                '"main"',
                '"exports": { "./i18n": "./i18n/index.ts" },\n  "main"'
            )
    with open(pkg_json, "w", encoding="utf-8") as f:
        f.write(content)
    print("Added ./i18n export to packages/core/package.json")
else:
    print("./i18n export already exists")

fix_patterns = [
    (r'label=t\("([^"]+)"\)', r'label={t("\1")}'),
    (r'trigger=t\("([^"]+)"\)', r'trigger={t("\1")}'),
    (r'aria-label=t\("([^"]+)"\)', r'aria-label={t("\1")}'),
    (r'title=t\("([^"]+)"\)', r'title={t("\1")}'),
    (r'placeholder=t\("([^"]+)"\)', r'placeholder={t("\1")}'),
    (r'description=t\("([^"]+)"\)', r'description={t("\1")}'),
]

fixed_count = 0
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
        for pattern, replacement in fix_patterns:
            content = re.sub(pattern, replacement, content)
        if content != original:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            fixed_count += 1
            print(f"Fixed JSX attrs in: {fpath}")

print(f"\nFixed {fixed_count} files with JSX attribute issues")
