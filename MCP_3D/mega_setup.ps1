# GIF 终极全量脚本：克隆+安装+启用所有
$ErrorActionPreference = "Continue"
$base = "\MCP_3D"
$logfile = "$base\mega_log.txt"
function log($m) { $t = Get-Date -Format "HH:mm:ss"; Write-Host "[$t] $m"; Add-Content $logfile "[$t] $m" }

log "============================================"
log "  MEGA OPEN-SOURCE 3D ECOSYSTEM SETUP"
log "============================================"

# ==== PART 1: Clone new discovered repos ====
log ""
log "=== PART 1: Clone new open-source repos ==="
New-Item "$base\ComfyUI-nodes","$base\Audio-tools","$base\GameDev-resources","$base\Godot-physics","$base\Blender-rigging" -Type Directory -Force | Out-Null

$newRepos = @(
    # ComfyUI 3D nodes (MIT)
    @{u="https://github.com/ubisoft/ComfyUI-Chord.git"; p="$base\ComfyUI-nodes\ComfyUI-Chord"; n="CHORD (Ubisoft PBR)"},
    @{u="https://github.com/amtarr/ComfyUI-TextureAlchemy.git"; p="$base\ComfyUI-nodes\ComfyUI-TextureAlchemy"; n="TextureAlchemy (38 nodes)"},
    @{u="https://github.com/jalberty2018/awesome-comfyui.git"; p="$base\ComfyUI-nodes\awesome-comfyui"; n="Awesome ComfyUI"},
    
    # Audio/Music (MIT)
    @{u="https://github.com/facebookresearch/audiocraft.git"; p="$base\Audio-tools\audiocraft"; n="MusicGen (Meta)"},
    @{u="https://github.com/Stability-AI/stable-audio-tools.git"; p="$base\Audio-tools\stable-audio-tools"; n="Stable Audio Tools"},
    @{u="https://github.com/RegoDefies/Rag-MusicPrompt.git"; p="$base\Audio-tools\Rag-MusicPrompt"; n="Rag-MusicPrompt"},
    
    # GameDev Resources
    @{u="https://github.com/madjin/awesome-cc0.git"; p="$base\GameDev-resources\awesome-cc0"; n="Awesome CC0"},
    @{u="https://github.com/Kavex/GameDev-Resources.git"; p="$base\GameDev-resources\GameDev-Resources"; n="GameDev Resources"},
    
    # Godot Physics (MIT)
    @{u="https://github.com/appsinacup/godot-rapier-physics.git"; p="$base\Godot-physics\godot-rapier-physics"; n="Godot Rapier Physics (Fluids!)"},
    @{u="https://github.com/erayzesen/godot-quarkphysics.git"; p="$base\Godot-physics\godot-quarkphysics"; n="Godot QuarkPhysics (SoftBody)"},
    
    # Blender Rigging/Retarget
    @{u="https://github.com/TheMightyGinkgo/TMG-Action-Jackson.git"; p="$base\Blender-rigging\TMG-Action-Jackson"; n="TMG Action Jackson (Retarget)"}
)

foreach ($r in $newRepos) {
    if (Test-Path "$($r.p)\.git") { log "SKIP: $($r.n)"; continue }
    log "CLONE: $($r.n)..."
    Remove-Item $r.p -Recurse -Force -EA 0
    git clone --depth 1 $r.u $r.p 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { log "OK: $($r.n)" }
    else { log "FAIL: $($r.n)" }
}

# ==== PART 2: Install ComfyUI nodes into actual ComfyUI ====
log ""
log "=== PART 2: Install ComfyUI nodes ==="
$comfyNodes = "D:\rj\AI\ComfyUI\custom_nodes"

# CHORD
$chordSrc = "$base\ComfyUI-nodes\ComfyUI-Chord"
$chordDst = "$comfyNodes\ComfyUI-Chord"
if (Test-Path $chordSrc) {
    if (-not (Test-Path $chordDst)) {
        robocopy $chordSrc $chordDst /E /NFL /NDL /NJH /NJS
        log "CHORD installed to ComfyUI!"
    } else { log "CHORD already in ComfyUI" }
}

