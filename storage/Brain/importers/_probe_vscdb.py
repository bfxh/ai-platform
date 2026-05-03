import sqlite3
import json

def probe_vscdb(path, label):
    print(f'\n=== {label} ===')
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("SELECT key, length(value) FROM ItemTable")
    all_rows = cursor.fetchall()
    print(f'Total keys: {len(all_rows)}')
    
    chat_keys = [r for r in all_rows if any(kw in r[0].lower() for kw in ['chat', 'aicoding', 'lingma', 'conversation', 'history', 'message'])]
    print(f'Chat-related keys ({len(chat_keys)}):')
    for k, vlen in chat_keys:
        print(f'  {k} (len={vlen})')
    
    for k, vlen in chat_keys[:5]:
        if vlen > 0 and vlen < 500000:
            cursor.execute("SELECT value FROM ItemTable WHERE key=?", (k,))
            row = cursor.fetchone()
            if row and row[0]:
                val = row[0]
                if isinstance(val, bytes):
                    try:
                        val = val.decode('utf-8')
                    except:
                        val = val.decode('utf-8', errors='replace')
                print(f'\n--- {k} (len={len(val)}) ---')
                try:
                    parsed = json.loads(val)
                    out = json.dumps(parsed, ensure_ascii=False, indent=2)
                    print(out[:3000])
                except:
                    print(val[:3000])
    
    conn.close()

probe_vscdb(r'C:\Users\888\AppData\Roaming\Qoder\User\globalStorage\state.vscdb', 'globalStorage')
probe_vscdb(r'C:\Users\888\AppData\Roaming\Qoder\User\workspaceStorage\fee7f55561a121c7c475e233bd8d9308\state.vscdb', 'workspaceStorage')
