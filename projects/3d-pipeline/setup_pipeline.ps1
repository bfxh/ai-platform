<#
.SYNOPSIS
    LingBot-Map 跨设备3D重建流水线 - 一键配置脚本
.DESCRIPTION
    配置三台设备协同工作：华为手机(采集) + 笔记本(CPU预处理) + 台式机(GPU推理)
.NOTES
    设备: 华为HarmonyOS + Windows笔记本 + Windows台式机(RTX 4060 Ti)
#>

$ErrorActionPreference = "Stop"

$ProjectDir = "\python\projects\lingbot-map"
$PipelineDir = "\python\projects\3d-pipeline"
$Python312 = "$env:USERPROFILE\AppData\Local\Programs\Python\Python312\python.exe"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  跨设备3D重建流水线 - 环境配置" -ForegroundColor Cyan
Write-Host "  手机(采集) + 笔记本(CPU) + 台式机(GPU)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ---- Step 1: 手机连接工具 ----
Write-Host "[1/5] 安装手机连接工具..." -ForegroundColor Yellow

Write-Host "  -> 安装 scrcpy (手机投屏+控制)..." -ForegroundColor Gray
$scrcpyDir = "$env:USERPROFILE\Downloads\scrcpy"
if (-not (Test-Path $scrcpyDir)) {
    $scrcpyDir = "\python\downloads\scrcpy"
}
if (Get-Command scrcpy -ErrorAction SilentlyContinue) {
    Write-Host "  -> scrcpy already installed" -ForegroundColor Green
} else {
    Write-Host "  -> scrcpy: https://github.com/Genymobile/scrcpy/releases" -ForegroundColor DarkYellow
    Write-Host "     Download win64 zip, extract to \python\downloads\scrcpy" -ForegroundColor DarkYellow
}

Write-Host "  -> 安装 ADB (Android Debug Bridge)..." -ForegroundColor Gray
if (Get-Command adb -ErrorAction SilentlyContinue) {
    Write-Host "  -> adb already installed" -ForegroundColor Green
} else {
    & $Python312 -m pip install adbutils -q 2>$null
    Write-Host "  -> adb: will use scrcpy bundled version" -ForegroundColor DarkYellow
}

# ---- Step 2: 创建流水线目录结构 ----
Write-Host "[2/5] 创建流水线目录..." -ForegroundColor Yellow

$dirs = @(
    "$PipelineDir",
    "$PipelineDir\01_phone_capture",
    "$PipelineDir\02_laptop_preprocess",
    "$PipelineDir\03_desktop_reconstruct",
    "$PipelineDir\04_results",
    "$PipelineDir\shared",
    "$PipelineDir\scripts"
)

foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        Write-Host "  -> Created: $d" -ForegroundColor Gray
    }
}

# ---- Step 3: 安装COLMAP ----
Write-Host "[3/5] 检查COLMAP安装..." -ForegroundColor Yellow
if (Get-Command colmap -ErrorAction SilentlyContinue) {
    $colmapVer = colmap --version 2>&1
    Write-Host "  -> COLMAP $colmapVer already installed" -ForegroundColor Green
} else {
    Write-Host "  -> COLMAP not found. Installing via pip..." -ForegroundColor Gray
    & $Python312 -m pip install colmap -q 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  -> pip install failed. Manual install required:" -ForegroundColor Red
        Write-Host "     Download: https://github.com/colmap/colmap/releases" -ForegroundColor Red
        Write-Host "     Extract to: \python\downloads\colmap" -ForegroundColor Red
        Write-Host "     Add to PATH" -ForegroundColor Red
    }
}

# ---- Step 4: 安装3DGS ----
Write-Host "[4/5] 检查3D Gaussian Splatting..." -ForegroundColor Yellow
$gsDir = "\python\projects\gaussian-splatting"
if (Test-Path $gsDir) {
    Write-Host "  -> 3DGS already cloned" -ForegroundColor Green
} else {
    Write-Host "  -> 3DGS: will clone when needed" -ForegroundColor Gray
}

# ---- Step 5: 配置局域网共享 ----
Write-Host "[5/5] 配置局域网共享..." -ForegroundColor Yellow
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "127.*" } | Select-Object -First 1).IPAddress
Write-Host "  -> 本机IP: $localIP" -ForegroundColor Cyan

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  配置完成!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步:" -ForegroundColor Cyan
Write-Host "  1. 手机连接: 运行 scripts\phone_connect.bat" -ForegroundColor White
Write-Host "  2. 笔记本预处理: 运行 scripts\laptop_preprocess.bat" -ForegroundColor White
Write-Host "  3. 台式机重建: 运行 scripts\desktop_reconstruct.bat" -ForegroundColor White
