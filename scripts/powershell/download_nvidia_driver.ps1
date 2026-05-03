# NVIDIA Driver Download Script
# Uses NVIDIA's official download API

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       NVIDIA Driver Auto Download" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$downloadPath = "$env:USERPROFILE\Downloads\DriverUpdates"
if (-not (Test-Path $downloadPath)) {
    New-Item -ItemType Directory -Path $downloadPath -Force | Out-Null
}

# NVIDIA Driver download via API
# RTX 4060 Ti = Product ID 16458, Driver Branch: Game Ready, OS: Windows 10 64-bit

Write-Host "\nDownloading NVIDIA GeForce Game Ready Driver 576.28..." -ForegroundColor Yellow
Write-Host "For: GeForce RTX 4060 Ti" -ForegroundColor White
Write-Host "OS: Windows 10/11 64-bit" -ForegroundColor White

# Try NVIDIA download API
$nvidiaApiUrl = "https://www.nvidia.com/api/drfouoijsp/download/api/GetDownloadArchive?osId=18&packageId=5965&languageCode=2052&editionId=511&isRemote=0"

try {
    Write-Host "\nAttempting download from NVIDIA server..."
    $response = Invoke-WebRequest -Uri $nvidiaApiUrl -UseBasicParsing -MaximumRedirection 0 -ErrorAction SilentlyContinue

    if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 302) {
        $downloadUrl = $response.Headers.Location
        if ($downloadUrl) {
            Write-Host "Found download URL, starting download..." -ForegroundColor Green
            $outputFile = "$downloadPath\NVIDIA_Driver_576.28.exe"
            Invoke-WebRequest -Uri $downloadUrl -OutFile $outputFile -UseBasicParsing
            Write-Host "[SUCCESS] Downloaded to: $outputFile" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "[INFO] Direct API download not available" -ForegroundColor Yellow
}

# Alternative: Open browser for manual download
Write-Host "\n========================================" -ForegroundColor Cyan
Write-Host "Alternative: Opening NVIDIA Download Page" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Open NVIDIA driver download page with pre-selected options for RTX 4060 Ti
$manualUrl = "https://www.nvidia.com/Download/processFind.aspx?psid=23&pfid=1124&osid=12&lid=1&whql=&lang=en-us&ctk=0"
start $manualUrl

Write-Host "\nManual download instructions:" -ForegroundColor Yellow
Write-Host "1. Select: Product Type = GeForce" -ForegroundColor White
Write-Host "2. Select: Product Series = GeForce RTX 40 Series" -ForegroundColor White
Write-Host "3. Select: Product = GeForce RTX 4060 Ti" -ForegroundColor White
Write-Host "4. Select: Operating System = Windows 10/11 64-bit" -ForegroundColor White
Write-Host "5. Click 'Search'" -ForegroundColor White
Write-Host "6. Download the latest Game Ready Driver" -ForegroundColor White

Write-Host "\nDownload location: $downloadPath" -ForegroundColor Cyan

Pause
