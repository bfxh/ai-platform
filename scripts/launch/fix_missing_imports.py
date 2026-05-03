import os, re

BASE = r""

def has_t_import(content):
    return bool(re.search(r'import\s+\{[^}]*\bt\b[^}]*\}\s+from\s+["\']@multica/core', content)) or \
           bool(re.search(r'import\s+\{\s*t\s*\}\s+from\s+["\']@multica/core/i18n', content))

def has_t_usage(content):
    return bool(re.search(r'\bt\(["\']', content))

def add_t_import(content, filepath):
    existing_core_import = re.search(r'import\s+\{([^}]+)\}\s+from\s+["\']@multica/core["\']', content)
    if existing_core_import:
        imports = existing_core_import.group(1)
        if 't' not in [x.strip() for x in imports.split(',')]:
            new_imports = 't, ' + imports
            content = content.replace(existing_core_import.group(0),
                f'import {{ {new_imports} }} from "@multica/core"')
        return content
    
    core_i18n_import = re.search(r'import\s+.*\s+from\s+["\']@multica/core/i18n["\']', content)
    if core_i18n_import:
        if 't' not in core_i18n_import.group(0):
            content = core_i18n_import.group(0).replace('import {', 'import { t,').replace('import  {', 'import { t,')
        return content

    first_import = re.search(r'^import\s', content, re.MULTILINE)
    if first_import:
        pos = first_import.start()
        import_line = 'import { t } from "@multica/core/i18n";\n'
        content = content[:pos] + import_line + content[pos:]
    return content

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
        
        if has_t_usage(content) and not has_t_import(content):
            content = add_t_import(content, fpath)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            fixed += 1
            print(f"Added t() import to: {fpath}")

print(f"\nFixed {fixed} files missing t() import")
