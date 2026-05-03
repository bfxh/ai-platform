$ErrorActionPreference = "SilentlyContinue"

function Write-Banner {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Confirm-Deletion {
    param([string]$Path)
    Write-Host "Confirm deletion: $Path" -ForegroundColor Yellow
    $confirm = Read-Host "Delete? (Y/N)"
    return $confirm -eq "Y" -or $confirm -eq "y"
}

# Main
Clear-Host
Write-Banner "d:\rj Cleanup Script"

$basePath = "d:\rj"
$toolsPath = Join-Path $basePath "Tools"
$deletedCount = 0
$skippedCount = 0

# 1. Clean test files
Write-Host "[1/3] Cleaning test files..." -ForegroundColor Magenta
if (Test-Path $toolsPath) {
    $testFiles = @(
        (Join-Path $toolsPath "test_*.py"),
        (Join-Path $toolsPath "test_*.bat"),
        (Join-Path $toolsPath "test_*.js")
    )
    
    foreach ($pattern in $testFiles) {
        $files = Get-ChildItem $pattern -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            if (Confirm-Deletion $file.FullName) {
                Remove-Item $file.FullName -Force
                Write-Host "Deleted: $($file.Name)" -ForegroundColor Green
                $deletedCount++
            } else {
                Write-Host "Skipped: $($file.Name)" -ForegroundColor Gray
                $skippedCount++
            }
        }
    }
}

# 2. Clean get-pip.py
Write-Host "`n[2/3] Cleaning get-pip.py..." -ForegroundColor Magenta
$getPipPath = Join-Path $toolsPath "get-pip.py"
if (Test-Path $getPipPath) {
    if (Confirm-Deletion $getPipPath) {
        Remove-Item $getPipPath -Force
        Write-Host "Deleted: get-pip.py" -ForegroundColor Green
        $deletedCount++
    } else {
        Write-Host "Skipped: get-pip.py" -ForegroundColor Gray
        $skippedCount++
    }
}

# 3. Check duplicate directories
Write-Host "`n[3/3] Checking duplicate directories..." -ForegroundColor Magenta
$dirs = Get-ChildItem $basePath -Directory | Select-Object Name, FullName
$duplicateNames = $dirs | Group-Object Name | Where-Object { $_.Count -gt 1 } | Select-Object -ExpandProperty Name

if ($duplicateNames.Count -gt 0) {
    Write-Host "Found duplicate directory names: $($duplicateNames -join ', ')" -ForegroundColor Yellow
    foreach ($name in $duplicateNames) {
        $dupDirs = $dirs | Where-Object { $_.Name -eq $name }
        Write-Host "`nDuplicate directory: $name" -ForegroundColor White
        $i = 1
        foreach ($dir in $dupDirs) {
            $age = (Get-Date) - (Get-Item $dir.FullName).LastWriteTime
            Write-Host "  $i. $($dir.FullName) (Last modified: $($age.Days) days ago)" -ForegroundColor Gray
            $i++
        }
        $choice = Read-Host "Delete one? (Enter number, 0=skip)"
        if ($choice -match '^[1-9]$' -and $choice -le $dupDirs.Count) {
            $targetDir = $dupDirs[$choice-1]
            if (Confirm-Deletion $targetDir.FullName) {
                Remove-Item $targetDir.FullName -Recurse -Force
                Write-Host "Deleted: $($targetDir.FullName)" -ForegroundColor Green
                $deletedCount++
            } else {
                Write-Host "Skipped deletion" -ForegroundColor Gray
                $skippedCount++
            }
        }
    }
} else {
    Write-Host "No duplicate directories found" -ForegroundColor Green
}

# Summary
Write-Banner "Cleanup Complete"
Write-Host "Deleted: $deletedCount files/directories" -ForegroundColor Green
Write-Host "Skipped: $skippedCount files/directories" -ForegroundColor Gray
Write-Host ""
Write-Host "Recommended to keep:"
Write-Host "  - Core development projects (ComfyUI, openclaw, etc.)"
Write-Host "  - Useful utility scripts (github_downloader.py, upgrade_*.py, etc.)"
Write-Host "  - System tools (PDF24, Optimizer)"
Write-Host ""
