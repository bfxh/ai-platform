# 第二波：克隆所有新发现的Houdini/Maya/Rhino/Unity/Blender开源工具
$base = "\MCP_3D"
$log = "$base\clone_wave2_log.txt"
function log($m) { $t = Get-Date -Format "HH:mm:ss"; Write-Host "[$t] $m"; Add-Content $log "[$t] $m" }

New-Item -ItemType Directory -Path "$base\Unity-tools","$base\Houdini-tools","$base\Maya-tools","$base\Rhino-tools" -Force | Out-Null

$repos = @(
    # Unity MCP servers
    @{url="https://github.com/CoplayDev/unity-mcp.git"; path="$base\Unity-tools\unity-mcp-coplay"; name="Unity MCP (Coplay)"},
    @{url="https://github.com/dsarno/unity-mcp.git"; path="$base\Unity-tools\unity-mcp-dsarno"; name="Unity MCP (dsarno/Windows)"},
    
    # Houdini
    @{url="https://github.com/sideeffects/SideFXLabs.git"; path="$base\Houdini-tools\SideFXLabs"; name="SideFX Labs (official HDA)"},
    @{url="https://github.com/wyhinton/AwesomeHoudini.git"; path="$base\Houdini-tools\AwesomeHoudini"; name="Awesome Houdini list"},
    @{url="https://github.com/ThiagoGazoni/HEGo.git"; path="$base\Houdini-tools\HEGo"; name="HEGo - Houdini for Godot"},
    
    # Maya
    @{url="https://github.com/mgear-dev/mgear4.git"; path="$base\Maya-tools\mgear4"; name="mgear4 (MIT rigging)"},
    @{url="https://github.com/AutodeskRoboticsLab/Mimic.git"; path="$base\Maya-tools\Mimic"; name="Mimic (robot control)"},
    
    # Rhino/Grasshopper
    @{url="https://github.com/robin-gdwl/Robots-in-Grasshopper.git"; path="$base\Rhino-tools\Robots-in-Grasshopper"; name="Robots in Grasshopper"},
    @{url="https://github.com/pilcru/ghpythonremote.git"; path="$base\Rhino-tools\ghpythonremote"; name="ghpythonremote"},
    @{url="https://github.com/fstwn/cockatoo.git"; path="$base\Rhino-tools\cockatoo"; name="Cockatoo (NURBS knitting)"}
)

foreach ($r in $repos) {
    if (Test-Path "$($r.path)\.git") {
        log "SKIP: $($r.name)"
        continue
    }
    log "CLONE: $($r.name)..."
    Remove-Item $r.path -Recurse -Force -ErrorAction SilentlyContinue
    git clone --depth 1 $r.url $r.path 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { log "OK: $($r.name)" }
    else { log "FAIL: $($r.name) (network)" }
}

log "=== Wave 2 complete ==="
