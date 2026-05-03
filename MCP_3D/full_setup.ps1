# 一键全部搞定：更新Trae CN MCP + 安装Godot插件 + 下载所有新工具
$ErrorActionPreference = "Continue"
$log = "\MCP_3D\setup_full_log.txt"
function log($m) { $t = Get-Date -Format "HH:mm:ss"; Write-Host "[$t] $m"; Add-Content $log "[$t] $m" }

log "=== STEP 1: Update Trae CN mcp.json ==="
$traeMcp = "$env:APPDATA\Trae CN\User\mcp.json"
$oldConfig = Get-Content $traeMcp -Raw | ConvertFrom-Json

# Our 3D MCP servers
$new3DServers = @{
    "godot-mcp" = @{
        command = "node"
        args = @("D:\\AI\\MCP_3D\\Godot\\godot-mcp-vollkorn\\build\\index.js")
        env = @{ GODOT_PATH = "D:\\rj\\KF\\JM\\Godot_v4.6.1-stable_win64.exe" }
    }
    "godot-bridge-mcp" = @{
        command = "npx"
        args = @("tsx", "D:\\AI\\MCP_3D\\Godot\\godot-bridge-mcp\\mcp-server\\index.ts")
    }
    "godot-mcp-cn" = @{
        command = "node"
        args = @("D:\\AI\\MCP_3D\\Godot\\godot-mcp-cn\\server\\dist\\index.js")
    }
    "blender-mcp" = @{
        command = "uvx"
        args = @("blender-mcp")
        env = @{
            HYPER3D_API_KEY = "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"
            RODIN_FREE_TRIAL_KEY = "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"
        }
    }
    "unreal-mcp" = @{
        command = "node"
        args = @("D:\\AI\\MCP_3D\\unreal-mcp\\dist\\bin.js")
    }
    "uemcp" = @{
        command = "node"
        args = @("D:\\AI\\MCP_3D\\uemcp\\server\\dist\\index.js")
    }
    "houdini-mcp" = @{
        command = "C:\\Users\\888\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
        args = @("D:\\AI\\MCP_3D\\houdini-mcp\\main.py")
    }
    "maya-mcp" = @{
        command = "C:\\Users\\888\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
        args = @("D:\\AI\\MCP_3D\\MayaMCP\\src\\maya_mcp_server.py")
    }
    "rhino-mcp" = @{
        command = "C:\\Users\\888\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
        args = @("D:\\AI\\MCP_3D\\rhino3d-mcp\\main.py")
    }
}

foreach ($key in $new3DServers.Keys) {
    $oldConfig.mcpServers | Add-Member -NotePropertyName $key -NotePropertyValue $new3DServers[$key] -Force
}
$oldConfig | ConvertTo-Json -Depth 10 | Out-File $traeMcp -Encoding UTF8
log "Trae CN mcp.json updated with 10 3D MCP servers!"

log ""
log "=== STEP 2: Install Godot addons to FragmentWeaponGame ==="
$godotProject = "D:\rj\KF\JM\GodotProject"

# Install Fuku (editor AI)
robocopy "\MCP_3D\Godot\addons\fuku" "$godotProject\addons\fuku" /E /NFL /NDL /NJH /NJS
log "  Fuku installed!"

# Install AI Context Generator
robocopy "\MCP_3D\Godot\tools\ai-context-generator" "$godotProject\addons\ai_context_generator" /E /NFL /NDL /NJH /NJS
log "  AI Context Generator installed!"

# Install VoronoiShatter as addon
if (Test-Path "\MCP_3D\Godot\tools\voronoishatter\addons") {
    robocopy "\MCP_3D\Godot\tools\voronoishatter\addons" "$godotProject\addons\voronoishatter" /E /NFL /NDL /NJH /NJS
    log "  VoronoiShatter installed!"
}

# Install vollkorn MCP scripts into project
$vollkornScripts = "\MCP_3D\Godot\godot-mcp-vollkorn\build\scripts"
if (Test-Path $vollkornScripts) {
    robocopy $vollkornScripts "$godotProject\addons\godot_mcp_vollkorn" /E /NFL /NDL /NJH /NJS
    log "  Vollkorn MCP scripts installed!"
}

# Install hi-godot/godot-ai plugin
if (Test-Path "\MCP_3D\Godot\godot-ai-higodot\plugin\addons\godot_ai") {
    robocopy "\MCP_3D\Godot\godot-ai-higodot\plugin\addons\godot_ai" "$godotProject\addons\godot_ai" /E /NFL /NDL /NJH /NJS
    log "  Godot AI (hi-godot) plugin installed!"
}

log "All Godot addons installed!"

log ""
log "=== STEP 3: Clone new discovered tools ==="
$newTools = @(
    @{url="https://github.com/VIKASKENDRE/blender-ai-builder.git"; path="\MCP_3D\blender-tools\blender-ai-builder"; name="Blender AI Builder"},
    @{url="https://github.com/mac999/blender-llm-addin.git"; path="\MCP_3D\blender-tools\blender-llm-addin"; name="Blender LLM Addin"},
    @{url="https://github.com/xamanjha/blenderAIAgent.git"; path="\MCP_3D\blender-tools\blenderAIAgent"; name="Blender AI Agent"},
    @{url="https://github.com/flopperam/unreal-engine-mcp.git"; path="\MCP_3D\UE5-tools\unreal-engine-mcp"; name="Unreal Engine MCP (flopperam)"},
    @{url="https://github.com/IvanMurzak/Unity-MCP.git"; path="\MCP_3D\Unity-MCP"; name="Unity MCP"},
    @{url="https://github.com/ayeletstudioindia/unreal-analyzer-mcp.git"; path="\MCP_3D\UE5-tools\unreal-analyzer-mcp"; name="Unreal Analyzer MCP"},
    @{url="https://github.com/VedantRGosavi/UE5-MCP.git"; path="\MCP_3D\UE5-tools\UE5-MCP-research"; name="UE5-MCP Research"},
    @{url="https://github.com/qwrtln/Homm3BG-soundtrack.git"; path="\MCP_3D\extra\homm3-soundtrack"; name="HoMM3 Soundtrack (free CC)"}
)

New-Item -ItemType Directory -Path "\MCP_3D\blender-tools","\MCP_3D\UE5-tools","\MCP_3D\extra" -Force | Out-Null

foreach ($t in $newTools) {
    if (Test-Path "$($t.path)\.git") {
        log "SKIP: $($t.name)"
        continue
    }
    log "CLONE: $($t.name)..."
    Remove-Item $t.path -Recurse -Force -ErrorAction SilentlyContinue
    git clone --depth 1 $t.url $t.path 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { log "OK: $($t.name)" }
    else { log "FAIL: $($t.name)" }
}

log ""
log "=== STEP 4: pip install blender-mcp-enhanced ==="
& "C:\Users\888\AppData\Local\Programs\Python\Python312\Scripts\pip.exe" install blender-mcp-enhanced -q 2>&1 | Out-Null
log "blender-mcp-enhanced installed!"

log ""
log "=== ALL DONE ==="
log "Trae CN + Godot project + new tools all configured!"
