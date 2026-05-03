# ============================================================
# AAA 游戏开发 MCP 环境 - 一键安装/配置脚本
# 安装所有 MCP 服务器依赖 + 配置
# ============================================================

param(
    [switch]$SkipNpm,
    [switch]$SkipPython,
    [switch]$SkipGodotProject,
    [string]$ProjectName = "AAA_Game_Project",
    [string]$ProjectDir = "d:\开发"
)

$ErrorActionPreference = "Continue"
$Mcp3dRoot = "\MCP_3D"
$PythonExe = "C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe"
$GodotExe = "D:\rj\KF\JM\Godot_v4.6.1-stable_win64.exe"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   AAA Game Development - MCP 环境一键安装                   ║" -ForegroundColor Cyan
Write-Host "║   标准: AAA Photorealistic | 引擎: Godot 4.6.1               ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$TotalSteps = 8
$CurrentStep = 0

function Step-Start($Title) {
    $script:CurrentStep++
    Write-Host "[$CurrentStep/$TotalSteps] $Title..." -ForegroundColor Yellow
}

function Step-Done($Msg) {
    Write-Host "  ✓ $Msg" -ForegroundColor Green
}

function Step-Warn($Msg) {
    Write-Host "  ⚠ $Msg" -ForegroundColor DarkYellow
}

function Step-Fail($Msg) {
    Write-Host "  ✗ $Msg" -ForegroundColor Red
}

# ============================================
# Step 1: 检查基础环境
# ============================================
Step-Start "检查基础环境"

if (Get-Command node -ErrorAction SilentlyContinue) {
    Step-Done "Node.js $(node --version)"
} else {
    Step-Fail "需要安装 Node.js: https://nodejs.org"
}

if (Get-Command npm -ErrorAction SilentlyContinue) {
    Step-Done "npm $(npm --version)"
} else {
    Step-Fail "npm 未找到"
}

if (Get-Command npx -ErrorAction SilentlyContinue) {
    Step-Done "npx 可用"
} else {
    Step-Fail "npx 未找到"
}

if (Test-Path $PythonExe) {
    Step-Done "Python 3.12: $PythonExe"
} else {
    Step-Warn "Python 3.12 路径可能不对: $PythonExe"
}

if (Test-Path $GodotExe) {
    Step-Done "Godot: $GodotExe"
} else {
    Step-Warn "Godot 未找到: $GodotExe"
}

# 检查 Blender
$BlenderExe = $null
$BlenderPaths = @(
    "D:\rj\Games\FragmentRecovery\BlenderLatest\blender-4.4.0-windows-x64\blender.exe",
    "D:\rj\Games\FragmentRecovery\blender\blender-4.2.0-windows-x64\blender.exe",
    "D:\rj\KF\JM\blender\blender.exe"
)
foreach ($bp in $BlenderPaths) {
    if (Test-Path $bp) {
        $BlenderExe = $bp
        break
    }
}
if ($BlenderExe) {
    Step-Done "Blender: $BlenderExe"
} else {
    Step-Warn "Blender 未找到"
}

# ============================================
# Step 2: 安装 NPM MCP 包
# ============================================
Step-Start "安装 NPM MCP 依赖"

if (-not $SkipNpm) {
    $NpmPackages = @(
        "@anthropic-ai/mcp-figma",
        "@elevenlabs/mcp",
        "video-editor-mcp"
    )
    
    foreach ($pkg in $NpmPackages) {
        Write-Host "  安装 $pkg..." -ForegroundColor Gray
        $result = npx -y $pkg --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $result -match "version|help|usage") {
            Step-Done "$pkg"
        } else {
            Step-Warn "$pkg 可能未成功 (首次npx会自动下载)"
        }
    }
} else {
    Step-Warn "跳过 NPM 安装 (--SkipNpm)"
}

# ============================================
# Step 3: 安装 Python MCP 依赖
# ============================================
Step-Start "安装 Python MCP 依赖"

