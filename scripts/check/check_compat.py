import json, os

result_file = r"\python\mod_results\mod_update_1.20.4.json"
with open(result_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

exact = [r for r in data['results'] if r.get('status') == 'update_available']
bad = []
for r in exact:
    latest = r.get('latest', {})
    fn = latest.get('filename', '')
    if 'neoforge' in fn.lower() or '1.20.4' in fn:
        bad.append({
            'old_file': r['file'],
            'new_file': fn,
            'title': r.get('title', '?'),
            'cur_ver': r.get('current_version', '?'),
            'new_ver': latest.get('version_number', '?')
        })

print(f"Total exact updates: {len(exact)}")
print(f"Incompatible (1.20.4 NeoForge on 1.20.1 Forge): {len(bad)}")
for b in bad:
    print(f"  {b['title']}: {b['old_file']} -> {b['new_file']}")
