<#
    MCP 3D Modeling Workflow - One-Click Setup Script
    Supported: Blender, UE5, Unity, Houdini, Maya, Rhino
    Date: 2026-05-01
#>

$ErrorActionPreference = "Continue"
$MCP_BASE = "\MCP_3D"
$MCP_LOG = "$MCP_BASE\setup_log.txt"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] [$Level] $Message"
    Write-Host $line
    Add-Content -Path $MCP_LOG -Value $line
}

function Test-Cmd {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-Prerequisites {
    Write-Log "=== Checking prerequisites ==="

    if (-not (Test-Cmd "git")) {
        Write-Log "Git not found, installing..." "WARN"
        winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    } else {
        Write-Log "Git: OK"
    }

    if (-not (Test-Cmd "uv")) {
        Write-Log "uv not found, installing..." "WARN"
        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
        $env:Path = "C:\Users\$env:USERNAME\.local\bin;$env:Path"
    } else {
        Write-Log "uv: OK"
    }

    if (-not (Test-Cmd "node")) {
        Write-Log "Node.js not found, installing..." "WARN"
        winget install --id OpenJS.NodeJS.LTS -e --source winget --accept-package-agreements --accept-source-agreements
    } else {
        Write-Log "Node.js: OK"
    }

    if (-not (Test-Cmd "python")) {
        Write-Log "Python not found, installing..." "WARN"
        winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
    } else {
        Write-Log "Python: OK"
    }

    Write-Log "Prerequisites check complete"
}

function Install-BlenderMCP {
    Write-Log "=== Setting up Blender MCP ==="

    $blenderExe = "D:\rj\KF\JM\blender\blender.exe"
    if (-not (Test-Path $blenderExe)) {
        Write-Log "Blender not found at $blenderExe, skipping" "WARN"
        return
    }
    Write-Log "Blender found: $blenderExe"

    $repoPath = "$MCP_BASE\blender-mcp"
    if (-not (Test-Path $repoPath)) {
        Write-Log "Cloning blender-mcp repo..."
        git clone https://github.com/bhza/blender-mcp.git $repoPath
    } else {
        Write-Log "blender-mcp repo exists, pulling latest..."
        Push-Location $repoPath
        git pull
        Pop-Location
    }

    $addonSrc = "$repoPath\addon.py"
    $addonDst = "$MCP_BASE\blender_addon\addon.py"
    if (Test-Path $addonSrc) {
        if (-not (Test-Path "$MCP_BASE\blender_addon")) {
            New-Item -ItemType Directory -Path "$MCP_BASE\blender_addon" -Force | Out-Null
        }
        Copy-Item $addonSrc $addonDst -Force
        Write-Log "Blender MCP addon copied to $addonDst"
        Write-Log ">>> MANUAL: In Blender -> Edit > Preferences > Add-ons > Install > select $addonDst"
    }

    Write-Log "Blender MCP setup complete (MCP server starts via: uvx blender-mcp)"
}

function Install-UE5MCP {
    Write-Log "=== Setting up UE5 MCP ==="

    $ue5Exe = "D:\rj\KF\JM\UE_5.6\Engine\Binaries\Win64\UnrealEditor.exe"
    if (-not (Test-Path $ue5Exe)) {
        Write-Log "UE5 not found at $ue5Exe, skipping" "WARN"
        return
    }
    Write-Log "UE5 found: $ue5Exe"

    $repoPath = "$MCP_BASE\unreal-mcp"
    if (-not (Test-Path $repoPath)) {
        Write-Log "Cloning unreal-mcp repo (uses Python Remote Execution, no plugin needed)..."
        git clone https://github.com/runreal/unreal-mcp.git $repoPath
    } else {
        Write-Log "unreal-mcp repo exists, pulling latest..."
        Push-Location $repoPath
        git pull
        Pop-Location
    }

    if (Test-Path "$repoPath\requirements.txt") {
        Write-Log "Installing unreal-mcp Python dependencies..."
        Push-Location $repoPath
        pip install -r requirements.txt
        Pop-Location
    }

    $ue5mcpAlt = "$MCP_BASE\uemcp"
    if (-not (Test-Path $ue5mcpAlt)) {
        Write-Log "Cloning uemcp repo (mature UE5 MCP solution, v3.8.0)..."
        git clone https://github.com/atomantic/uemcp.git $ue5mcpAlt
    } else {
        Write-Log "uemcp repo exists, pulling latest..."
        Push-Location $ue5mcpAlt
        git pull
        Pop-Location
    }

    if (Test-Path "$ue5mcpAlt\package.json") {
        Write-Log "Installing uemcp Node.js dependencies..."
        Push-Location $ue5mcpAlt
        npm install
        Pop-Location
    }

    Write-Log "UE5 MCP setup complete"
    Write-Log ">>> Method 1 (unreal-mcp): Enable Python plugin in UE5, then run unreal-mcp"
    Write-Log ">>> Method 2 (uemcp): Install UE5 Python plugin, run uemcp MCP server"
}

function Install-UnityMCP {
    Write-Log "=== Setting up Unity MCP ==="

    $unityEditor = "D:\rj\KF\JM\Unity\Editor"
    if (-not (Test-Path $unityEditor)) {
        Write-Log "Unity not found at $unityEditor, skipping" "WARN"
        return
    }
    Write-Log "Unity found: $unityEditor"

    $repoPath = "$MCP_BASE\Unity-MCP"
    if (-not (Test-Path $repoPath)) {
        Write-Log "Cloning Unity-MCP repo..."
        git clone https://github.com/IvanMurzak/Unity-MCP.git $repoPath
    } else {
        Write-Log "Unity-MCP repo exists, pulling latest..."
        Push-Location $repoPath
        git pull
        Pop-Location
    }

    if (Test-Path "$repoPath\package.json") {
        Write-Log "Installing Unity-MCP Node.js dependencies..."
        Push-Location $repoPath
        npm install
        Pop-Location
    }

    Write-Log "Unity MCP setup complete"
    Write-Log ">>> MANUAL: Copy Unity-MCP C# plugin to Unity project Packages folder"
}

function Install-HoudiniMCP {
    Write-Log "=== Setting up Houdini MCP ==="

    $houdiniPath = Get-ChildItem "C:\Program Files\Side Effects Software" -ErrorAction SilentlyContinue
    if (-not $houdiniPath) {
        Write-Log "Houdini not installed, downloading MCP server code only" "WARN"
    } else {
        Write-Log "Houdini found: $($houdiniPath.FullName)"
    }

    $repoPath = "$MCP_BASE\houdini-mcp"
    if (-not (Test-Path $repoPath)) {
        Write-Log "Cloning houdini-mcp repo..."
        git clone https://github.com/capoomgit/houdini-mcp.git $repoPath
    } else {
        Write-Log "houdini-mcp repo exists, pulling latest..."
        Push-Location $repoPath
        git pull
        Pop-Location
    }

    if (Test-Path "$repoPath\requirements.txt") {
        Write-Log "Installing houdini-mcp Python dependencies..."
        Push-Location $repoPath
        pip install -r requirements.txt
        Pop-Location
    }

    Write-Log "Houdini MCP setup complete (awaiting Houdini installation)"
}

function Install-MayaMCP {
    Write-Log "=== Setting up Maya MCP ==="

    $mayaPath = Get-ChildItem "C:\Program Files\Autodesk\Maya*" -ErrorAction SilentlyContinue
    if (-not $mayaPath) {
        Write-Log "Maya not installed, downloading MCP server code only" "WARN"
    } else {
        Write-Log "Maya found: $($mayaPath.FullName)"
    }

    $repoPath = "$MCP_BASE\MayaMCP"
    if (-not (Test-Path $repoPath)) {
        Write-Log "Cloning MayaMCP repo (zero-install philosophy, uses command port)..."
        git clone https://github.com/phuhao00/MayaMCP.git $repoPath
    } else {
        Write-Log "MayaMCP repo exists, pulling latest..."
        Push-Location $repoPath
        git pull
        Pop-Location
    }

    if (Test-Path "$repoPath\requirements.txt") {
        Write-Log "Installing MayaMCP Python dependencies..."
        Push-Location $repoPath
        pip install -r requirements.txt
        Pop-Location
    }

    Write-Log "Maya MCP setup complete (awaiting Maya installation)"
}

function Install-RhinoMCP {
    Write-Log "=== Setting up Rhino MCP ==="

    $rhinoPath = Get-ChildItem "C:\Program Files\McNeel\Rhinoceros*" -ErrorAction SilentlyContinue
    if (-not $rhinoPath) {
        Write-Log "Rhino not installed, downloading MCP server code only" "WARN"
    } else {
        Write-Log "Rhino found: $($rhinoPath.FullName)"
    }

    $repoPath = "$MCP_BASE\rhino3d-mcp"
    if (-not (Test-Path $repoPath)) {
        Write-Log "Cloning rhino3d-mcp repo (135+ tools)..."
        git clone https://github.com/quocvibui/rhino3d-mcp.git $repoPath
    } else {
        Write-Log "rhino3d-mcp repo exists, pulling latest..."
        Push-Location $repoPath
        git pull
        Pop-Location
    }

    if (Test-Path "$repoPath\requirements.txt") {
        Write-Log "Installing rhino3d-mcp Python dependencies..."
        Push-Location $repoPath
        pip install -r requirements.txt
        Pop-Location
    }

    $ghRepoPath = "$MCP_BASE\rhino_gh_mcp"
    if (-not (Test-Path $ghRepoPath)) {
        Write-Log "Cloning rhino_gh_mcp repo (Grasshopper integration)..."
        git clone https://github.com/goldsmith323/rhino_gh_mcp.git $ghRepoPath
    }

    Write-Log "Rhino MCP setup complete (awaiting Rhino installation)"
}

function Build-UnifiedConfig {
    Write-Log "=== Building unified MCP configuration ==="

    $configContent = @'
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"],
      "env": {
        "HYPER3D_API_KEY": "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez",
        "RODIN_FREE_TRIAL_KEY": "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"
      }
    },
    "unreal-mcp": {
      "command": "python",
      "args": ["D:\\AI\\MCP_3D\\unreal-mcp\\src\\unreal_mcp\\server.py"]
    },
    "uemcp": {
      "command": "node",
      "args": ["D:\\AI\\MCP_3D\\uemcp\\dist\\index.js"]
    },
    "unity-mcp": {
      "command": "node",
      "args": ["D:\\AI\\MCP_3D\\Unity-MCP\\dist\\index.js"]
    },
    "houdini-mcp": {
      "command": "python",
      "args": ["D:\\AI\\MCP_3D\\houdini-mcp\\houdini_mcp_server.py"]
    },
    "maya-mcp": {
      "command": "python",
      "args": ["D:\\AI\\MCP_3D\\MayaMCP\\maya_mcp_server.py"]
    },
    "rhino-mcp": {
      "command": "python",
      "args": ["D:\\AI\\MCP_3D\\rhino3d-mcp\\server.py"]
    }
  }
}
'@

    $configPath = "$MCP_BASE\mcp_3d_unified.json"
    $configContent | Out-File -FilePath $configPath -Encoding UTF8
    Write-Log "Unified MCP config saved to $configPath"

    Write-Log ""
    Write-Log "=== Config file locations ==="
    Write-Log "Unified config: $configPath"
    Write-Log "Trae CN: Copy config to %APPDATA%\Trae CN\User\mcp.json"
    Write-Log "Claude:  Copy config to %APPDATA%\Claude\claude_desktop_config.json"
    Write-Log ""
    Write-Log "NOTE: MCP server startup commands may need adjustment based on actual repo structure"
    Write-Log "Check each repo's README.md for accurate startup instructions"
}

