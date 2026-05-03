import os, re

BASE = r""

i18n_path = os.path.join(BASE, "packages", "core", "i18n", "index.tsx")
with open(i18n_path, "r", encoding="utf-8") as f:
    content = f.read()
dict_start = content.find('zh: {')
dict_end = content.find('\n  },\n};', dict_start)
dict_text = content[dict_start+5:dict_end]
all_keys = re.findall(r'"([^"]+)":\s*"', dict_text)
all_keys = [k for k in all_keys if len(k) >= 3]
all_keys.sort(key=len, reverse=True)

print(f"Found {len(all_keys)} translation keys to match")

skip_dirs = {"node_modules", ".git", "dist", "out", ".next", "bin", "build", ".vite"}

def has_t_import(content):
    return bool(re.search(r'\bt\b.*from\s+["\']@multica/core', content)) or \
           bool(re.search(r'from\s+["\']@multica/core/i18n', content))

def add_t_import(content):
    existing = re.search(r'import\s+\{([^}]+)\}\s+from\s+["\']@multica/core["\']', content)
    if existing:
        imports = existing.group(1)
        if 't' not in [x.strip() for x in imports.split(',')]:
            new_imports = 't, ' + imports
            content = content.replace(existing.group(0),
                f'import {{ {new_imports} }} from "@multica/core"')
        return content
    first_import = re.search(r'^import\s', content, re.MULTILINE)
    if first_import:
        pos = first_import.start()
        content = content[:pos] + 'import { t } from "@multica/core/i18n";\n' + content[pos:]
    return content

total_replaced = 0
files_modified = 0

for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for fname in files:
        if not fname.endswith((".ts", ".tsx")):
            continue
        fpath = os.path.join(root, fname)
        norm_path = fpath.replace("\\", "/")
        if "i18n/index.tsx" in norm_path or "i18n/zh.ts" in norm_path:
            continue
        if "/e2e/" in norm_path or ".test." in fname or ".spec." in fname:
            continue
        if "/apps/web/" in norm_path or "/apps/docs/" in norm_path:
            continue
        
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except:
            continue
        
        original = content
        replaced = 0
        
        for key in all_keys:
            escaped_key = key.replace('\\', '\\\\').replace('"', '\\"')
            
            patterns = [
                (f'>"{escaped_key}"<', f'>{{t("{escaped_key}")}}<'),
                (f'"{escaped_key}"</', f'{{t("{escaped_key}")}}</'),
                (f' >"{escaped_key}"', f' >{{t("{escaped_key}")}}'),
                (f'"{escaped_key}"<', f'{{t("{escaped_key}")}}<'),
            ]
            
            for old, new in patterns:
                if old in content:
                    content = content.replace(old, new)
                    replaced += content.count(new) - original.count(new)
            
            jsx_attrs = ['label', 'title', 'placeholder', 'description', 'heading', 'trigger',
                        'aria-label', 'tooltip', 'suffix', 'prefix', 'text', 'alt', 'name',
                        'message', 'toast', 'success', 'error', 'info', 'warning']
            for attr in jsx_attrs:
                old_attr = f'{attr}="{escaped_key}"'
                new_attr = f'{attr}={{t("{escaped_key}")}}'
                if old_attr in content:
                    content = content.replace(old_attr, new_attr)
                    replaced += 1
            
            toast_patterns = [
                (f'toast.success("{escaped_key}")', f'toast.success(t("{escaped_key}"))'),
                (f'toast.error("{escaped_key}")', f'toast.error(t("{escaped_key}"))'),
                (f'toast.info("{escaped_key}")', f'toast.info(t("{escaped_key}"))'),
                (f'toast.warning("{escaped_key}")', f'toast.warning(t("{escaped_key}"))'),
                (f'toast("{escaped_key}")', f'toast(t("{escaped_key}"))'),
            ]
            for old_t, new_t in toast_patterns:
                if old_t in content:
                    content = content.replace(old_t, new_t)
                    replaced += 1
        
        if content != original:
            if not has_t_import(content):
                content = add_t_import(content)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            files_modified += 1
            print(f"  Modified: {fpath}")

print(f"\nTotal: {files_modified} files modified")
