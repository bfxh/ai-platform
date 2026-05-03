# Simple driver update script

# Check for driver updates via Windows Update
try {
    $UpdateSession = New-Object -ComObject Microsoft.Update.Session
    $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
    
    Write-Host "Searching for driver updates..."
    $SearchResult = $UpdateSearcher.Search("IsInstalled=0 and Type='Driver'")
    
    if ($SearchResult.Updates.Count -eq 0) {
        Write-Host "No driver updates available"
    } else {
        Write-Host "Found $($SearchResult.Updates.Count) driver updates"
        
        $UpdateCollection = New-Object -ComObject Microsoft.Update.UpdateColl
        foreach ($Update in $SearchResult.Updates) {
            Write-Host " - $($Update.Title)"
            $UpdateCollection.Add($Update) | Out-Null
        }
        
        Write-Host "Downloading..."
        $Downloader = $UpdateSession.CreateUpdateDownloader()
        $Downloader.Updates = $UpdateCollection
        $DownloadResult = $Downloader.Download()
        
        if ($DownloadResult.ResultCode -eq 2) {
            Write-Host "Download completed"
            
            Write-Host "Installing..."
            $Installer = $UpdateSession.CreateUpdateInstaller()
            $Installer.Updates = $UpdateCollection
            $InstallResult = $Installer.Install()
            
            if ($InstallResult.ResultCode -eq 2) {
                Write-Host "Installation completed successfully"
            } else {
                Write-Host "Installation result: $($InstallResult.ResultCode)"
            }
        } else {
            Write-Host "Download result: $($DownloadResult.ResultCode)"
        }
    }
} catch {
    Write-Host "Error: $_"
}

Write-Host "\nDriver update check completed"
