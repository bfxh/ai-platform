<#
.SYNOPSIS
    AI MCP 服务管理脚本
    提供启动、停止、重启、状态查看、日志查看和更新等功能

.DESCRIPTION
    该脚本提供完整的 MCP 容器服务生命周期管理:
    - start:   启动所有或指定服务
    - stop:    停止所有或指定服务
    - restart: 重启所有或指定服务
    - status:  查看服务运行状态
    - logs:    查看服务日志
    - update:  更新服务镜像并重新部署
    - ps:      列出所有 MCP 容器
    - exec:    在指定容器中执行命令
    - cleanup: 清理未使用的镜像和卷

.PARAMETER Action
    要执行的操作: start, stop, restart, status, logs, update, ps, exec, cleanup

.PARAMETER Services
    指定要操作的服务名称，多个用逗号分隔。为空则操作所有服务

.PARAMETER Follow
    日志查看时持续跟踪新输出 (logs 操作)

.PARAMETER Lines
    日志查看时显示的行数 (logs 操作)，默认 100

.PARAMETER Command
    在容器中执行的命令 (exec 操作)

.EXAMPLE
    .\manage-services.ps1 start
    启动所有 MCP 服务

.EXAMPLE
    .\manage-services.ps1 start -Services blender-mcp,code-quality
    只启动 blender-mcp 和 code-quality 服务

.EXAMPLE
    .\manage-services.ps1 stop
    停止所有 MCP 服务

.EXAMPLE
    .\manage-services.ps1 status
    查看所有服务状态

.EXAMPLE
    .\manage-services.ps1 logs -Services blender-mcp -Follow -Lines 50
    跟踪 blender-mcp 服务的日志，显示最新 50 行

.EXAMPLE
    .\manage-services.ps1 update
    更新所有服务镜像并重新部署

.EXAMPLE
    .\manage-services.ps1 exec -Services blender-mcp -Command "python -c 'print(1+1)'"
    在 blender-mcp 容器中执行命令
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "update", "ps", "exec", "cleanup")]
    [string]$Action,

    [string[]]$Services = @(),
    [switch]$Follow,
    [int]$Lines = 100,
    [string]$Command = "",
    [switch]$Force
)

# =============================================================================
# 配置
# =============================================================================
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$ComposeFile = Join-Path $ScriptDir "docker-compose.yml"
$EnvFile = Join-Path $ScriptDir ".env"

# 服务定义 (与 docker-compose.yml 对应)
$AllServices = @(
    # JM 类
    @{ Name = "blender-mcp"; Display = "Blender MCP"; Category = "JM"; Port = 8001 },
    @{ Name = "unity-mcp"; Display = "Unity MCP"; Category = "JM"; Port = 8002 },
    @{ Name = "ue-mcp"; Display = "UE MCP"; Category = "JM"; Port = 8003 },
    @{ Name = "godot-mcp"; Display = "Godot MCP"; Category = "JM"; Port = 8004 },
    # BC 类
    @{ Name = "code-quality"; Display = "Code Quality"; Category = "BC"; Port = 8005 },
    @{ Name = "github-dl"; Display = "GitHub DL"; Category = "BC"; Port = 8006 },
    @{ Name = "vs-mgr"; Display = "VS Manager"; Category = "BC"; Port = 8007 },
    @{ Name = "dev-mgr"; Display = "Dev Manager"; Category = "BC"; Port = 8008 },
    # Tools 类
    @{ Name = "download-manager"; Display = "Download Manager"; Category = "Tools"; Port = 8009 },
    @{ Name = "network-optimizer"; Display = "Network Optimizer"; Category = "Tools"; Port = 8010 },
    @{ Name = "memory-monitor"; Display = "Memory Monitor"; Category = "Tools"; Port = 8011 },
    # 共享服务
    @{ Name = "n8n"; Display = "N8N Workflow"; Category = "Shared"; Port = 5678 }
)

# =============================================================================
# 辅助函数
# =============================================================================

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    $colors = @{
        "INFO" = "Cyan"; "SUCCESS" = "Green"; "WARN" = "Yellow";
        "ERROR" = "Red"; "DEBUG" = "Gray"; "WHITE" = "White"
    }
    $fgColor = if ($colors.ContainsKey($Color)) { $colors[$Color] } else { $Color }
    Write-Host $Message -ForegroundColor $fgColor
}

function Get-TargetServices {
    if ($Services.Count -eq 0) {
        return $AllServices
    }
    $serviceNames = $Services -split '[,;]'
    return $AllServices | Where-Object { $serviceNames -contains $_.Name }
}

function Test-ComposeFile {
    if (-not (Test-Path $ComposeFile)) {
        Write-ColorOutput "Docker Compose 文件不存在: $ComposeFile" "ERROR"
        exit 1
    }
}

