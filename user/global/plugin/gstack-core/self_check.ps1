$root = "\python"
$status = @()

# 1. MCP directory check
$mcpDirs = @("JM", "BC", "Tools")
foreach ($d in $mcpDirs) {
    $dirPath = "$root\MCP\$d"
    if (Test-Path $dirPath) {
        $count = (Get-ChildItem $dirPath -File -Filter "*.py" -Recurse -ErrorAction SilentlyContinue).Count
        $status += "$d($count)"
    } else {
        $status += "$d(0)"
    }
}

# 2. Blender MCP connectivity test
try {
    $null = Invoke-WebRequest -Uri "http://localhost:8400" -TimeoutSec 1
    $status += "BlenderMCP:UP"
} catch {
    $status += "BlenderMCP:DOWN"
    # 自动拉起 Blender MCP
    Write-Host "⚠️ Blender MCP 离线，正在自动重启..." -ForegroundColor Yellow
    $blenderMcpDir = "$root\MCP\JM\blender_mcp"
    $blenderConfig = "$blenderMcpDir\config.json"
    $blenderPath = "C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
    
    if (Test-Path $blenderConfig) {
        $config = Get-Content $blenderConfig | ConvertFrom-Json
        if ($config.blender_path) {
            $blenderPath = $config.blender_path
        }
    }
    
    $serverScript = "$blenderMcpDir\src\server.py"
    if (Test-Path $serverScript) {
        Start-Process $blenderPath -ArgumentList "--python", "`"$serverScript`"" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        # 再次检查
        try {
            $null = Invoke-WebRequest -Uri "http://localhost:8400" -TimeoutSec 2
            $status[-1] = "BlenderMCP:UP (Auto-started)"
            Write-Host "✅ Blender MCP 已自动启动" -ForegroundColor Green
        } catch {
            Write-Host "❌ Blender MCP 启动失败" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Blender MCP 服务器脚本不存在" -ForegroundColor Red
    }
}

# 3. CC cache check
$ccPath = "$root\CC\3_Unused"
if (Test-Path $ccPath) {
    $unusedCount = (Get-ChildItem $ccPath -File -Recurse -ErrorAction SilentlyContinue).Count
    if ($unusedCount -gt 20) {
        $status += "UnusedFiles:$unusedCount"
    } else {
        $status += "CC:OK"
    }
} else {
    $status += "CC:OK"
}

# 4. Last error check
$errorFile = "$root\logs\last_error.txt"
if (Test-Path $errorFile) {
    $lastErr = (Get-Content $errorFile -Raw).Trim()
    if ($lastErr) {
        $status += "Error:$lastErr"
    }
}

# 5. Skills count
$skillsPath = "$root\MCP_Core\skills"
if (Test-Path $skillsPath) {
    $skillCount = (Get-ChildItem $skillsPath -Directory -ErrorAction SilentlyContinue).Count
    $status += "Skills:$skillCount"
} else {
    $status += "Skills:0"
}

# 6. n8n workflow automation check
try {
    $null = Invoke-WebRequest -Uri "http://localhost:5678" -TimeoutSec 1
    $status += "n8n:UP"
} catch {
    $status += "n8n:DOWN"
    # 自动拉起 n8n
    Write-Host "⚠️ n8n 离线，正在自动启动..." -ForegroundColor Yellow
    $n8nDir = "$root\MCP\Tools\n8n"
    $composeFile = "$n8nDir\docker-compose.yml"
    
    if (Test-Path $composeFile) {
        # 检查 Docker 是否已安装
        try {
            $dockerVersion = docker --version
            if ($dockerVersion) {
                Set-Location $n8nDir
                docker-compose up -d
                Start-Sleep -Seconds 5
                # 再次检查
                try {
                    $null = Invoke-WebRequest -Uri "http://localhost:5678" -TimeoutSec 3
                    $status[-1] = "n8n:UP (Auto-started)"
                    Write-Host "✅ n8n 已自动启动" -ForegroundColor Green
                } catch {
                    Write-Host "❌ n8n 启动失败" -ForegroundColor Red
                }
            } else {
                Write-Host "❌ Docker 未安装" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Docker 未安装或不可用" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ n8n docker-compose.yml 不存在" -ForegroundColor Red
    }
}

# Output status bar
$statusBar = "GSTACK Status: $($status -join " | ")"
Write-Host $statusBar -ForegroundColor Cyan
$statusBar | Set-Clipboard

# Ensure directories exist
if (!(Test-Path "$root\logs")) {
    New-Item -ItemType Directory -Path "$root\logs" -Force | Out-Null
}
if (!(Test-Path "$root\.trae")) {
    New-Item -ItemType Directory -Path "$root\.trae" -Force | Out-Null
}

Write-Host "✅ Status bar copied to clipboard - paste to AI when needed" -ForegroundColor Green
