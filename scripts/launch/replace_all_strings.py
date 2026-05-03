import os, re

BASE = r""

i18n_path = os.path.join(BASE, "packages", "core", "i18n", "index.tsx")
with open(i18n_path, "r", encoding="utf-8") as f:
    content = f.read()
dict_start = content.find('zh: {')
dict_end = content.find('\n  },\n};', dict_start)
dict_text = content[dict_start+5:dict_end]
all_keys = re.findall(r'"([^"]+)":\s*"', dict_text)
all_keys.sort(key=len, reverse=True)

print(f"Found {len(all_keys)} translation keys")

skip_dirs = {"node_modules", ".git", "dist", "out", ".next", "bin", "build", ".vite"}
skip_files = {"index.tsx", "zh.ts", "en.ts"}

def has_t_import(content):
    return bool(re.search(r'import\s+\{[^}]*\bt\b[^}]*\}\s+from\s+["\']@multica/core', content)) or \
           bool(re.search(r'import\s+\{\s*t\s*\}\s+from\s+["\']@multica/core/i18n', content))

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

def needs_braces(line, pos):
    before = line[:pos].rstrip()
    after = line[pos + len('t("...")'):].lstrip() if pos + len('t("...")') <= len(line) else ''
    jsx_attrs = ['label=', 'title=', 'placeholder=', 'description=', 'heading=', 'trigger=', 'aria-label=',
                 'tooltip=', 'suffix=', 'prefix=', 'alt=', 'text=']
    for attr in jsx_attrs:
        if before.endswith(attr):
            return True
    if before.endswith('=') and not before.endswith('==') and not before.endswith('!='):
        return True
    return False

total_replaced = 0
files_modified = 0

for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for fname in files:
        if not fname.endswith((".ts", ".tsx")):
            continue
        if fname in skip_files and "i18n" in root:
            continue
        fpath = os.path.join(root, fname)
        if "i18n/index.tsx" in fpath.replace("\\", "/"):
            continue
        if "i18n/zh.ts" in fpath.replace("\\", "/"):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except:
            continue
        
        original = content
        replaced_in_file = 0
        
        for key in all_keys:
            if len(key) < 3:
                continue
            
            patterns_to_avoid = [
                f't("{key}")',
                f"t('{key}')",
                f'"{key}":',
                f"'{key}':",
                f'`{key}`',
                f'//.*"{key}"',
                f'import.*"{key}"',
            ]
            
            escaped_key = key.replace('"', '\\"')
            search_str = f'"{escaped_key}"'
            
            if search_str not in content:
                continue
            
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                stripped = line.lstrip()
                if stripped.startswith('//') or stripped.startswith('*') or stripped.startswith('/*'):
                    new_lines.append(line)
                    continue
                
                if search_str in line:
                    if f't("{escaped_key}")' in line:
                        new_lines.append(line)
                        continue
                    
                    new_line = line
                    idx = 0
                    while True:
                        pos = new_line.find(search_str, idx)
                        if pos == -1:
                            break
                        
                        before = new_line[:pos]
                        after_pos = pos + len(search_str)
                        after = new_line[after_pos:]
                        
                        if before.rstrip().endswith(':') and not before.rstrip().endswith('::'):
                            idx = after_pos
                            continue
                        
                        if after and after[0] == ':':
                            idx = after_pos
                            continue
                        
                        if 'import' in before and 'from' in line:
                            idx = after_pos
                            continue
                        
                        if 'registerDictionary' in line or 't("' in before[max(0,pos-20):pos]:
                            idx = after_pos
                            continue
                        
                        replacement = f't("{escaped_key}")'
                        
                        if needs_braces(new_line, pos):
                            replacement = f'{{{replacement}}}'
                        
                        new_line = new_line[:pos] + replacement + new_line[after_pos:]
                        idx = pos + len(replacement)
                        replaced_in_file += 1
                
                new_lines.append(line)
            content = '\n'.join(new_lines)
        
        if content != original:
            if not has_t_import(content):
                content = add_t_import(content)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            files_modified += 1
            total_replaced += replaced_in_file
            print(f"  Replaced {replaced_in_file} in {fpath}")

print(f"\nTotal: {total_replaced} strings replaced in {files_modified} files")
