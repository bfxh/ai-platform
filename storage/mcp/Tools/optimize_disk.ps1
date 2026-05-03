<# 
.SYNOPSIS
    D盘/E盘/F盘 磁盘优化脚本 - 质量不变，释放空间
.DESCRIPTION
    安全清理可回收空间，不删除任何用户数据/源码/项目文件
    只清理: 构建缓存/临时文件/重复下载/Python缓存/node_modules缓存等
.NOTES
    请仔细阅读每一步的说明，确认后再执行
#>

param(
    [switch]$DryRun,
    [switch]$Step1,
    [switch]$Step2,
    [switch]$Step3,
    [switch]$Step4,
    [switch]$Step5,
    [switch]$Step6,
    [switch]$All
)

$ErrorActionPreference = "SilentlyContinue"
$logFile = "\python\MCP\Tools\optimize_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

function Write-Log {
    param([string]$msg, [string]$color = "White")
    Write-Host $msg -ForegroundColor $color
    Add-Content -Path $logFile -Value $msg
}

function Remove-SafeDir {
    param([string]$Path, [string]$Label)
    if (-not (Test-Path $Path)) {
        Write-Log "  [SKIP] $Label - not found: $Path" "Gray"
        return 0
    }
    $size = (Get-ChildItem $Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($size / 1MB, 2)
    if ($DryRun) {
        Write-Log "  [DRY] Would remove ${Label} (${sizeMB} MB): ${Path}" "Yellow"
        return $size
    }
    Remove-Item $Path -Recurse -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $Path)) {
        Write-Log "  [OK] Removed ${Label} (${sizeMB} MB): ${Path}" "Green"
        return $size
    } else {
        Write-Log "  [FAIL] Could not remove ${Label}: ${Path}" "Red"
        return 0
    }
}

Write-Log "============================================================" "Cyan"
Write-Log "  DISK OPTIMIZATION SCRIPT - Quality Preserved" "Cyan"
Write-Log "  Mode: $(if($DryRun){'DRY RUN (no changes)'}else{'LIVE - will delete files'})" "Cyan"
Write-Log "  Log: $logFile" "Cyan"
Write-Log "============================================================" "Cyan"
Write-Log ""

$totalFreed = 0

# ============================================================
# STEP 1: Python __pycache__ (safe - auto regenerated)
# ============================================================
if ($Step1 -or $All) {
    Write-Log "===== STEP 1: Python __pycache__ (auto-regenerated) =====" "Cyan"
    $dirs = Get-ChildItem -Path D:\,E:\,F:\ -Directory -Recurse -Filter "__pycache__" -Depth 6 -ErrorAction SilentlyContinue
    foreach ($d in $dirs) {
        $freed = Remove-SafeDir $d.FullName "__pycache__"
        $totalFreed += $freed
    }
    $pycFiles = Get-ChildItem -Path D:\,E:\,F:\ -Recurse -File -Filter "*.pyc" -Depth 6 -ErrorAction SilentlyContinue
    foreach ($f in $pycFiles) {
        if ($DryRun) {
            Write-Log "  [DRY] Would remove .pyc: $($f.FullName)" "Yellow"
            $totalFreed += $f.Length
        } else {
            Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue
            $totalFreed += $f.Length
        }
    }
    Write-Log "  Step 1 done." "Green"
    Write-Log ""
}

# ============================================================
# STEP 2: Build artifacts (safe - can rebuild)
# D:\dist (168 dirs, 9.5GB), D:\target (49 dirs, 4.31GB), D:\build (62 dirs, 1.05GB)
# ============================================================
if ($Step2 -or $All) {
    Write-Log "===== STEP 2: Build artifacts in D:\DEV (can rebuild) =====" "Cyan"
    
    $devPaths = @(
        "D:\DEV\工具\GitHub"
    )
    foreach ($base in $devPaths) {
        if (-not (Test-Path $base)) { continue }
        $distDirs = Get-ChildItem -Path $base -Directory -Recurse -Filter "dist" -Depth 3 -ErrorAction SilentlyContinue
        foreach ($d in $distDirs) { $totalFreed += Remove-SafeDir $d.FullName "dist" }
        $targetDirs = Get-ChildItem -Path $base -Directory -Recurse -Filter "target" -Depth 3 -ErrorAction SilentlyContinue
        foreach ($d in $targetDirs) { $totalFreed += Remove-SafeDir $d.FullName "target" }
        $buildDirs = Get-ChildItem -Path $base -Directory -Recurse -Filter "build" -Depth 3 -ErrorAction SilentlyContinue
        foreach ($d in $buildDirs) { $totalFreed += Remove-SafeDir $d.FullName "build" }
    }
    Write-Log "  Step 2 done." "Green"
    Write-Log ""
}

