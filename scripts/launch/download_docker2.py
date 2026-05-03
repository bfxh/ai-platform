import urllib.request
import ssl
import os

url = "https://download.docker.com/win/static/stable/x86_64/docker-27.3.1.zip"
output = os.path.join(os.environ['TEMP'], 'docker.zip')

print("Downloading Docker...")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    urllib.request.urlretrieve(url, output, context=ctx)
    print(f"Download completed! File saved to: {output}")
    print("Extracting Docker...")
    
    import zipfile
    extract_dir = os.path.join(os.environ['PROGRAMFILES'], 'Docker')
    with zipfile.ZipFile(output, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    print(f"Docker extracted to: {extract_dir}")
    print("Adding Docker to PATH...")
    
except Exception as e:
    print(f"Error: {e}")
    exit(1)