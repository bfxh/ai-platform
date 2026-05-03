$url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$output = "$env:TEMP\DockerInstaller.exe"

Write-Host "Downloading Docker Desktop..." -ForegroundColor Cyan
(New-Object System.Net.WebClient).DownloadFile($url, $output)

if (Test-Path $output) {
    Write-Host "Download completed! Starting installer..." -ForegroundColor Green
    Start-Process $output -ArgumentList "install --accept-license" -Wait
    Write-Host "Docker Desktop installation completed!" -ForegroundColor Green
} else {
    Write-Host "Download failed!" -ForegroundColor Red
    exit 1
}