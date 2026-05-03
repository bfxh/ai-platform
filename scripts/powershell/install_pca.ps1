$zipPath = 'f:\rj\QQ\E-PCA 类寄生蜂v2.7.0.zip'
$destPath = '%GAME_DIR%'

Write-Host '========================================'
Write-Host '  E-PCA v2.7.0 Install Script'
Write-Host '========================================'
Write-Host ''

$file = Get-Item $zipPath
$sizeMB = [math]::Round($file.Length / 1MB, 2)
Write-Host ('Source: ' + $zipPath)
Write-Host ('Size: ' + $sizeMB.ToString() + ' MB')
Write-Host ('Destination: ' + $destPath)
Write-Host ''

if (-not (Test-Path $destPath)) {
    Write-Host 'Creating destination directory...'
    New-Item -ItemType Directory -Path $destPath -Force | Out-Null
}

Write-Host 'Extracting, please wait...'
Write-Host ''

Expand-Archive -Path $zipPath -DestinationPath $destPath -Force

Write-Host ''
Write-Host '========================================'
Write-Host '  Extraction Complete!'
Write-Host '========================================'
Write-Host ''
Write-Host ('Extracted to: ' + $destPath)
Get-ChildItem $destPath -Depth 0 | ForEach-Object {
    Write-Host ('  - ' + $_.Name)
}