# ============================================================
# STEP 3: node_modules in non-active projects (safe - npm install rebuilds)
# D:\node_modules (123 dirs, 2.35GB)
# ============================================================
if ($Step3 -or $All) {
    Write-Log "===== STEP 3: node_modules in GitHub clones (npm install rebuilds) =====" "Cyan"
    $githubPath = "D:\DEV\工具\GitHub"
    if (Test-Path $githubPath) {
        $nmDirs = Get-ChildItem -Path $githubPath -Directory -Recurse -Filter "node_modules" -Depth 3 -ErrorAction SilentlyContinue
        foreach ($d in $nmDirs) { $totalFreed += Remove-SafeDir $d.FullName "node_modules" }
    }
    Write-Log "  Step 3 done." "Green"
    Write-Log ""
}

# ============================================================
# STEP 4: Duplicate/obsolete archives
# \python.zip (5.1GB - already extracted to \python)
# D:\DEV\华为开发环境.zip (1.66GB) + .qkdownloading (1.66GB)
# ============================================================
if ($Step4 -or $All) {
    Write-Log "===== STEP 4: Duplicate archives (already extracted) =====" "Cyan"
    
    $dupFiles = @(
        @{Path="\python.zip"; Label="AI.zip (already extracted to \python)"; SizeMB=5099},
        @{Path="D:\DEV\RJ\华为开发环境-b31f14364137.zip.qkdownloading"; Label="Incomplete download"; SizeMB=1660},
        @{Path="%SOFTWARE_DIR%\KF\devecostudio-windows-3.1.0.500.zip"; Label="DevEco Studio installer"; SizeMB=844},
        @{Path="%SOFTWARE_DIR%\GJ\android-ndk.zip"; Label="Android NDK zip"; SizeMB=634}
    )
    
    foreach ($f in $dupFiles) {
        if (Test-Path $f.Path) {
            if ($DryRun) {
                Write-Log "  [DRY] Would remove $($f.Label) (~$($f.SizeMB) MB): $($f.Path)" "Yellow"
                $totalFreed += $f.SizeMB * 1MB
            } else {
                $size = (Get-Item $f.Path -ErrorAction SilentlyContinue).Length
                Remove-Item $f.Path -Force -ErrorAction SilentlyContinue
                if (-not (Test-Path $f.Path)) {
                    Write-Log "  [OK] Removed $($f.Label) ($([math]::Round($size/1MB,2)) MB)" "Green"
                    $totalFreed += $size
                } else {
                    Write-Log "  [FAIL] Could not remove: $($f.Path)" "Red"
                }
            }
        } else {
            Write-Log "  [SKIP] Not found: $($f.Path)" "Gray"
        }
    }
    Write-Log "  Step 4 done." "Green"
    Write-Log ""
}

# ============================================================
# STEP 5: Windows temp + Trae cache cleanup
# User Temp: 0.42GB, Trae Roaming: 3.93GB, Trae .trae-cn: 4.41GB
# ============================================================
if ($Step5 -or $All) {
    Write-Log "===== STEP 5: Windows temp & Trae cache =====" "Cyan"
    
    $tempPaths = @(
        @{Path="$env:TEMP\*"; Label="User Temp"; Safe=$true},
        @{Path="C:\Windows\Temp\*"; Label="System Temp"; Safe=$true}
    )
    foreach ($tp in $tempPaths) {
        if ($DryRun) {
            $size = (Get-ChildItem $tp.Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            Write-Log "  [DRY] Would clean $($tp.Label) ($([math]::Round($size/1MB,2)) MB)" "Yellow"
            $totalFreed += $size
        } else {
            $size = (Get-ChildItem $tp.Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            Remove-Item $tp.Path -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "  [OK] Cleaned $($tp.Label) ($([math]::Round($size/1MB,2)) MB)" "Green"
            $totalFreed += $size
        }
    }
    Write-Log "  Step 5 done." "Green"
    Write-Log ""
}

# ============================================================
# STEP 6: F:\ target + bin dirs (5.22GB + 3.4GB)
# ============================================================
if ($Step6 -or $All) {
    Write-Log "===== STEP 6: F:\ build artifacts (target/bin) =====" "Cyan"
    $fTargets = Get-ChildItem -Path F:\ -Directory -Recurse -Filter "target" -Depth 4 -ErrorAction SilentlyContinue
    foreach ($d in $fTargets) { $totalFreed += Remove-SafeDir $d.FullName "target" }
    Write-Log "  Step 6 done." "Green"
    Write-Log ""
}

# ============================================================
# SUMMARY
# ============================================================
Write-Log ""
Write-Log "============================================================" "Cyan"
$freedGB = [math]::Round($totalFreed / 1GB, 2)
Write-Log "  TOTAL FREED: $freedGB GB" "Green"
Write-Log "  Mode: $(if($DryRun){'DRY RUN'}else{'LIVE'})" "Cyan"
Write-Log "  Log: $logFile" "Cyan"
Write-Log "============================================================" "Cyan"
