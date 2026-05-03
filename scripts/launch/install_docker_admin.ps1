$installer = "$env:TEMP\DockerDesktopInstaller.exe"
if (Test-Path $installer) {
    Write-Host "Starting Docker Desktop installation (requires admin)..." -ForegroundColor Cyan
    Start-Process -FilePath $installer -ArgumentList "install","--accept-license","--quiet" -Verb RunAs -Wait
    Write-Host "Docker Desktop installation completed!" -ForegroundColor Green
    
    $dockerPath = "C:\Program Files\Docker\Docker\resources\bin"
    if (Test-Path $dockerPath) {
        $env:Path += ";$dockerPath"
        Write-Host "Docker added to PATH for this session" -ForegroundColor Green
    }
} else {
    Write-Host "Docker installer not found at: $installer" -ForegroundColor Red
    exit 1
}