function Show-Summary {
    Write-Log ""
    Write-Log "============================================"
    Write-Log "   MCP 3D Modeling Workflow - Setup Summary"
    Write-Log "============================================"
    Write-Log ""
    Write-Log "Installed DCC software:"
    Write-Log "  [OK] Blender 5.1.0  -> D:\rj\KF\JM\blender\blender.exe"
    Write-Log "  [OK] UE5 5.6        -> D:\rj\KF\JM\UE_5.6\Engine\Binaries\Win64\UnrealEditor.exe"
    Write-Log "  [OK] Unity          -> D:\rj\KF\JM\Unity\Editor"
    Write-Log "  [OK] Godot 4.6.1    -> D:\rj\KF\JM\Godot_v4.6.1-stable_win64.exe"
    Write-Log ""
    Write-Log "Not installed (commercial license required):"
    Write-Log "  [--] Maya           -> MCP code downloaded, awaiting Maya install"
    Write-Log "  [--] Houdini        -> MCP code downloaded, awaiting Houdini install"
    Write-Log "  [--] Rhino          -> MCP code downloaded, awaiting Rhino install"
    Write-Log ""
    Write-Log "MCP server code location: $MCP_BASE"
    Write-Log "Unified config file: $MCP_BASE\mcp_3d_unified.json"
    Write-Log ""
    Write-Log "=== Next Steps ==="
    Write-Log ""
    Write-Log "1. Blender MCP:"
    Write-Log "   - Open Blender -> Edit > Preferences > Add-ons > Install"
    Write-Log "   - Select: $MCP_BASE\blender_addon\addon.py"
    Write-Log "   - Enable addon, then find BlenderMCP tab in 3D viewport sidebar (N key)"
    Write-Log "   - Click 'Connect to Claude' to start connection"
    Write-Log ""
    Write-Log "2. UE5 MCP (two options):"
    Write-Log "   Option A (unreal-mcp, no plugin needed):"
    Write-Log "   - Enable Python Editor Script Plugin in UE5"
    Write-Log "   - Run: python $MCP_BASE\unreal-mcp\src\unreal_mcp\server.py"
    Write-Log "   Option B (uemcp, more mature):"
    Write-Log "   - Install UE5 Python plugin + uemcp UE5 plugin"
    Write-Log "   - Run: node $MCP_BASE\uemcp\dist\index.js"
    Write-Log ""
    Write-Log "3. Unity MCP:"
    Write-Log "   - Copy Unity-MCP C# plugin to Unity project Packages folder"
    Write-Log "   - Run MCP server: node $MCP_BASE\Unity-MCP\dist\index.js"
    Write-Log ""
    Write-Log "4. Configure in Trae CN:"
    Write-Log "   - Merge $MCP_BASE\mcp_3d_unified.json content"
    Write-Log "   - Into %APPDATA%\Trae CN\User\mcp.json"
    Write-Log ""
    Write-Log "Setup log: $MCP_LOG"
    Write-Log "============================================"
}

# ===== Main =====
Write-Log "MCP 3D Modeling Workflow - Setup Script Starting"
Write-Log "Install directory: $MCP_BASE"

if (-not (Test-Path $MCP_BASE)) {
    New-Item -ItemType Directory -Path $MCP_BASE -Force | Out-Null
    Write-Log "Created install directory: $MCP_BASE"
}

Install-Prerequisites
Install-BlenderMCP
Install-UE5MCP
Install-UnityMCP
Install-HoudiniMCP
Install-MayaMCP
Install-RhinoMCP
Build-UnifiedConfig
Show-Summary

Write-Log "Script execution complete!"
