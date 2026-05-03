Write-Host "===== LARGE FILES (>500MB) =====" -ForegroundColor Yellow
$drives = @("D:\","E:\","F:\")
foreach ($drive in $drives) {
    Write-Host "[SCAN] $drive ..." -ForegroundColor Cyan
    Get-ChildItem -Path $drive -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Length -gt 500MB -and $_.Extension -notin @('.pak','.blob','.exe','.dll','.so') } |
        Sort-Object Length -Descending |
        Select-Object -First 20 |
        ForEach-Object {
            [PSCustomObject]@{
                SizeMB = [math]::Round($_.Length/1MB, 2)
                Ext = $_.Extension
                Path = $_.FullName
            }
        } | Format-Table -AutoSize
}

Write-Host ""
Write-Host "===== TEMP/LOG FILES =====" -ForegroundColor Yellow
$tempExts = @("*.log","*.tmp","*.temp","*.bak","*.old","*.swp","*~")
$tempResults = @()
foreach ($drive in $drives) {
    $total = 0
    $count = 0
    foreach ($ext in $tempExts) {
        $files = Get-ChildItem -Path $drive -Recurse -File -Filter $ext -Depth 5 -ErrorAction SilentlyContinue |
            Where-Object { $_.Length -gt 1MB }
        foreach ($f in $files) {
            $total += $f.Length
            $count++
        }
    }
    if ($count -gt 0) {
        $tempResults += [PSCustomObject]@{Drive=$drive; TempFiles=$count; SizeGB=[math]::Round($total/1GB,2)}
    }
}
$tempResults | Format-Table -AutoSize

Write-Host ""
Write-Host "===== WINDOWS TEMP =====" -ForegroundColor Yellow
$winTemp = (Get-ChildItem "$env:TEMP" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum)
Write-Host "User Temp: $([math]::Round($winTemp.Sum/1GB,2)) GB ($($winTemp.Count) files)"
$sysTemp = (Get-ChildItem "C:\Windows\Temp" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum)
Write-Host "System Temp: $([math]::Round($sysTemp.Sum/1GB,2)) GB ($($sysTemp.Count) files)"

Write-Host ""
Write-Host "===== RECYCLE BIN =====" -ForegroundColor Yellow
$shell = New-Object -ComObject Shell.Application
$rb = $shell.NameSpace(0x0a)
$rbCount = $rb.Items().Count
Write-Host "Recycle Bin items: $rbCount"

Write-Host ""
Write-Host "===== PYTHON CACHE =====" -ForegroundColor Yellow
$pyc = Get-ChildItem -Path D:\ -Recurse -File -Filter "*.pyc" -Depth 6 -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum
Write-Host "D:\ .pyc files: $([math]::Round($pyc.Sum/1MB,2)) MB ($($pyc.Count) files)"

Write-Host ""
Write-Host "===== TRAE CACHE =====" -ForegroundColor Yellow
$traeCache = Get-ChildItem "%USERPROFILE%\AppData\Roaming\Trae CN" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum
Write-Host "Trae CN Roaming: $([math]::Round($traeCache.Sum/1GB,2)) GB"
$traeLocal = Get-ChildItem "%USERPROFILE%\.trae-cn" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum
Write-Host "Trae .trae-cn: $([math]::Round($traeLocal.Sum/1GB,2)) GB"
