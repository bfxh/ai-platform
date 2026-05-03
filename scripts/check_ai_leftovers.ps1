$root = ""
if (-not (Test-Path $root)) {
    Write-Host " does not exist"
    exit 0
}

Write-Host "=== Remaining files in  ==="
$total = @(Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue).Count
Write-Host "Total files: $total"

Write-Host ""
Write-Host "=== Top directories with file counts ==="
Get-ChildItem $root -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $dir = $_
    $count = @(Get-ChildItem $dir.FullName -Recurse -File -ErrorAction SilentlyContinue).Count
    Write-Host ("  {0}: {1} files" -f $dir.Name, $count)
}

Write-Host ""
Write-Host "=== Largest directories in storage/ ==="
if (Test-Path "$root\storage") {
    Get-ChildItem "$root\storage" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $dir = $_
        $count = @(Get-ChildItem $dir.FullName -Recurse -File -ErrorAction SilentlyContinue).Count
        Write-Host ("  storage/{0}: {1} files" -f $dir.Name, $count)
    }
}
