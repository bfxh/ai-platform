Write-Host "========================================" -ForegroundColor Cyan
Write-Host " exo Cluster Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$DESKTOP_IP = "192.168.1.6"
$LAPTOP_IP  = "192.168.1.14"
$EXO_PORT   = 52415

Write-Host "Cluster Topology:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  [Desktop] ---------- [Laptop]"
Write-Host "  $DESKTOP_IP        $LAPTOP_IP"
Write-Host "  (orchestrator)      (worker)"
Write-Host ""

Write-Host "Checking exo installation..." -ForegroundColor Yellow
$exoCheck = pip show exo 2>$null
if (-not $exoCheck) {
    Write-Host "  exo not installed, installing..."
    pip install exo
}
Write-Host "  exo installed"

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host " STARTUP COMMANDS" -ForegroundColor Yellow
Write-Host "========================================"
Write-Host ""
Write-Host "On DESKTOP (orchestrator):" -ForegroundColor White
Write-Host "  exo --node-id desktop-orchestrator" -ForegroundColor Cyan
Write-Host "  --listen-host $DESKTOP_IP --port $EXO_PORT" -ForegroundColor Cyan
Write-Host ""
Write-Host "On LAPTOP (worker):" -ForegroundColor White
Write-Host "  exo --node-id laptop-worker" -ForegroundColor Magenta
Write-Host "  --discovery-address $DESKTOP_IP" -ForegroundColor Magenta
Write-Host "  --listen-host $LAPTOP_IP --port $EXO_PORT" -ForegroundColor Magenta
Write-Host ""

Write-Host "========================================" -ForegroundColor Yellow
Write-Host " CLUSTER STATUS CHECK" -ForegroundColor Yellow
Write-Host "========================================"

Write-Host ""
Write-Host "Checking if laptop is online..." -ForegroundColor Yellow
$pingResult = Test-Connection -ComputerName $LAPTOP_IP -Count 1 -Quiet -ErrorAction SilentlyContinue

if ($pingResult) {
    Write-Host "  [OK] Laptop $LAPTOP_IP is ONLINE" -ForegroundColor Green
    Write-Host "  Run: exo --node-id desktop-orchestrator --listen-host $DESKTOP_IP --port $EXO_PORT" -ForegroundColor Cyan
} else {
    Write-Host "  [OFF] Laptop $LAPTOP_IP is OFFLINE" -ForegroundColor Red
    Write-Host "  Desktop can run solo: exo --node-id desktop-orchestrator --listen-host $DESKTOP_IP --port $EXO_PORT" -ForegroundColor Cyan
    Write-Host "  Laptop will auto-join when it comes online and runs laptop_bootstrap.ps1" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host " HUAWEI PHONE SETUP (via WiFi)" -ForegroundColor Yellow
Write-Host "========================================"
Write-Host ""
Write-Host "Install on phone via Termux/F-Droid:" -ForegroundColor White
Write-Host "  1. Termux (F-Droid store)" -ForegroundColor Cyan
Write-Host "  2. In Termux: pkg install python git" -ForegroundColor Cyan
Write-Host "  3. pip install exo" -ForegroundColor Cyan
Write-Host "  4. exo --discovery-address $DESKTOP_IP --listen-host <phone-ip>" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: Phone IP will be assigned by router (192.168.1.x)" -ForegroundColor Yellow
Write-Host "      Check router admin at http://192.168.1.1" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " Configuration complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
