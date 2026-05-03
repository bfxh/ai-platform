$terraTechDir = "D:\SteamLibrary\steamapps\common\TerraTech"

Write-Host "=== TerraTech.exe ==="
$exePath = Join-Path $terraTechDir "TerraTech.exe"
if (Test-Path $exePath) {
    Write-Host "FOUND: TerraTech.exe"
    $item = Get-Item $exePath
    Write-Host "  Size: $([math]::Round($item.Length / 1MB, 2)) MB"
    Write-Host "  LastWriteTime: $($item.LastWriteTime)"
} else {
    Write-Host "NOT FOUND: TerraTech.exe in root"
    # Search for it in subdirectories
    $found = Get-ChildItem $terraTechDir -Filter "TerraTech.exe" -Recurse -ErrorAction SilentlyContinue
    if ($found) {
        foreach ($f in $found) {
            Write-Host "FOUND: $($f.FullName)"
        }
    } else {
        Write-Host "TerraTech.exe not found anywhere in directory"
    }
}

Write-Host ""
Write-Host "=== BepInEx Check ==="
$bepFiles = @("doorstop_config.ini", "winhttp.dll", "BepInEx", "doorstop_config.yml")
foreach ($f in $bepFiles) {
    $fp = Join-Path $terraTechDir $f
    if (Test-Path $fp) {
        Write-Host "FOUND: $f"
        if ($f -eq "BepInEx") {
            Write-Host "  BepInEx subdirectories:"
            Get-ChildItem $fp -Directory -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "    $($_.Name)" }
        }
    } else {
        Write-Host "NOT FOUND: $f"
    }
}

Write-Host ""
Write-Host "=== Top-level Directory Listing ==="
Get-ChildItem $terraTechDir -Depth 0 | ForEach-Object {
    $type = if ($_.PSIsContainer) { "[DIR]" } else { "[FILE]" }
    Write-Host "$type $($_.Name)"
}

Write-Host ""
Write-Host "=== Steam libraryfolders.vdf ==="
$vdfPaths = @(
    "D:\SteamLibrary\steamapps\libraryfolders.vdf",
    "E:\Steam\steamapps\libraryfolders.vdf"
)
foreach ($vdf in $vdfPaths) {
    if (Test-Path $vdf) {
        Write-Host "VDF: $vdf"
        Get-Content $vdf
        Write-Host ""
    }
}
