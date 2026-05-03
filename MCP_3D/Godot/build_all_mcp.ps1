$base = "\MCP_3D\Godot"
$py = "C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe"
$pip = "C:\Users\888\AppData\Local\Programs\Python\Python312\Scripts\pip.exe"
$log = "$base\build_log.txt"

function log($m) { $t = Get-Date -Format "HH:mm:ss"; $l = "[$t] $m"; Write-Host $l; Add-Content $log $l }

New-Item -ItemType File -Path $log -Force | Out-Null
log "=== Godot MCP 全构建开始 ==="

# 1. godot-mcp-vollkorn (主选 MCP Server)
log "--- 构建 godot-mcp-vollkorn ---"
Push-Location "$base\godot-mcp-vollkorn"
if (Test-Path "node_modules\.package-lock.json") {
    log "依赖已安装，跳过 npm install"
} else {
    log "安装依赖..."
    npm install --no-audit --no-fund 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { log "npm install 失败，尝试 pnpm..."; pnpm install --no-frozen-lockfile 2>&1 | Out-Null }
}
log "编译 TypeScript..."
npx tsc 2>&1 | Out-Null
if (Test-Path "scripts\build.js") {
    node scripts/build.js 2>&1 | Out-Null
}
if (Test-Path "build\index.js") { log "OK: godot-mcp-vollkorn build/index.js" }
else { log "FAIL: godot-mcp-vollkorn 构建失败" }
Pop-Location

# 2. godot-mcp-coding-solo (备选 MCP Server)
log "--- 构建 godot-mcp-coding-solo ---"
Push-Location "$base\godot-mcp-coding-solo"
if (Test-Path "node_modules\.package-lock.json") {
    log "依赖已安装"
} else {
    log "安装依赖..."
    npm install --no-audit --no-fund 2>&1 | Out-Null
}
log "编译 TypeScript..."
npx tsc 2>&1 | Out-Null
if (Test-Path "scripts\build.js") {
    node scripts/build.js 2>&1 | Out-Null
}
if (Test-Path "build\index.js") { log "OK: godot-mcp-coding-solo build/index.js" }
else { log "FAIL: godot-mcp-coding-solo 构建失败" }
Pop-Location

# 3. godot-mcp-cn (中文 MCP Server)
log "--- 构建 godot-mcp-cn ---"
Push-Location "$base\godot-mcp-cn\server"
if (-not (Test-Path "node_modules")) {
    log "安装依赖..."
    npm install --no-audit --no-fund 2>&1 | Out-Null
}
log "编译 TypeScript..."
npx tsc 2>&1 | Out-Null
if (Test-Path "dist\index.js") { log "OK: godot-mcp-cn server/dist/index.js" }
else { log "FAIL: godot-mcp-cn 构建失败" }
Pop-Location

# 4. godot-bridge-mcp (Python MCP bridge)
log "--- 安装 godot-bridge-mcp ---"
Push-Location "$base\godot-bridge-mcp\mcp-server"
if (Test-Path "requirements.txt") {
    & $pip install -r requirements.txt -q 2>&1 | Out-Null
    log "Python 依赖已安装"
} else {
    log "WARN: godot-bridge-mcp 无 requirements.txt"
}
Pop-Location

# 5. godot-ai-higodot (Python MCP Server)
log "--- 安装 godot-ai-higodot ---"
Push-Location "$base\godot-ai-higodot"
& $pip install -e . -q 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { log "OK: godot-ai-higodot 已安装" }
else { log "WARN: godot-ai-higodot 安装可能有误，检查输出" }
Pop-Location

log "=== 全部构建完成 ==="
Write-Host "`n构建日志: $log" -ForegroundColor Green
