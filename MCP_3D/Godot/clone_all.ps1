$base = "\MCP_3D\Godot"
$py = "C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe"
$pip = "C:\Users\888\AppData\Local\Programs\Python\Python312\Scripts\pip.exe"
$log = "$base\clone_log.txt"
function log($m) { $t = Get-Date -Format "HH:mm:ss"; $l = "[$t] $m"; Write-Host $l; Add-Content $log $l }

New-Item -ItemType Directory -Path "$base\addons","$base\gdextension","$base\tools" -Force | Out-Null

$repos = @(
    @{url="https://github.com/Coding-Solo/godot-mcp.git"; path="$base\godot-mcp-coding-solo"; name="Coding-Solo/godot-mcp"},
    @{url="https://github.com/af009/fuku.git"; path="$base\addons\fuku"; name="af009/fuku"},
    @{url="https://github.com/Godot4-Addons/ai_assistant_for_godot.git"; path="$base\addons\ai_coding_assistant"; name="AI Coding Assistant"},
    @{url="https://github.com/FlamxGames/godot-ai-assistant-hub.git"; path="$base\addons\ai_assistant_hub"; name="AI Assistant Hub"},
    @{url="https://github.com/Adriankhl/godot-llm.git"; path="$base\gdextension\godot-llm"; name="godot-llm"},
    @{url="https://github.com/xarillian/GDLlama.git"; path="$base\gdextension\GDLlama"; name="GDLlama"},
    @{url="https://github.com/robertvaradan/voronoishatter.git"; path="$base\tools\voronoishatter"; name="voronoishatter"},
    @{url="https://github.com/OffByTwoDev/Destruct3D.git"; path="$base\tools\Destruct3D"; name="Destruct3D"},
    @{url="https://github.com/mickeyordev/godot-ai-context-generator.git"; path="$base\tools\ai-context-generator"; name="AI Context Generator"}
)

foreach ($r in $repos) {
    if (Test-Path "$($r.path)\.git") {
        log "SKIP: $($r.name) (already cloned)"
        continue
    }
    log "CLONE: $($r.name) ..."
    Remove-Item $r.path -Recurse -Force -ErrorAction SilentlyContinue
    git clone --depth 1 $r.url $r.path 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { log "OK: $($r.name)" }
    else { log "FAIL: $($r.name) code=$LASTEXITCODE" }
}

log "=== Installing npm deps ==="
foreach ($dir in @("$base\godot-mcp-vollkorn", "$base\godot-mcp-coding-solo", "$base\godot-bridge-mcp", "$base\godot-mcp-cn")) {
    if (Test-Path "$dir\package.json") {
        log "npm install: $dir"
        Push-Location $dir
        npm install --no-audit --no-fund 2>&1 | Out-Null
        Pop-Location
        log "npm done: $dir"
    }
}

log "=== Installing Python deps ==="
& $pip install fastmcp -q 2>&1 | Out-Null
log "fastmcp installed"

log "=== ALL DONE ==="