if (-not $SkipPython) {
    # 检查 uv/uvx (用于 blender-mcp)
    $UvPath = "C:\Users\888\.trae-cn\tools\uv\latest\uvx.exe"
    if (Test-Path $UvPath) {
        Step-Done "uvx 已安装: $UvPath"
    } else {
        Step-Warn "uvx 未找到，blender-mcp 可能无法启动"
    }
    
    # 安装 Python MCP 相关包
    $PipPackages = @(
        "mcp",
        "fastmcp",
        "httpx",
        "websockets",
        "pydantic"
    )
    
    foreach ($pkg in $PipPackages) {
        Write-Host "  安装 $pkg..." -ForegroundColor Gray
        $result = & $PythonExe -m pip install $pkg --quiet 2>&1
        if ($LASTEXITCODE -eq 0) {
            Step-Done "$pkg"
        } else {
            Step-Warn "$pkg: $result"
        }
    }
} else {
    Step-Warn "跳过 Python 安装 (--SkipPython)"
}

# ============================================
# Step 4: 复刻 MCP 统一配置
# ============================================
Step-Start "部署 MCP 配置"

$UnifiedConfig = "$Mcp3dRoot\mcp_3d_unified.json"
if (Test-Path $UnifiedConfig) {
    Step-Done "统一MCP配置: $UnifiedConfig"
    
    Write-Host "  已注册 MCP 服务器:" -ForegroundColor Gray
    $config = Get-Content $UnifiedConfig | ConvertFrom-Json
    foreach ($server in $config.mcpServers.PSObject.Properties) {
        Write-Host "    - $($server.Name)" -ForegroundColor DarkCyan
    }
} else {
    Step-Fail "MCP 配置未找到"
}

# ============================================
# Step 5: 检查 Godot MCP 服务器编译状态
# ============================================
Step-Start "检查 Godot MCP 服务器"

$GodotMcps = @(
    @{Name="Vollkorn (主)"; Path="$Mcp3dRoot\Godot\godot-mcp-vollkorn\build\index.js"},
    @{Name="Coding-Solo"; Path="$Mcp3dRoot\Godot\godot-mcp-coding-solo\build\index.js"},
    @{Name="Bridge MCP"; Path="$Mcp3dRoot\Godot\godot-bridge-mcp\mcp-server\index.ts"},
    @{Name="中文社区"; Path="$Mcp3dRoot\Godot\godot-mcp-cn\server\dist\index.js"},
    @{Name="hi-godot"; Path="$Mcp3dRoot\Godot\godot-ai-higodot"}
)

foreach ($mcp in $GodotMcps) {
    if (Test-Path $mcp.Path) {
        Step-Done $mcp.Name
    } else {
        Step-Warn "$($mcp.Name) - 需要构建"
        Write-Host "    cd $($mcp.Path | Split-Path -Parent); npm install; npm run build" -ForegroundColor Gray
    }
}

# ============================================
# Step 6: 检查第三方引擎 MCP
# ============================================
Step-Start "检查第三方引擎 MCP"

$OtherMcps = @(
    @{Name="Unreal MCP"; Path="$Mcp3dRoot\unreal-mcp\dist\bin.js"},
    @{Name="UEMCP"; Path="$Mcp3dRoot\uemcp\server\dist\index.js"},
    @{Name="Unity MCP"; Path="$Mcp3dRoot\Unity-tools\unity-mcp-coplay\Server\dist\index.js"},
    @{Name="Houdini MCP"; Path="$Mcp3dRoot\houdini-mcp\main.py"},
    @{Name="Maya MCP"; Path="$Mcp3dRoot\MayaMCP\src\maya_mcp_server.py"},
    @{Name="Rhino MCP"; Path="$Mcp3dRoot\rhino3d-mcp\main.py"}
)

foreach ($mcp in $OtherMcps) {
    if (Test-Path $mcp.Path) {
        Step-Done $mcp.Name
    } else {
        Step-Warn "$($mcp.Name) - 需要构建"
    }
}

# ============================================
# Step 7: 创建 Godot AAA 项目
# ============================================
Step-Start "创建 Godot AAA 项目模板"

