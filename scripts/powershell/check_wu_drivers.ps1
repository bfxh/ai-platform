# Windows Update Driver Checker
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       Windows Update Driver Checker" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    $UpdateSession = New-Object -ComObject Microsoft.Update.Session
    $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
    $UpdateSearcher.Online = $true

    Write-Host "`nSearching for driver updates online..." -ForegroundColor Yellow

    $SearchResult = $UpdateSearcher.Search("IsInstalled=0 and Type='Driver'")

    if ($SearchResult.Updates.Count -eq 0) {
        Write-Host "`n[Result] No pending driver updates found via Windows Update" -ForegroundColor Green
    } else {
        Write-Host "`n[Result] Found $($SearchResult.Updates.Count) driver updates:" -ForegroundColor Green

        foreach ($Update in $SearchResult.Updates) {
            $severity = if ($Update.MsrcSeverity) { $Update.MsrcSeverity } else { "Optional" }
            Write-Host "  - $($Update.Title) [$severity]" -ForegroundColor White
        }

        Write-Host "`nDownloading and installing updates..." -ForegroundColor Yellow

        $UpdateCollection = New-Object -ComObject Microsoft.Update.UpdateColl
        foreach ($Update in $SearchResult.Updates) {
            $UpdateCollection.Add($Update) | Out-Null
        }

        $Downloader = $UpdateSession.CreateUpdateDownloader()
        $Downloader.Updates = $UpdateCollection
        $DownloadResult = $Downloader.Download()

        if ($DownloadResult.ResultCode -eq 2) {
            Write-Host "  [Download OK]" -ForegroundColor Green

            $Installer = $UpdateSession.CreateUpdateInstaller()
            $Installer.Updates = $UpdateCollection
            $InstallResult = $Installer.Install()

            if ($InstallResult.ResultCode -eq 2) {
                Write-Host "  [Install OK] All drivers updated successfully!" -ForegroundColor Green
            } else {
                Write-Host "  [Install Failed] Result code: $($InstallResult.ResultCode)" -ForegroundColor Red
            }
        } else {
            Write-Host "  [Download Failed] Result code: $($DownloadResult.ResultCode)" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "`n[Error] $_" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Driver check complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Pause
