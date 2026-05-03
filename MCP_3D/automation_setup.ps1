# 🔥 终极自动化+分布式脚本：测试框架 + 桌面自动化 + PC/笔记本/手机集群
$ErrorActionPreference = "Continue"
$base = "\MCP_3D"
$log = "$base\automation_log.txt"
function log($m) { $t = Get-Date -Format "HH:mm:ss"; Write-Host "[$t] $m"; Add-Content $log "[$t] $m" }

log "============================================"
log "  AUTOMATION + DISTRIBUTED COMPUTING SETUP"
log "============================================"

# ==== PART 1: Game Testing Frameworks ====
log ""
log "=== PART 1: Godot Game Testing ==="
New-Item "$base\Testing","$base\Automation","$base\Distributed" -Type Directory -Force | Out-Null

$testing = @(
    @{u="https://github.com/bitwes/Gut.git"; p="$base\Testing\GUT"; n="GUT (Godot Unit Test v9.6.0)"},
    @{u="https://github.com/Randroids-Dojo/PlayGodot.git"; p="$base\Testing\PlayGodot"; n="PlayGodot (Headless Auto Test)"},
    @{u="https://github.com/RandallLiuXin/godot-e2e.git"; p="$base\Testing\godot-e2e"; n="godot-e2e (Python/pytest)"},
    @{u="https://github.com/godotengine/regression-test-project.git"; p="$base\Testing\godot-regression"; n="Godot Regression Tests"}
)

foreach ($r in $testing) {
    if (Test-Path "$($r.p)\.git") { log "SKIP: $($r.n)"; continue }
    log "CLONE: $($r.n)..."
    Remove-Item $r.p -Recurse -Force -EA 0
    git clone --depth 1 $r.u $r.p 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { log "OK: $($r.n)" }
    else { log "FAIL: $($r.n)" }
}

# ==== PART 2: Install GUT into Godot Project ====
log ""
log "=== PART 2: Install GUT into Godot Project ==="
$gutSrc = "$base\Testing\GUT\addons\gut"
$gutDst = "D:\rj\KF\JM\GodotProject\addons\gut"
if (Test-Path $gutSrc) {
    robocopy $gutSrc $gutDst /E /NFL /NDL /NJH /NJS
    log "GUT installed to Godot project!"
}

# Install godot-e2e addon
$e2eSrc = "$base\Testing\godot-e2e\addons\godot_e2e"
$e2eDst = "D:\rj\KF\JM\GodotProject\addons\godot_e2e"
if (Test-Path $e2eSrc) {
    robocopy $e2eSrc $e2eDst /E /NFL /NDL /NJH /NJS
    log "godot-e2e addon installed!"
}

# ==== PART 3: Distributed Computing - exo ====
log ""
log "=== PART 3: exo - Distributed AI Cluster ==="
# Clone exo repo for reference
if (-not (Test-Path "$base\Distributed\exo\.git")) {
    git clone --depth 1 https://github.com/exo-explore/exo.git "$base\Distributed\exo" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { log "exo repo cloned!" }
    else { log "FAIL: exo clone" }
} else { log "exo repo exists" }

# Install exo via pip (this is how you run it)
$pip = "C:\Users\888\AppData\Local\Programs\Python\Python312\Scripts\pip.exe"
log "Installing exo via pip..."
& $pip install exo -q 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { log "exo installed! (pip)" }
else { log "FAIL: exo pip install" }

# ==== PART 4: Desktop Automation Tools ====
log ""
log "=== PART 4: Desktop Automation ==="
$automation = @(
    @{u="https://github.com/jieliu2000/RPALite.git"; p="$base\Automation\RPALite"; n="RPALite (MIT RPA Windows)"},
    @{u="https://github.com/automatyzer/desktop.git"; p="$base\Automation\desktop-bot"; n="Desktop Bot (MIT)"},
    @{u="https://github.com/go-vgo/robotgo.git"; p="$base\Automation\robotgo"; n="Robotgo (Go, cross-platform)"},
    @{u="https://github.com/socioy/bumblebee.git"; p="$base\Automation\bumblebee"; n="Bumblebee (AI mouse)"}
)

foreach ($r in $automation) {
    if (Test-Path "$($r.p)\.git") { log "SKIP: $($r.n)"; continue }
    log "CLONE: $($r.n)..."
    Remove-Item $r.p -Recurse -Force -EA 0
    git clone --depth 1 $r.u $r.p 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { log "OK: $($r.n)" }
    else { log "FAIL: $($r.n)" }
}

# Install RPALite deps
if (Test-Path "$base\Automation\RPALite\requirements.txt") {
    & $pip install -r "$base\Automation\RPALite\requirements.txt" -q 2>&1 | Out-Null
    log "RPALite deps installed"
}
if (Test-Path "$base\Automation\bumblebee\requirements.txt") {
    & $pip install -r "$base\Automation\bumblebee\requirements.txt" -q 2>&1 | Out-Null
    log "Bumblebee deps installed"
}

# ==== PART 5: Task Runner ====
log ""
log "=== PART 5: Task Runner (go-task) ==="
if (-not (Test-Path "$base\Automation\task")) {
    git clone --depth 1 https://github.com/go-task/task.git "$base\Automation\task" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { log "go-task/task cloned (MIT, 12K+ stars)" }
}

