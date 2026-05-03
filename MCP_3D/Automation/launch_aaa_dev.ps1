# ============================================================
# AAA 开发环境 - 一键启动所有服务
# 启动 Blender + ComfyUI + Godot + 所有MCP服务器
# ============================================================

param(
    [switch]$BlenderOnly,
    [switch]$ComfyUIOnly,
    [switch]$GodotOnly,
    [string]$GodotProject = "d:\开发\AAA_Game_Project"
)

$BlenderExe = "D:\rj\Games\FragmentRecovery\BlenderLatest\blender-4.4.0-windows-x64\blender.exe"
$ComfyUIDir = "D:\rj\AI\ComfyUI"
$GodotExe = "D:\rj\KF\JM\Godot_v4.6.1-stable_win64.exe"
$PythonExe = "C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       AAA 开发环境 - 一键启动                        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$LaunchAll = -not ($BlenderOnly -or $ComfyUIOnly -or $GodotOnly)

function Launch-App($Name, $Exe, $Args, $WorkDir) {
    Write-Host "  启动 $Name..." -ForegroundColor Yellow
    try {
        if ($WorkDir) {
            Start-Process -FilePath $Exe -ArgumentList $Args -WorkingDirectory $WorkDir -WindowStyle Normal
        } else {
            Start-Process -FilePath $Exe -ArgumentList $Args -WindowStyle Normal
        }
        Write-Host "    ✓ $Name 已启动" -ForegroundColor Green
    } catch {
        Write-Host "    ✗ $Name 启动失败: $_" -ForegroundColor Red
    }
}

# Blender
if ($LaunchAll -or $BlenderOnly) {
    if (Test-Path $BlenderExe) {
        Launch-App "Blender 4.4" $BlenderExe "" ""
        Start-Sleep -Seconds 3
    } else {
        Write-Host "  ⚠ Blender 未找到: $BlenderExe" -ForegroundColor DarkYellow
    }
}

# ComfyUI
if ($LaunchAll -or $ComfyUIOnly) {
    if (Test-Path "$ComfyUIDir\main.py") {
        $ComfyCmd = "python main.py --listen 127.0.0.1 --port 8188"
        Write-Host "  启动 ComfyUI (后台)..." -ForegroundColor Yellow
        Start-Process -FilePath $PythonExe -ArgumentList "main.py", "--listen", "127.0.0.1", "--port", "8188" -WorkingDirectory $ComfyUIDir -WindowStyle Minimized
        Write-Host "    ✓ ComfyUI 已启动 (http://127.0.0.1:8188)" -ForegroundColor Green
        Write-Host "    ⏳ 等待 ComfyUI 加载..." -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ ComfyUI 未找到: $ComfyUIDir" -ForegroundColor DarkYellow
    }
}

# Godot
if ($LaunchAll -or $GodotOnly) {
    if (Test-Path $GodotExe) {
        $GodotArgs = @()
        if ($GodotProject -and (Test-Path "$GodotProject\project.godot")) {
            $GodotArgs = @("--path", $GodotProject, "--editor")
        }
        Launch-App "Godot 4.6.1" $GodotExe $GodotArgs ""
    } else {
        Write-Host "  ⚠ Godot 未找到: $GodotExe" -ForegroundColor DarkYellow
    }
}

Write-Host ""
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  启动完成！" -ForegroundColor Green
Write-Host ""
Write-Host "  运行中的服务:" -ForegroundColor White
if ($LaunchAll -or $BlenderOnly) { Write-Host "  • Blender 4.4 - 3D建模/材质/动画" -ForegroundColor Gray }
if ($LaunchAll -or $ComfyUIOnly) { Write-Host "  • ComfyUI - AI图像生成 (http://127.0.0.1:8188)" -ForegroundColor Gray }
if ($LaunchAll -or $GodotOnly) { Write-Host "  • Godot 4.6.1 - 游戏引擎" -ForegroundColor Gray }
Write-Host ""
Write-Host "  MCP 服务器由 Trae IDE 自动管理，无需手动启动" -ForegroundColor DarkCyan
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Cyan
