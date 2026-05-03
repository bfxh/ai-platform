import json

for v in ['1.12.2', '1.20.4']:
    path = f'/python\\mod_results\\mod_update_{v}.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    exact = [r for r in data['results'] if r.get('status') == 'update_available']
    print(f'\n=== {v} 精确匹配可更新 ({len(exact)}) ===')
    for r in exact:
        latest = r.get('latest', {})
        cur = r.get('current_version', '?')
        new = latest.get('version_number', '?')
        fn = latest.get('filename', '?')
        title = r.get('title', '?')
        print(f'  {title}: {cur} -> {new}')
        print(f'    {r["file"]} -> {fn}')