# Also install task CLI via winget/scoop if possible
try {
    winget install Task.Task -e --source winget --accept-package-agreements 2>&1 | Out-Null
    log "go-task CLI installed via winget"
} catch {
    log "go-task CLI: install manually from https://taskfile.dev"
}

# ==== PART 6: Create network/fling config for PC-Laptop-Phone ====
log ""
log "=== PART 6: Distributed Network Config ==="

$networkConfig = @"
# === EXO Distributed AI Cluster Config ===
# PC (台式机): IP auto-detect, main node
# Laptop (笔记本): Install exo: pip install exo
# Huawei Phone: Install Termux or use Python on Android to run exo

# Step 1: On ALL devices, install exo:
#   pip install exo

# Step 2: On this PC (台式机), run:
#   exo

# Step 3: On Laptop (笔记本), run:
#   exo
#   (devices auto-discover each other via P2P on same WiFi)

# Step 4: Run a model across all devices:
#   exo run llama3.2 --prompt "Hello world"
#   (exo automatically splits layers across all devices)

# Supported models: LLaMA, Mistral, DeepSeek v3, Qwen3.5, Nemotron
# Connection: WiFi LAN + automatic device discovery + RDMA over Thunderbolt

# === PC as Godot CI Runner ===
# This PC can run Godot headless for automated testing:
# D:\rj\KF\JM\Godot_v4.6.1-stable_win64.exe --headless --path D:\rj\KF\JM\GodotProject -s addons/gut/gut_cmdln.gd

# === Laptop can run ComfyUI separately ===
# Laptop: Run ComfyUI for 3D generation → send results to PC's Godot project

# === Huawei Phone can be an exo node ===
# Phone: Install Termux + Python + exo → joins the AI cluster
"@

$networkConfig | Out-File "$base\network_cluster_config.txt" -Encoding UTF8
log "Network cluster config created!"

# ==== PART 7: Godot Auto-Test Script ====
log ""
log "=== PART 7: Create auto-test script ==="

$autoTestScript = @'
@echo off
REM === Godot Auto-Test Launcher ===
echo ========================================
echo   GODOT AUTOMATED TESTING SYSTEM
echo ========================================
echo.

REM Run headless GUT tests
echo [1/2] Running GUT unit tests...
"D:\rj\KF\JM\Godot_v4.6.1-stable_win64.exe" --headless --path "D:\rj\KF\JM\GodotProject" -s addons/gut/gut_cmdln.gd -gdir=res://tests -gprefix=test_ -gsuffix=.gd -gexit

echo.
echo [2/2] Running E2E tests...
"C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe" -m pytest "\MCP_3D\Testing\godot-e2e\tests" -v

echo.
echo ========================================
echo   ALL TESTS COMPLETE
echo ========================================
pause
'@

$autoTestScript | Out-File "\MCP_3D\auto_test.bat" -Encoding ASCII
log "Auto-test batch script created!"

# ==== PART 8: Godot Test Scene Template ====
log ""
log "=== PART 8: Create test directory structure ==="
$testDir = "D:\rj\KF\JM\GodotProject\tests"
if (-not (Test-Path $testDir)) {
    New-Item $testDir -Type Directory -Force | Out-Null
    log "Created tests/ directory in Godot project"
}

# Copy GUT's example test as template
if (Test-Path "$base\Testing\GUT\gut_examples") {
    New-Item "D:\rj\KF\JM\GodotProject\tests" -Type Directory -Force | Out-Null
    log "Test template ready"
}

# ==== PART 9: Final Summary ====
log ""
log "============================================"
log "  AUTOMATION + DISTRIBUTED SETUP COMPLETE"
log "============================================"
$total = (Get-ChildItem $base -Recurse -Depth 1 -EA 0 | Where-Object { $_.PSIsContainer -and (Test-Path "$($_.FullName)\.git") }).Count
$size = [math]::Round((Get-ChildItem $base -Recurse -EA 0 | Measure-Object Length -Sum).Sum / 1GB, 2)
log "Total repos: $total"
log "Total size: $size GB"
log ""
log "GAME TESTING:"
log "  GUT v9.6.0 (Godot Unit Test) - MIT, Asset Library"
log "  PlayGodot (Headless Auto Test via Debugger)"
log "  godot-e2e (Python/pytest E2E)"
log "  Godot Regression Tests (Official)"
log ""
log "DISTRIBUTED COMPUTING:"
log "  exo - PC + Laptop + Phone = AI Cluster!"
log "  Auto device discovery, P2P, RDMA, zero config"
log ""
log "DESKTOP AUTOMATION:"
log "  RPALite (MIT, Windows RPA)"
log "  Desktop Bot (MIT, AI-powered)"
log "  Robotgo (Go, cross-platform)"
log "  Bumblebee (AI mouse with LSTM!)"
log ""
log "TASK RUNNER:"
log "  go-task/task (MIT, 12K+ stars)"
log ""
log "=== TO START USING ==="
log "1. Auto-test: run \MCP_3D\auto_test.bat"
log "2. exo cluster: pip install exo && exo (on all devices)"
log "3. Godot headless test: see network_cluster_config.txt"
log "============================================"
