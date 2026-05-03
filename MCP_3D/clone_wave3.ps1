# 第三波：Material Maker, T3D GN Presets, Niagara Destruction, 纹理生成等
$base = "\MCP_3D"
$log = "$base\clone_wave3_log.txt"
function log($m) { $t = Get-Date -Format "HH:mm:ss"; Write-Host "[$t] $m"; Add-Content $log "[$t] $m" }

New-Item -ItemType Directory -Path "$base\Godot-texture","$base\Blender-geometry" -Force | Out-Null

$repos = @(
    # Godot PBR/纹理
    @{url="https://github.com/RodZill4/material-maker.git"; path="$base\Godot-texture\material-maker"; name="Material Maker (PBR)"},
    @{url="https://github.com/Scaryrocker8/godot-easy-pbr.git"; path="$base\Godot-texture\godot-easy-pbr"; name="GodotEasyPBR"},
    
    # Blender Geometry Nodes
    @{url="https://github.com/Tams3d/T3D-GN-Presets.git"; path="$base\Blender-geometry\T3D-GN-Presets"; name="T3D GN Presets (free)"},
    @{url="https://github.com/cgvirus/blender-geometry-nodes-collection.git"; path="$base\Blender-geometry\blender-geometry-nodes"; name="Blender GN Collection"},
    
    # UE5 破坏/Niagara
    @{url="https://github.com/eanticev/niagara-destruction-driver.git"; path="$base\UE5-tools\niagara-destruction-driver"; name="Niagara Destruction Driver (MIT)"},
    
    # AI/ML 辅助
    @{url="https://github.com/hi-godot/godot-ai.git"; path="$base\Godot\godot-ai-higodot"; name="Godot AI (hi-godot) - 已有更新"}
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

log "=== Wave 3 complete ==="
