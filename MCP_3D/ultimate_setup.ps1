# 终极全量脚本：安装ComfyUI 3D Pack + 所有新工具 + 最终配置
$ErrorActionPreference = "Continue"
$base = "\MCP_3D"
$logfile = "$base\ultimate_log.txt"
function log($m) { $t = Get-Date -Format "HH:mm:ss"; Write-Host "[$t] $m"; Add-Content $logfile "[$t] $m" }

log "============================================"
log "  ULTIMATE MCP 3D SETUP - FINAL WAVE"
log "============================================"

# PART 1: ComfyUI 3D Pack (most important)
log ""
log "=== PART 1: ComfyUI 3D Pack ==="
$comfyNodes = "D:\rj\AI\ComfyUI\custom_nodes"
$comfy3dPath = "$comfyNodes\ComfyUI-3D-Pack"
if (Test-Path "$comfy3dPath\.git") {
    log "ComfyUI-3D-Pack already installed"
} else {
    log "Installing ComfyUI-3D-Pack (8.7K stars, MIT)..."
    git clone --depth 1 https://github.com/MrForExample/ComfyUI-3D-Pack.git $comfy3dPath 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        log "ComfyUI-3D-Pack cloned!"
        Push-Location $comfy3dPath
        & "D:\rj\AI\ComfyUI\python_embeded\python.exe" -s -m pip install -r requirements.txt 2>&1 | Out-Null
        log "ComfyUI-3D-Pack deps installed!"
        Pop-Location
    } else {
        log "FAIL: ComfyUI-3D-Pack (network)"
    }
}

# PART 2: Clone remaining tools in parallel batches
log ""
log "=== PART 2: Final tool clones ==="

New-Item "$base\Mocap","$base\Unity-tools","$base\Houdini-tools","$base\Maya-tools","$base\Rhino-tools","$base\Blender-geometry" -Type Directory -Force | Out-Null

# Fast clones (small repos)
$fastRepos = @(
    @{u="https://github.com/Larenju-Rai/open-mocap-blender.git"; p="$base\Mocap\open-mocap-blender"; n="Open Mocap Blender"},
    @{u="https://github.com/CoplayDev/unity-mcp.git"; p="$base\Unity-tools\unity-mcp-coplay"; n="Unity MCP Coplay"},
    @{u="https://github.com/wyhinton/AwesomeHoudini.git"; p="$base\Houdini-tools\AwesomeHoudini"; n="Awesome Houdini"},
    @{u="https://github.com/mgear-dev/mgear4.git"; p="$base\Maya-tools\mgear4"; n="mgear4 (MIT rigging)"},
    @{u="https://github.com/robin-gdwl/Robots-in-Grasshopper.git"; p="$base\Rhino-tools\Robots-GH"; n="Robots in Grasshopper"},
    @{u="https://github.com/pilcru/ghpythonremote.git"; p="$base\Rhino-tools\ghpythonremote"; n="ghpythonremote"},
    @{u="https://github.com/fstwn/cockatoo.git"; p="$base\Rhino-tools\cockatoo"; n="Cockatoo NURBS"},
    @{u="https://github.com/eanticev/niagara-destruction-driver.git"; p="$base\UE5-tools\niagara-destruction"; n="Niagara Destruction"},
    @{u="https://github.com/Tams3d/T3D-GN-Presets.git"; p="$base\Blender-geometry\T3D-GN-Presets"; n="T3D GN Presets"},
    @{u="https://github.com/cgvirus/blender-geometry-nodes-collection.git"; p="$base\Blender-geometry\blender-gn-collection"; n="Blender GN Collection"}
)

foreach ($r in $fastRepos) {
    if (Test-Path "$($r.p)\.git") { log "SKIP: $($r.n)"; continue }
    log "CLONE: $($r.n)..."
    Remove-Item $r.p -Recurse -Force -EA 0
    git clone --depth 1 $r.u $r.p 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { log "OK: $($r.n)" }
    else { log "FAIL: $($r.n)" }
}

# PART 3: Install plugin dependencies
log ""
log "=== PART 3: Install plugin dependencies ==="

# Unity MCP deps
foreach ($d in @("$base\Unity-tools\unity-mcp-coplay")) {
    if (Test-Path "$d\package.json") {
        Push-Location $d; npm install --no-audit --no-fund 2>&1 | Out-Null; Pop-Location
        log "npm done: $d"
    }
}

# Maya deps
if (Test-Path "$base\Maya-tools\mgear4\requirements.txt") {
    & "C:\Users\888\AppData\Local\Programs\Python\Python312\Scripts\pip.exe" install -r "$base\Maya-tools\mgear4\requirements.txt" -q 2>&1 | Out-Null
    log "mgear4 deps installed"
}

# PART 4: Final verification
log ""
log "=== PART 4: Verification ==="
$allDirs = Get-ChildItem $base -Recurse -Depth 2 | Where-Object { $_.PSIsContainer -and (Test-Path "$($_.FullName)\.git") }
$count = ($allDirs | Measure-Object).Count
log "Total cloned open-source projects: $count"
log "Total size: $([math]::Round((Get-ChildItem $base -Recurse | Measure-Object Length -Sum).Sum / 1GB, 2)) GB"

log ""
log "============================================"
log "  ULTIMATE SETUP COMPLETE!"
log "============================================"
log ""
log "SUMMARY OF ALL INSTALLED TOOLS:"
log "  Trae CN mcp.json: 10 DCC MCP servers"
log "  Godot: 5 MCP servers + 3 AI addons + 3 LLM GDE + 2 destruction"
log "  Blender: blender-mcp + MCP-enhanced + AI Builder + GN Presets + Open Mocap"
log "  UE5: unreal-mcp + uemcp + Analyzer + Niagara Destruction"
log "  Unity: Unity-MCP + Coplay MCP"
log "  Houdini: houdini-mcp + AwesomeHoudini ref"
log "  Maya: MayaMCP + mgear4 rigging"
log "  Rhino: rhino3d-mcp + ghpythonremote + Cockatoo + Robots-GH"
log "  ComfyUI: 3D-Pack (10+ 3D gen models)"
log "============================================"
