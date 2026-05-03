Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Desktop Network Setup - 192.168.1.6" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$DESKTOP_IP = "192.168.1.6"
$LAPTOP_IP  = "192.168.1.14"
$SHARE_DIR  = "\MCP_3D\Shared"
$SHARE_NAME = "MCP3D_Cluster"

Write-Host "[1/5] Creating shared directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $SHARE_DIR | Out-Null
New-Item -ItemType Directory -Force -Path "$SHARE_DIR\projects" | Out-Null
New-Item -ItemType Directory -Force -Path "$SHARE_DIR\models" | Out-Null
New-Item -ItemType Directory -Force -Path "$SHARE_DIR\datasets" | Out-Null
New-Item -ItemType Directory -Force -Path "$SHARE_DIR\outputs" | Out-Null
Write-Host "  Created: $SHARE_DIR"
Write-Host "    projects/ models/ datasets/ outputs/"

Write-Host ""
Write-Host "[2/5] Configuring SMB share..." -ForegroundColor Yellow
$shareCheck = net share | Select-String $SHARE_NAME
if (-not $shareCheck) {
    net share $SHARE_NAME="$SHARE_DIR" /GRANT:EVERYONE,FULL /REMARK:"MCP3D Cluster Shared Storage"
    Write-Host "  Share created: \\$DESKTOP_IP\$SHARE_NAME"
} else {
    Write-Host "  Share already exists: \\$DESKTOP_IP\$SHARE_NAME"
}

Write-Host ""
Write-Host "[3/5] Configuring Windows Firewall..." -ForegroundColor Yellow
$rules = @(
    @{Name="File and Printer Sharing (SMB-In)"; Dir="In"; Proto="TCP"; Port="445"}
    @{Name="Remote Desktop (RDP)"; Dir="In"; Proto="TCP"; Port="3389"}
    @{Name="exo HTTP API"; Dir="In"; Proto="TCP"; Port="52415"}
    @{Name="WinRM Remote Management"; Dir="In"; Proto="TCP"; Port="5985"}
    @{Name="ICMPv4 Echo Request"; Dir="In"; Proto="ICMPv4"; Port=""}
)

foreach ($rule in $rules) {
    $exists = netsh advfirewall firewall show rule name="$($rule.Name)" 2>$null
    if ($exists -match "No rules match") {
        if ($rule.Proto -eq "ICMPv4") {
            netsh advfirewall firewall add rule name="$($rule.Name)" dir=in protocol=icmpv4 action=allow | Out-Null
        } else {
            netsh advfirewall firewall add rule name="$($rule.Name)" dir=in protocol=$($rule.Proto) localport=$($rule.Port) action=allow | Out-Null
        }
        Write-Host "  Added rule: $($rule.Name)"
    } else {
        Write-Host "  Rule exists: $($rule.Name)"
    }
}

Write-Host ""
Write-Host "[4/5] Enabling Remote Desktop..." -ForegroundColor Yellow
Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0 -Force
Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "UserAuthentication" -Value 0 -Force
Write-Host "  Remote Desktop enabled"

Write-Host ""
Write-Host "[5/5] Enabling Network Discovery..." -ForegroundColor Yellow
netsh advfirewall firewall set rule group="Network Discovery" new enable=Yes | Out-Null
Write-Host "  Network Discovery enabled"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " DESKTOP SETUP COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Share:  \\$DESKTOP_IP\$SHARE_NAME" -ForegroundColor White
Write-Host "RDP:    $DESKTOP_IP`:3389" -ForegroundColor White
Write-Host ""
Write-Host "Next: Run laptop_bootstrap.ps1 on laptop (192.168.1.14)" -ForegroundColor Cyan
