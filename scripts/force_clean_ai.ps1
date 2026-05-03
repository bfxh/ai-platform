# Force delete all remaining  files
$root = ""

Write-Host "Force deleting  leftover files..."
$errors = 0
$deleted = 0

# First, delete all files
$files = Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue
foreach ($f in $files) {
    try {
        # Remove read-only attribute if present
        if ($f.Attributes -band [System.IO.FileAttributes]::ReadOnly) {
            $f.Attributes = $f.Attributes -bxor [System.IO.FileAttributes]::ReadOnly
        }
        Remove-Item $f.FullName -Force -ErrorAction Stop
        $deleted++
    } catch {
        $errors++
        if ($errors -le 10) {
            Write-Host "  FAILED: $($f.FullName) - $($_.Exception.Message)"
        }
    }
}

Write-Host "Deleted $deleted files, $errors failures"

# Then remove empty directories
$dirs = Get-ChildItem $root -Recurse -Directory -ErrorAction SilentlyContinue | Sort-Object { $_.FullName.Length } -Descending
foreach ($d in $dirs) {
    try {
        $isEmpty = @(Get-ChildItem $d.FullName -ErrorAction SilentlyContinue).Count -eq 0
        if ($isEmpty) {
            Remove-Item $d.FullName -Force -ErrorAction Stop
        }
    } catch {}
}

# Check what's left
$remaining = @(Get-ChildItem $root -Recurse -ErrorAction SilentlyContinue).Count
Write-Host "Remaining items after cleanup: $remaining"

if ($remaining -eq 0) {
    Remove-Item $root -Force -ErrorAction SilentlyContinue
    Write-Host " fully removed!"
} else {
    Write-Host "Some items could not be removed. Trying to remove the root..."
    Remove-Item $root -Recurse -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $root)) {
        Write-Host " fully removed!"
    }
}
