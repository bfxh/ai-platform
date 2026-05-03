# Auto Driver Update Script - Automated download and installation
# Run as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       Auto Driver Update Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$downloadPath = "$env:USERPROFILE\Downloads\DriverUpdates"
if (-not (Test-Path $downloadPath)) {
    New-Item -ItemType Directory -Path $downloadPath -Force | Out-Null
}

# Function to download file
function Download-File {
    param($url, $outputPath)
    try {
        Write-Host "Downloading: $url"
        Invoke-WebRequest -Uri $url -OutFile $outputPath -UseBasicParsing
        Write-Host "  [OK] Saved to: $outputPath" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  [FAILED] $_" -ForegroundColor Red
        return $false
    }
}

# Step 1: Download NVIDIA Driver
Write-Host "\n[Step 1] Downloading NVIDIA GeForce RTX 4060 Ti Driver..." -ForegroundColor Yellow
$nvidiaUrl = "https://us.download.nvidia.com/Windows/576.28/576.28-desktop-win10-win11-64bit-international-dch-whql.exe"
$nvidiaOutput = "$downloadPath\NVIDIA_Driver_576.28.exe"

# Try official NVIDIA download link
if (Test-Path $nvidiaOutput) {
    Write-Host "  [SKIP] NVIDIA driver already downloaded" -ForegroundColor Cyan
} else {
    $success = Download-File -url $nvidiaUrl -outputPath $nvidiaOutput
    if (-not $success) {
        Write-Host "  Trying alternative download method..." -ForegroundColor Yellow
        # Open NVIDIA download page for manual download
        start "https://www.nvidia.com/Download/Find.aspx?lang=en-us"
    }
}

# Step 2: Download Realtek Audio Driver
Write-Host "\n[Step 2] Downloading Realtek Audio Driver..." -ForegroundColor Yellow
$realtekAudioUrl = "https://download.microsoft.com/download/1/a/7/1a77c44c-532c-4e2e-9f0e-8e6d3c3d6f2e/Realtek-Audio-Driver-6.0.9835.1.exe"
$realtekAudioOutput = "$downloadPath\Realtek_Audio_Driver_6.0.9835.1.exe"

# Open Microsoft Update Catalog for manual download
Write-Host "  Opening Microsoft Update Catalog for Realtek Audio..." -ForegroundColor Cyan
start "https://www.catalog.update.microsoft.com/Search.aspx?q=realtek+high+definition+audio+driver+2025"

# Step 3: Download Realtek Network Driver
Write-Host "\n[Step 3] Downloading Realtek Network Driver..." -ForegroundColor Yellow
Write-Host "  Opening Realtek download page..." -ForegroundColor Cyan
start "https://www.station-drivers.com/index.php/en/component/remository/Drivers/Realtek/Lan/RTL-81xx-84xx-Ethernet-Controller/Windows-10/Realtek-RTL-81xx-Ethernet-Controller-Drivers-Version-1079.xx.1003/lang,en-gb/"

# Step 4: Install downloaded drivers
Write-Host "\n[Step 4] Installing downloaded drivers..." -ForegroundColor Yellow

if (Test-Path $nvidiaOutput) {
    Write-Host "  Installing NVIDIA Driver..." -ForegroundColor Cyan
    Write-Host "  This will require a system restart" -ForegroundColor Yellow
    Start-Process -FilePath $nvidiaOutput -ArgumentList "/s" -Wait
} else {
    Write-Host "  [SKIP] NVIDIA driver not found, opening download page..." -ForegroundColor Yellow
    start "https://www.nvidia.com/Download/index.aspx"
}

Write-Host "\n========================================" -ForegroundColor Cyan
Write-Host "       Download Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "\nLocation: $downloadPath" -ForegroundColor White
Write-Host "\nNote: Please restart your computer after installing drivers" -ForegroundColor Yellow
Write-Host "\nIf automatic download failed, please download manually from the opened pages" -ForegroundColor Yellow

Pause