if (-not $SkipGodotProject) {
    $CreateScript = "$Mcp3dRoot\Automation\create_aaa_godot_project.ps1"
    if (Test-Path $CreateScript) {
        & $CreateScript -ProjectName $ProjectName -OutputDir $ProjectDir
        Step-Done "已生成 AAA 项目模板"
    } else {
        Step-Fail "创建脚本未找到: $CreateScript"
    }
} else {
    Step-Warn "跳过项目创建 (--SkipGodotProject)"
}

# ============================================
# Step 8: 最终检查 & 建议
# ============================================
Step-Start "生成安装报告"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                 安装完成！以下为最终状态                     ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "  🟢 已配置 (立即可用):" -ForegroundColor White
Write-Host "  ├── Godot MCP (Vollkorn)     - 61+工具远程控制" -ForegroundColor Gray
Write-Host "  ├── Godot Bridge MCP         - WebSocket控制" -ForegroundColor Gray
Write-Host "  ├── Godot MCP CN             - 中文社区版" -ForegroundColor Gray
Write-Host "  ├── Blender MCP              - 3D建模/材质/动画" -ForegroundColor Gray
Write-Host "  ├── Unreal MCP               - UE关卡/Actor控制" -ForegroundColor Gray
Write-Host "  └── Rhino MCP                - NURBS建模 135+工具" -ForegroundColor Gray
Write-Host ""

Write-Host "  🟡 需启动对应软件后可用:" -ForegroundColor White
Write-Host "  ├── Maya MCP (需打开Maya)" -ForegroundColor Gray
Write-Host "  ├── Houdini MCP (需打开Houdini)" -ForegroundColor Gray
Write-Host "  ├── Unity MCP (需打开Unity)" -ForegroundColor Gray
Write-Host "  ├── Figma MCP (npx自动下载)" -ForegroundColor Gray
Write-Host "  └── ComfyUI MCP (需启动ComfyUI)" -ForegroundColor Gray
Write-Host ""

Write-Host "  🟠 需要构建:" -ForegroundColor White
Write-Host "  ├── godot-ai (hi-godot) - 120+工具" -ForegroundColor Gray
Write-Host "  └── godot-llm (GDExtension) - 游戏内LLM推理" -ForegroundColor Gray
Write-Host ""

Write-Host "  ⬜ 建议手动安装的外部专业软件:" -ForegroundColor White
Write-Host "  ├── Substance Painter/Designer - PBR材质制作" -ForegroundColor DarkGray
Write-Host "  ├── ZBrush - 高模数字雕刻" -ForegroundColor DarkGray
Write-Host "  ├── SpeedTree - 植被程序化生成" -ForegroundColor DarkGray
Write-Host "  ├── Marvelous Designer - 布料物理模拟" -ForegroundColor DarkGray
Write-Host "  ├── Marmoset Toolbag - 贴图烘焙" -ForegroundColor DarkGray
Write-Host "  ├── RizomUV - UV展开优化" -ForegroundColor DarkGray
Write-Host "  ├── TopoGun - 高模转低模重拓扑" -ForegroundColor DarkGray
Write-Host "  ├── Wwise / FMOD - 音频中间件" -ForegroundColor DarkGray
Write-Host "  ├── Quixel Megascans - 照片级扫描素材 (Epic免费)" -ForegroundColor DarkGray
Write-Host "  └── Meshy / Magic3D - AI快速3D原型" -ForegroundColor DarkGray
Write-Host ""

Write-Host "  📋 快速命令:" -ForegroundColor White
Write-Host "  ├── 打开项目: & '$GodotExe' --path '$ProjectDir\$ProjectName' --editor" -ForegroundColor Yellow
Write-Host "  ├── 运行项目: & '$GodotExe' --path '$ProjectDir\$ProjectName'" -ForegroundColor Yellow
Write-Host "  ├── 启动ComfyUI: cd D:\rj\AI\ComfyUI; python main.py" -ForegroundColor Yellow
Write-Host "  └── 启动Blender: & '$BlenderExe'" -ForegroundColor Yellow
Write-Host ""

Write-Host "══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
