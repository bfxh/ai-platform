$zipPath = 'f:\rj\QQ\E-PCA 类寄生蜂v2.7.0.zip'
$destPath = '\python\temp_epca'
Write-Host ('Zip exists: ' + (Test-Path $zipPath).ToString())
Write-Host ('Dest exists: ' + (Test-Path $destPath).ToString())
try {
    Expand-Archive -Path $zipPath -DestinationPath $destPath -Force
    Write-Host 'Expand-Archive completed'
    Get-ChildItem $destPath -Recurse | ForEach-Object { Write-Host $_.FullName }
} catch {
    Write-Host ('Error: ' + $_.Exception.Message)
}
