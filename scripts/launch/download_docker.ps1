$url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$output = "$env:TEMP\DockerInstaller.exe"

Write-Host "Downloading Docker Desktop..." -ForegroundColor Cyan

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
    Write-Host "Download completed successfully!" -ForegroundColor Green
    
    if (Test-Path $output) {
        Write-Host "Starting Docker Desktop installer..." -ForegroundColor Cyan
        Start-Process -FilePath $output -ArgumentList "install --accept-license" -Wait -NoNewWindow
        Write-Host "Docker Desktop installation completed!" -ForegroundColor Green
    } else {
        Write-Host "Downloaded file not found!" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error downloading Docker: $_" -ForegroundColor Red
    exit 1
}