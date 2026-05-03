$ErrorActionPreference = "Stop"

$projectDir = ""
$pnpmPath = "C:\Users\888\AppData\Roaming\npm"
$env:PATH = "$pnpmPath;$env:PATH"

Write-Host "===== Starting Multica Desktop =====" -ForegroundColor Cyan
Write-Host ""

Set-Location $projectDir

Write-Host "Starting desktop app (dev mode)..." -ForegroundColor Yellow
& "$pnpmPath\pnpm.cmd" dev:desktop
