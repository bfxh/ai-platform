# Automatic Driver Update Script
# Automatically checks and updates all device drivers

Write-Host "========================================" -ForegroundColor Green
Write-Host "       Automatic Driver Updater" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Check for admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] Administrator privileges required" -ForegroundColor Red
    Write-Host "Please run as Administrator" -ForegroundColor Yellow
    Pause
    exit
}

# Step 1: Check for driver updates via Windows Update
Write-Host "\n[Step 1] Checking Windows Update for driver updates..." -ForegroundColor Cyan
try {
    $UpdateSession = New-Object -ComObject Microsoft.Update.Session
    $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
    
    Write-Host "Searching for available driver updates..."
    $SearchResult = $UpdateSearcher.Search("IsInstalled=0 and Type='Driver'")
    
    if ($SearchResult.Updates.Count -eq 0) {
        Write-Host "  [Result] No pending driver updates" -ForegroundColor Yellow
    } else {
        Write-Host "  [Result] Found $($SearchResult.Updates.Count) driver updates" -ForegroundColor Green
        
        $UpdateCollection = New-Object -ComObject Microsoft.Update.UpdateColl
        foreach ($Update in $SearchResult.Updates) {
            Write-Host "  - $($Update.Title)" -ForegroundColor White
            $UpdateCollection.Add($Update) | Out-Null
        }
        
        Write-Host "\nDownloading driver updates..."
        $Downloader = $UpdateSession.CreateUpdateDownloader()
        $Downloader.Updates = $UpdateCollection
        $DownloadResult = $Downloader.Download()
        
        if ($DownloadResult.ResultCode -eq 2) {
            Write-Host "  [Download OK] Installing..." -ForegroundColor Green
            
            $Installer = $UpdateSession.CreateUpdateInstaller()
            $Installer.Updates = $UpdateCollection
            $InstallResult = $Installer.Install()
            
            if ($InstallResult.ResultCode -eq 2) {
                Write-Host "  [Install OK] Driver update completed" -ForegroundColor Green
            } else {
                Write-Host "  [Install Result] Code: $($InstallResult.ResultCode)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  [Download Failed] Code: $($DownloadResult.ResultCode)" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "  [Error] Windows Update check failed: $_" -ForegroundColor Red
}

# Step 2: Check for problem devices
Write-Host "\n[Step 2] Checking for problem devices..." -ForegroundColor Cyan
try {
    $problemDevices = Get-PnpDevice -ErrorAction SilentlyContinue | Where-Object { $_.Status -ne "OK" }
    
    if ($problemDevices) {
        Write-Host "  Found $($problemDevices.Count) problem devices:" -ForegroundColor Yellow
        $problemDevices | ForEach-Object {
            Write-Host "    - $($_.FriendlyName) [Status: $($_.Status)]" -ForegroundColor White
        }
    } else {
        Write-Host "  [Result] No problem devices found" -ForegroundColor Green
    }
} catch {
    Write-Host "  [Error] Device check failed: $_" -ForegroundColor Red
}

# Step 3: Display current driver status
Write-Host "\n[Step 3] Current driver status..." -ForegroundColor Cyan
try {
    # Display display adapters
    $displayDevices = Get-PnpDevice -Class Display | Select-Object FriendlyName, DriverVersion
    if ($displayDevices) {
        Write-Host "  Display Adapters:" -ForegroundColor Yellow
        $displayDevices | ForEach-Object {
            Write-Host "    $($_.FriendlyName) - $($_.DriverVersion)" -ForegroundColor White
        }
    }
    
    # Display Intel system devices
    $systemDevices = Get-PnpDevice -Class System | Where-Object {$_.Manufacturer -like '*Intel*'} | Select-Object FriendlyName, DriverVersion
    if ($systemDevices) {
        Write-Host "\n  Intel System Devices (Top 5):" -ForegroundColor Yellow
        $systemDevices | Select-Object -First 5 | ForEach-Object {
            Write-Host "    $($_.FriendlyName)" -ForegroundColor White
        }
    }
} catch {
    Write-Host "  [Error] Driver status check failed: $_" -ForegroundColor Red
}

Write-Host "\n========================================" -ForegroundColor Green
Write-Host "       Driver Update Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "\nTips: " -ForegroundColor Yellow
Write-Host "1. Restart your computer to ensure drivers take effect" -ForegroundColor White
Write-Host "2. Run this script regularly to keep drivers updated" -ForegroundColor White
Write-Host "3. Visit hardware manufacturer websites for latest drivers" -ForegroundColor White

Pause
