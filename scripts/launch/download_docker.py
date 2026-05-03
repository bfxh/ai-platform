import urllib.request
import os

url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
output = os.path.join(os.environ['TEMP'], 'DockerInstaller.exe')

print("Downloading Docker Desktop...")
urllib.request.urlretrieve(url, output)
print(f"Download completed! File saved to: {output}")

if os.path.exists(output):
    print("Starting Docker Desktop installer...")
    os.startfile(output)
    print("Installer started. Please follow the installation prompts.")
else:
    print("Download failed!")
    exit(1)