function Test-DockerRunning {
    try {
        $info = docker info 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Invoke-DockerCompose {
    param([string]$ComposeAction, [string]$ServiceList = "")
    $cmdArgs = @("-f", $ComposeFile)
    if (Test-Path $EnvFile) {
        $cmdArgs += @("--env-file", $EnvFile)
    }
    $cmdArgs += $ComposeAction
    if ($ServiceList) {
        $cmdArgs += $ServiceList -split '\s+'
    }
    Write-ColorOutput "执行: docker compose $($cmdArgs -join ' ')" "DEBUG"
    & docker compose @cmdArgs
    return $LASTEXITCODE
}

function Get-ContainerStatus {
    param([string]$ServiceName)
    $containerName = "mcp-$($ServiceName -replace '-', '-')"
    try {
        $status = docker inspect --format='{{.State.Status}}' $containerName 2>$null
        $health = docker inspect --format='{{.State.Health.Status}}' $containerName 2>$null
        $uptime = docker inspect --format='{{.State.StartedAt}}' $containerName 2>$null
        $port = docker inspect --format='{{range $p, $conf := .NetworkSettings.Ports}}{{(index $conf 0).HostPort}}{{end}}' $containerName 2>$null
        return @{
            Status = $status
            Health = $health
            Uptime = $uptime
            Port = $port
            Running = ($status -eq "running")
        }
    } catch {
        return @{ Status = "not found"; Health = "N/A"; Uptime = "N/A"; Port = ""; Running = $false }
    }
}

# =============================================================================
# 操作函数
# =============================================================================

function Start-Services {
    $targetServices = Get-TargetServices
    Write-ColorOutput "============================================" "INFO"
    Write-ColorOutput "启动 MCP 服务" "INFO"
    Write-ColorOutput "============================================" "INFO"

    $serviceList = ($targetServices | ForEach-Object { $_.Name }) -join " "
    $exitCode = Invoke-DockerCompose -ComposeAction "up -d" -ServiceList $serviceList

    if ($exitCode -eq 0) {
        Write-ColorOutput "服务启动命令已发送" "SUCCESS"
        Start-Sleep -Seconds 3
        Show-Status
    } else {
        Write-ColorOutput "服务启动失败" "ERROR"
    }
}

function Stop-Services {
    $targetServices = Get-TargetServices
    Write-ColorOutput "============================================" "INFO"
    Write-ColorOutput "停止 MCP 服务" "INFO"
    Write-ColorOutput "============================================" "INFO"

    $serviceList = ($targetServices | ForEach-Object { $_.Name }) -join " "
    $exitCode = Invoke-DockerCompose -ComposeAction "stop" -ServiceList $serviceList

    if ($exitCode -eq 0) {
        Write-ColorOutput "服务已停止" "SUCCESS"
    } else {
        Write-ColorOutput "服务停止失败" "ERROR"
    }
}

function Restart-Services {
    $targetServices = Get-TargetServices
    Write-ColorOutput "============================================" "INFO"
    Write-ColorOutput "重启 MCP 服务" "INFO"
    Write-ColorOutput "============================================" "INFO"

    $serviceList = ($targetServices | ForEach-Object { $_.Name }) -join " "
    $exitCode = Invoke-DockerCompose -ComposeAction "restart" -ServiceList $serviceList

    if ($exitCode -eq 0) {
        Write-ColorOutput "服务重启命令已发送" "SUCCESS"
        Start-Sleep -Seconds 3
        Show-Status
    } else {
        Write-ColorOutput "服务重启失败" "ERROR"
    }
}

function Show-Status {
    Write-ColorOutput "============================================" "INFO"
    Write-ColorOutput "MCP 服务状态" "INFO"
    Write-ColorOutput "============================================" "INFO"

    $targetServices = Get-TargetServices
    $results = @()

    foreach ($svc in $targetServices) {
        $containerInfo = Get-ContainerStatus -ServiceName $svc.Name

        $statusColor = switch ($containerInfo.Status) {
            "running" { "SUCCESS" }
            "exited" { "ERROR" }
            "not found" { "WARN" }
            default { "WARN" }
        }

        $healthColor = switch ($containerInfo.Health) {
            "healthy" { "SUCCESS" }
            "unhealthy" { "ERROR" }
            "starting" { "WARN" }
            default { "WHITE" }
        }

        $results += [PSCustomObject]@{
            "服务名称" = $svc.Display
            "类别" = $svc.Category
            "容器状态" = $containerInfo.Status
            "健康状态" = $containerInfo.Health
            "端口" = $svc.Port
            "启动时间" = $containerInfo.Uptime
        }
    }

    $results | Format-Table -AutoSize | Out-String | Write-Host

    # 统计信息
    $running = ($results | Where-Object { $_."容器状态" -eq "running" }).Count
    $total = $results.Count
    Write-ColorOutput "运行中: $running / $total" $(if ($running -eq $total) { "SUCCESS" } else { "WARN" })
}

function Show-Logs {
    $targetServices = Get-TargetServices
    if ($targetServices.Count -eq 0) {
        Write-ColorOutput "请指定要查看日志的服务" "ERROR"
        return
    }

    $serviceList = ($targetServices | ForEach-Object { $_.Name }) -join " "
    $followFlag = if ($Follow) { "-f" } else { "" }

    Write-ColorOutput "============================================" "INFO"
    Write-ColorOutput "查看日志: $serviceList" "INFO"
    Write-ColorOutput "============================================" "INFO"

    $cmd = "docker compose -f `"$ComposeFile`" logs $followFlag --tail=$Lines $serviceList"
    Invoke-Expression $cmd
}

function Update-Services {
    $targetServices = Get-TargetServices
    Write-ColorOutput "============================================" "INFO"
    Write-ColorOutput "更新 MCP 服务" "INFO"
    Write-ColorOutput "============================================" "INFO"

    # 1. 拉取最新镜像
    Write-ColorOutput "步骤 1/3: 拉取最新镜像..." "INFO"
    $serviceList = ($targetServices | ForEach-Object { $_.Name }) -join " "
    Invoke-DockerCompose -ComposeAction "pull" -ServiceList $serviceList

    # 2. 重新构建 (如果需要)
    Write-ColorOutput "步骤 2/3: 重新构建服务..." "INFO"
    Invoke-DockerCompose -ComposeAction "build" -ServiceList $serviceList

    # 3. 重新部署
    Write-ColorOutput "步骤 3/3: 重新部署服务..." "INFO"
    $exitCode = Invoke-DockerCompose -ComposeAction "up -d" -ServiceList $serviceList

    if ($exitCode -eq 0) {
        Write-ColorOutput "服务更新完成" "SUCCESS"
        Start-Sleep -Seconds 3
        Show-Status
    } else {
        Write-ColorOutput "服务更新失败" "ERROR"
    }
}

function Show-Containers {
    Write-ColorOutput "============================================" "INFO"
    Write-ColorOutput "MCP 容器列表" "INFO"
    Write-ColorOutput "============================================" "INFO"

    docker ps --filter "name=mcp-" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
}

function Invoke-ContainerExec {
    $targetServices = Get-TargetServices
    if ($targetServices.Count -ne 1) {
        Write-ColorOutput "exec 操作只能指定一个服务" "ERROR"
        return
    }
    if (-not $Command) {
        Write-ColorOutput "请使用 -Command 参数指定要执行的命令" "ERROR"
        return
    }

    $serviceName = $targetServices[0].Name
    $containerName = "mcp-$serviceName"

    Write-ColorOutput "在容器 $containerName 中执行: $Command" "INFO"
    docker exec -it $containerName $Command
}

function Clear-Resources {
    Write-ColorOutput "============================================" "INFO"
    Write-ColorOutput "清理资源" "INFO"
    Write-ColorOutput "============================================" "INFO"

    if (-not $Force) {
        $confirm = Read-Host "确定要清理未使用的 Docker 资源吗? (y/N)"
        if ($confirm -ne "y" -and $confirm -ne "Y") {
            Write-ColorOutput "操作已取消" "WARN"
            return
        }
    }

    Write-ColorOutput "清理未使用的容器..." "INFO"
    docker container prune -f

    Write-ColorOutput "清理未使用的镜像..." "INFO"
    docker image prune -f

    Write-ColorOutput "清理未使用的卷..." "INFO"
    docker volume prune -f

    Write-ColorOutput "清理未使用的网络..." "INFO"
    docker network prune -f

    Write-ColorOutput "清理完成" "SUCCESS"
}

# =============================================================================
# 主程序
# =============================================================================

function Main {
    Write-ColorOutput "========================================" "INFO"
    Write-ColorOutput "    AI MCP 服务管理系统" "INFO"
    Write-ColorOutput "========================================" "INFO"
    Write-ColorOutput "操作: $Action" "INFO"
    if ($Services.Count -gt 0) {
        Write-ColorOutput "服务: $($Services -join ', ')" "INFO"
    } else {
        Write-ColorOutput "服务: 全部" "INFO"
    }
    Write-ColorOutput "========================================" "INFO"
    Write-ColorOutput ""

    # 检查 Docker
    if (-not (Test-DockerRunning)) {
        Write-ColorOutput "Docker 未运行，请先启动 Docker Desktop" "ERROR"
        exit 1
    }

    # 检查 Compose 文件
    Test-ComposeFile

    # 执行操作
    switch ($Action) {
        "start"   { Start-Services }
        "stop"    { Stop-Services }
        "restart" { Restart-Services }
        "status"  { Show-Status }
        "logs"    { Show-Logs }
        "update"  { Update-Services }
        "ps"      { Show-Containers }
        "exec"    { Invoke-ContainerExec }
        "cleanup" { Clear-Resources }
        default   { Write-ColorOutput "未知操作: $Action" "ERROR" }
    }
}

Main
