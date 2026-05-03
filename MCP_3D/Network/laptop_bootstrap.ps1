Write-Host "========================================" -ForegroundColor Magenta
Write-Host " Laptop Bootstrap - 192.168.1.14" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

$DESKTOP_IP = "192.168.1.6"
$LAPTOP_IP  = "192.168.1.14"
$SHARE_NAME = "MCP3D_Cluster"
$MOUNT_DRIVE = "Z:"

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "  RE-RUNNING AS ADMINISTRATOR..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

Write-Host "[0/8] Opening firewall ports..." -ForegroundColor Yellow
$rules = @(
    @{Name="ICMPv4 Echo Request (ping)"; Dir="In"; Proto="ICMPv4"}
    @{Name="SMB File Sharing"; Dir="In"; Proto="TCP"; Port="445"}
    @{Name="Remote Desktop (RDP)"; Dir="In"; Proto="TCP"; Port="3389"}
    @{Name="exo Cluster API"; Dir="In"; Proto="TCP"; Port="52415"}
    @{Name="WinRM Remote Mgmt"; Dir="In"; Proto="TCP"; Port="5985"}
)

foreach ($rule in $rules) {
    $check = netsh advfirewall firewall show rule name="$($rule.Name)" 2>$null
    if ($check -match "No rules match") {
        if ($rule.Proto -eq "ICMPv4") {
            netsh advfirewall firewall add rule name="$($rule.Name)" dir=in protocol=icmpv4 action=allow | Out-Null
        } else {
            netsh advfirewall firewall add rule name="$($rule.Name)" dir=in protocol=$($rule.Proto) localport=$($rule.Port) action=allow | Out-Null
        }
        Write-Host "  [ADDED]  $($rule.Name)"
    } else {
        Write-Host "  [EXISTS] $($rule.Name)"
    }
}

Write-Host ""
Write-Host "[1/8] Enabling Remote Desktop..." -ForegroundColor Yellow
Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0 -Force
Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "UserAuthentication" -Value 0 -Force
netsh advfirewall firewall set rule group="Remote Desktop" new enable=Yes | Out-Null
Write-Host "  RDP enabled on port 3389"

Write-Host ""
Write-Host "[2/8] Enabling Network Discovery + SMB..." -ForegroundColor Yellow
netsh advfirewall firewall set rule group="Network Discovery" new enable=Yes | Out-Null
netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes | Out-Null
Set-Service -Name LanmanServer -StartupType Automatic
Start-Service -Name LanmanServer 2>$null
Write-Host "  SMB server enabled"

Write-Host ""
Write-Host "[3/8] Checking connectivity to desktop..." -ForegroundColor Yellow
if (Test-Connection -ComputerName $DESKTOP_IP -Count 2 -Quiet) {
    Write-Host "  OK: Desktop $DESKTOP_IP reachable"
} else {
    Write-Host "  WARNING: Cannot reach desktop" -ForegroundColor Red
    Write-Host "  Check both on same WiFi, continue anyway..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[4/8] Mounting shared drive..." -ForegroundColor Yellow
net use $MOUNT_DRIVE /delete 2>$null | Out-Null
net use $MOUNT_DRIVE "\\$DESKTOP_IP\$SHARE_NAME" /persistent:yes 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  MOUNTED: $MOUNT_DRIVE -> \\$DESKTOP_IP\$SHARE_NAME"
} else {
    Write-Host "  NOTE: Mount failed - will retry after desktop firewall opens" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[5/8] Checking tools..." -ForegroundColor Yellow
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "  git: OK"
} else {
    Write-Host "  git: Installing..."
    winget install Git.Git --accept-source-agreements --accept-package-agreements 2>$null
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    $pyVer = python --version 2>&1
    Write-Host "  python: $pyVer"
} else {
    Write-Host "  python: NOT FOUND - install from https://python.org or: winget install Python.Python.3.12"
}

if (Get-Command pip -ErrorAction SilentlyContinue) {
    Write-Host "  pip: OK"
} else {
    Write-Host "  pip: NOT FOUND (comes with Python)"
}

if (Get-Command task -ErrorAction SilentlyContinue) {
    Write-Host "  task: OK"
} else {
    Write-Host "  task: Installing..."
    winget install Task.Task --accept-source-agreements --accept-package-agreements 2>$null
}

Write-Host ""
Write-Host "[6/8] Installing exo cluster agent..." -ForegroundColor Yellow
pip install exo 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  exo installed OK"
} else {
    Write-Host "  exo install failed - try manually: pip install exo" -ForegroundColor Red
}

Write-Host ""
Write-Host "[7/8] Creating local workspace..." -ForegroundColor Yellow
$LOCAL_DIR = "\MCP_3D"
New-Item -ItemType Directory -Force -Path $LOCAL_DIR | Out-Null
New-Item -ItemType Directory -Force -Path "$LOCAL_DIR\Shared" | Out-Null
New-Item -ItemType Directory -Force -Path "$LOCAL_DIR\Network" | Out-Null
Copy-Item -Path "$PSScriptRoot\*" -Destination "$LOCAL_DIR\Network\" -Exclude "laptop_bootstrap.ps1" -Force -ErrorAction SilentlyContinue
Write-Host "  Workspace: $LOCAL_DIR"

Write-Host ""
Write-Host "[8/8] Creating auto-start script..." -ForegroundColor Yellow

$autoBat = @"
@echo off
title Laptop Cluster Worker
echo =====================================
echo  Laptop Cluster Auto-Start
echo =====================================
echo.
echo Desktop:  \\$DESKTOP_IP\\$SHARE_NAME
echo Cluster:  exo --discovery-address $DESKTOP_IP
echo.
echo [1] Mounting shared drive...
net use $MOUNT_DRIVE /delete >nul 2>&1
net use $MOUNT_DRIVE \\\\$DESKTOP_IP\\$SHARE_NAME /persistent:yes
echo.
echo [2] Starting exo worker (auto-join cluster)...
start "exo-worker" cmd /c "exo --node-id laptop-worker --discovery-address $DESKTOP_IP"
echo.
echo LAPTOP READY for cluster tasks.
echo Desktop can now RDP to: $LAPTOP_IP:3389
echo.
pause
"@

Set-Content -Path "$LOCAL_DIR\auto_start.bat" -Value $autoBat -Encoding ASCII
Write-Host "  Created: $LOCAL_DIR\auto_start.bat"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " LAPTOP BOOTSTRAP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host " Shared drive: $MOUNT_DRIVE -> \\$DESKTOP_IP\$SHARE_NAME" -ForegroundColor White
Write-Host " RDP access:   $LAPTOP_IP`:3389" -ForegroundColor White
Write-Host " Cluster:      exo --discovery-address $DESKTOP_IP" -ForegroundColor White
Write-Host ""
Write-Host " TO START:  Run \MCP_3D\auto_start.bat" -ForegroundColor Cyan
Write-Host " TO VERIFY: From desktop: ping $LAPTOP_IP" -ForegroundColor Cyan
