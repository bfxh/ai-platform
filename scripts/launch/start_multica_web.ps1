$ErrorActionPreference = "Stop"

$projectDir = ""
$pnpmPath = "C:\Users\888\AppData\Roaming\npm"
$env:PATH = "$pnpmPath;$env:PATH"

Write-Host "===== Starting Multica Server + Web =====" -ForegroundColor Cyan
Write-Host ""

Set-Location $projectDir

Write-Host "Starting backend (Go server)..." -ForegroundColor Yellow
$serverProc = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$projectDir\server'; go run ./cmd/server" -PassThru

Start-Sleep -Seconds 3

Write-Host "Starting frontend (Next.js)..." -ForegroundColor Yellow
$webProc = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$projectDir'; & '$pnpmPath\pnpm.cmd' dev:web" -PassThru

Write-Host ""
Write-Host "===== Services Started =====" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8080"
Write-Host "  Frontend: http://localhost:3000"
Write-Host "  Login code: 888888"
Write-Host ""
Write-Host "  Server PID: $($serverProc.Id)"
Write-Host "  Web PID:    $($webProc.Id)"
