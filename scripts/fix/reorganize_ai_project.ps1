$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  \python Reorganize Script - Continue Qoder Tasks" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

$AI_ROOT = "\python"

function New-DirIfMissing {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "  [CREATE] $Path" -ForegroundColor Green
    } else {
        Write-Host "  [EXISTS] $Path" -ForegroundColor Yellow
    }
}

function Move-FileToCategory {
    param(
        [string]$Source,
        [string]$DestDir,
        [string]$Pattern
    )
    $files = Get-ChildItem -Path $Source -Filter $Pattern -File -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        $dest = Join-Path $DestDir $file.Name
        if (-not (Test-Path $dest)) {
            Move-Item -Path $file.FullName -Destination $dest -Force
            Write-Host "  [MOVE] $($file.Name) -> $DestDir" -ForegroundColor Cyan
        } else {
            Write-Host "  [SKIP] $($file.Name) (dest exists)" -ForegroundColor DarkGray
        }
    }
}

Write-Host "=== Step 1: Create missing TRAE directories ===" -ForegroundColor White
New-DirIfMissing "$AI_ROOT\MCP\JM"
New-DirIfMissing "$AI_ROOT\MCP\BC"
New-DirIfMissing "$AI_ROOT\MCP\Tools"
New-DirIfMissing "$AI_ROOT\MCP_Core\skills"
New-DirIfMissing "$AI_ROOT\MCP_Core\workflow"
New-DirIfMissing "$AI_ROOT\MCP_Core\agent"
New-DirIfMissing "$AI_ROOT\gstack_core"
New-DirIfMissing "$AI_ROOT\CC\1_Raw"
New-DirIfMissing "$AI_ROOT\CC\2_Old"
New-DirIfMissing "$AI_ROOT\CC\3_Unused"
New-DirIfMissing "$AI_ROOT\CLL_Projects"
New-DirIfMissing "$AI_ROOT\docs"
New-DirIfMissing "$AI_ROOT\scripts\build"
New-DirIfMissing "$AI_ROOT\scripts\launch"
New-DirIfMissing "$AI_ROOT\scripts\check"
New-DirIfMissing "$AI_ROOT\scripts\fix"
New-DirIfMissing "$AI_ROOT\scripts\download"
New-DirIfMissing "$AI_ROOT\scripts\test"
New-DirIfMissing "$AI_ROOT\scripts\mod"
New-DirIfMissing "$AI_ROOT\scripts\powershell"
New-DirIfMissing "$AI_ROOT\storage\Brain"
Write-Host ""

Write-Host "=== Step 2: Categorize Python scripts ===" -ForegroundColor White
Move-FileToCategory $AI_ROOT "$AI_ROOT\scripts\build" "build_*.py"
Move-FileToCategory $AI_ROOT "$AI_ROOT\scripts\launch" "launch_*.py"
Move-FileToCategory $AI_ROOT "$AI_ROOT\scripts\launch" "direct_launch*.py"
Move-FileToCategory $AI_ROOT "$AI_ROOT\scripts\check" "check_*.py"
Move-FileToCategory $AI_ROOT "$AI_ROOT\scripts\fix" "fix_*.py"
Move-FileToCategory $AI_ROOT "$AI_ROOT\scripts\download" "download_*.py"
Move-FileToCategory $AI_ROOT "$AI_ROOT\scripts\test" "auto_test_*.py"
Move-FileToCategory $AI_ROOT "$AI_ROOT\scripts\test" "test_*.py"
Move-FileToCategory $AI_ROOT "$AI_ROOT\scripts\mod" "apply_updates.py"
Write-Host ""

Write-Host "=== Step 3: Move PowerShell scripts ===" -ForegroundColor White
Move-FileToCategory $AI_ROOT "$AI_ROOT\scripts\powershell" "*.ps1"
Write-Host ""

Write-Host "=== Step 4: Move docs and screenshots ===" -ForegroundColor White
Move-FileToCategory $AI_ROOT "$AI_ROOT\docs" "*_GUIDE*.md"
Move-FileToCategory $AI_ROOT "$AI_ROOT\docs" "ARCHITECTURE*.md"
Move-FileToCategory $AI_ROOT "$AI_ROOT\docs" "NEW_ARCHITECTURE*.md"
Move-FileToCategory $AI_ROOT "$AI_ROOT\docs" "TRAE_COMPLETE_GUIDE.md"
Move-FileToCategory $AI_ROOT "$AI_ROOT\docs" "QUICK_START_TRAE.md"
Move-FileToCategory $AI_ROOT "$AI_ROOT\docs" "PLUGIN_API_REFERENCE.md"
Move-FileToCategory $AI_ROOT "$AI_ROOT\docs" "*.png"
Write-Host ""

Write-Host "=== Step 5: Create junction links ===" -ForegroundColor White
$junctions = @(
    @{Link="$AI_ROOT\MCP"; Target="$AI_ROOT\storage\mcp"},
    @{Link="$AI_ROOT\MCP_Core"; Target="$AI_ROOT\core"},
    @{Link="$AI_ROOT\CC"; Target="$AI_ROOT\storage\CC"},
    @{Link="$AI_ROOT\CLL_Projects"; Target="$AI_ROOT\storage\cll"}
)
foreach ($j in $junctions) {
    $linkPath = $j.Link
    $targetPath = $j.Target
    if ((Test-Path $targetPath) -and -not (Test-Path $linkPath)) {
        cmd /c mklink /J "$linkPath" "$targetPath" 2>$null
        Write-Host "  [LINK] $linkPath -> $targetPath" -ForegroundColor Magenta
    } elseif (Test-Path $linkPath) {
        Write-Host "  [EXISTS] $linkPath" -ForegroundColor Yellow
    } else {
        Write-Host "  [SKIP] $targetPath not found" -ForegroundColor DarkGray
    }
}
Write-Host ""

Write-Host "=== Step 6: Check temp directories ===" -ForegroundColor White
$tempDirs = @("$AI_ROOT\temp_epca", "$AI_ROOT\extracted", "$AI_ROOT\mod_results")
foreach ($dir in $tempDirs) {
    if (Test-Path $dir) {
        $size = (Get-ChildItem $dir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        $sizeMB = [math]::Round($size / 1MB, 2)
        Write-Host "  [TEMP] $dir ($sizeMB MB) - review before deleting" -ForegroundColor DarkYellow
    }
}
Write-Host ""

Write-Host "=======================================================" -ForegroundColor Green
Write-Host "  Reorganize complete!" -ForegroundColor Green
Write-Host "  Next: Rewrite README.md + Write TUTORIAL.md" -ForegroundColor Green
Write-Host "  Next: Prepare GitHub upload" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Green
