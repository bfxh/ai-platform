import requests, json, os

r = requests.get('https://api.github.com/repos/UB-Mannheim/tesseract/releases/latest', timeout=10)
data = r.json()
tag = data.get('tag_name', 'unknown')
print(f'Latest release: {tag}')

download_url = None
for asset in data.get('assets', []):
    name = asset['name']
    if 'w64' in name and name.endswith('.exe'):
        download_url = asset['browser_download_url']
        size_mb = asset['size'] // 1024 // 1024
        print(f'Found: {name} ({size_mb}MB)')
        print(f'URL: {download_url}')
        break

if download_url:
    os.makedirs('/python/downloads', exist_ok=True)
    path = '/python/downloads/tesseract-setup.exe'
    print(f'Downloading to {path}...')
    with requests.get(download_url, stream=True, timeout=300) as resp:
        if resp.status_code == 200:
            total = int(resp.headers.get('content-length', 0))
            downloaded = 0
            with open(path, 'wb') as f:
                for chunk in resp.iter_content(8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if downloaded % (5*1024*1024) < 8192:
                            pct = downloaded*100//total if total else 0
                            print(f'  {downloaded//1024//1024}MB ({pct}%)')
            actual = os.path.getsize(path)
            print(f'Download complete: {actual//1024//1024}MB')
        else:
            print(f'Download failed: HTTP {resp.status_code}')
else:
    print('No Windows 64-bit installer found in latest release')