# TextureAlchemy
$taSrc = "$base\ComfyUI-nodes\ComfyUI-TextureAlchemy"
$taDst = "$comfyNodes\ComfyUI-TextureAlchemy"
if (Test-Path $taSrc) {
    if (-not (Test-Path $taDst)) {
        robocopy $taSrc $taDst /E /NFL /NDL /NJH /NJS
        log "TextureAlchemy installed to ComfyUI!"
    } else { log "TextureAlchemy already in ComfyUI" }
}

# Install NVIDIA GenAI Creator Toolkit
if (-not (Test-Path "$comfyNodes\NVIDIA-GenAI-Creator-Toolkit")) {
    log "Cloning NVIDIA GenAI Creator Toolkit..."
    git clone --depth 1 https://github.com/NVIDIA/NVIDIA-GenAI-Creator-Toolkit.git "$comfyNodes\NVIDIA-GenAI-Creator-Toolkit" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { log "NVIDIA GenAI Toolkit installed!" }
    else { log "FAIL: NVIDIA GenAI (network)" }
}

# ==== PART 3: Enable Godot plugins in project.godot ====
log ""
log "=== PART 3: Enable Godot plugins ==="
$godotProj = "D:\rj\KF\JM\GodotProject\project.godot"
$content = Get-Content $godotProj -Raw

$plugins = @(
    "fuku", "godot_ai", "ai_context_generator", "voronoishatter",
    "godot_mcp_vollkorn", "godot-jolt", "mesh-slicing-gdextension",
    "godot-concave-mesh-slicer", "fragment_weapon_system"
)

foreach ($p in $plugins) {
    $pattern = "$p/enabled=true"
    if ($content -notmatch [regex]::Escape($pattern)) {
        $content = $content -replace "($p/enabled=)false", "`$1true"
        log "  Enabled: $p"
    }
}
$content | Set-Content $godotProj -NoNewline
log "Godot plugins enabled!"

# ==== PART 4: Install Godot physics addons into project ====
log ""
log "=== PART 4: Install Godot physics addons ==="
$godotAddons = "D:\rj\KF\JM\GodotProject\addons"

# Rapier
if (Test-Path "$base\Godot-physics\godot-rapier-physics\addons") {
    robocopy "$base\Godot-physics\godot-rapier-physics\addons" "$godotAddons\godot-rapier-physics" /E /NFL /NDL /NJH /NJS
    log "Godot Rapier Physics installed to project!"
}

# ==== PART 5: Final summary ====
log ""
log "============================================"
log "  MEGA SETUP COMPLETE"
log "============================================"
$total = (Get-ChildItem $base -Recurse -Depth 1 | Where-Object { $_.PSIsContainer -and (Test-Path "$($_.FullName)\.git") }).Count
$size = [math]::Round((Get-ChildItem $base -Recurse -EA 0 | Measure-Object Length -Sum).Sum / 1GB, 2)
log "Total open-source repos: $total"
log "Total size: $size GB"
log "============================================"
log ""
log "NEWLY ADDED:"
log "  ComfyUI: CHORD (Ubisoft PBR) + TextureAlchemy (38 nodes) + NVIDIA GenAI Toolkit"
log "  Audio: MusicGen (Meta) + Stable Audio Tools + Rag-MusicPrompt"
log "  Godot: Rapier Physics (Fluids!) + QuarkPhysics (SoftBody)"
log "  Blender: TMG Action Jackson (Retarget)"
log "  Resources: Awesome CC0 + GameDev Resources list"
log "  Godot Project: All plugins enabled + new physics addons"
log ""
log "FREE ASSET WEBSITES (documented):"
log "  Polyhaven (CC0 textures/HDRI/models)"
log "  Kenney.nl (fully free assets)"
log "  OpenGameArt.org"
log "  opensource3dassets.com (991+ GLB)"
log "  itch.io (free game asset packs)"
log "============================================"
