<#
.SYNOPSIS
    AI MCP 健康检查脚本
    检查每个容器健康状态、端口响应，自动重启不健康服务，发送告警通知

.DESCRIPTION
    该脚本执行以下操作:
    1. 检查每个 MCP 容器的 Docker 健康状态
    2. 检查服务端口是否响应
    3. 自动重启不健康的服务
    4. 发送告警通知 (支持 Webhook)
    5. 生成健康检查报告

.PARAMETER Continuous
    持续运行模式，按指定间隔循环检查

.PARAMETER Interval
    持续运行时的检查间隔 (秒)，默认 60

.PARAMETER AutoRestart
    自动重启不健康的容器

.PARAMETER AlertWebhook
    告警 Webhook URL

.PARAMETER Report
    生成健康检查报告文件

.EXAMPLE
    .\health-check.ps1
    执行一次健康检查

.EXAMPLE
    .\health-check.ps1 -Continuous -Interval 30 -AutoRestart
    每 30 秒持续检查，自动重启不健康服务

.EXAMPLE
    .\health-check.ps1 -AutoRestart -AlertWebhook "https://hooks.slack.com/..."
    执行检查，自动重启并发送告警到 Slack

.EXAMPLE
    .\health-check.ps1 -Report
    执行检查并生成报告文件
#>

[CmdletBinding()]
param(
    [switch]$Continuous,
    [int]$Interval = 60,
    [switch]$AutoRestart,
    [string]$AlertWebhook = "",
    [switch]$Report,
    [string]$ReportPath = ""
)

# =============================================================================
# 配置
# =============================================================================
$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$HealthLogDir = Join-Path $ScriptDir "health-logs"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$HealthLogFile = Join-Path $HealthLogDir "health-check-$Timestamp.log"
$ReportFile = if ($ReportPath) { $ReportPath } else { Join-Path $HealthLogDir "report-$Timestamp.html" }

# 加载 .env 配置
$EnvFile = Join-Path $ScriptDir ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^([^#][^=]*)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# 服务定义
$AllServices = @(
    @{ Name = "blender-mcp"; Display = "Blender MCP"; Category = "JM"; Port = 8001; Container = "mcp-blender" },
    @{ Name = "unity-mcp"; Display = "Unity MCP"; Category = "JM"; Port = 8002; Container = "mcp-unity" },
    @{ Name = "ue-mcp"; Display = "UE MCP"; Category = "JM"; Port = 8003; Container = "mcp-ue" },
    @{ Name = "godot-mcp"; Display = "Godot MCP"; Category = "JM"; Port = 8004; Container = "mcp-godot" },
    @{ Name = "code-quality"; Display = "Code Quality"; Category = "BC"; Port = 8005; Container = "mcp-code-quality" },
    @{ Name = "github-dl"; Display = "GitHub DL"; Category = "BC"; Port = 8006; Container = "mcp-github-dl" },
    @{ Name = "vs-mgr"; Display = "VS Manager"; Category = "BC"; Port = 8007; Container = "mcp-vs-mgr" },
    @{ Name = "dev-mgr"; Display = "Dev Manager"; Category = "BC"; Port = 8008; Container = "mcp-dev-mgr" },
    @{ Name = "download-manager"; Display = "Download Manager"; Category = "Tools"; Port = 8009; Container = "mcp-download-manager" },
    @{ Name = "network-optimizer"; Display = "Network Optimizer"; Category = "Tools"; Port = 8010; Container = "mcp-network-optimizer" },
    @{ Name = "memory-monitor"; Display = "Memory Monitor"; Category = "Tools"; Port = 8011; Container = "mcp-memory-monitor" },
    @{ Name = "n8n"; Display = "N8N Workflow"; Category = "Shared"; Port = 5678; Container = "mcp-n8n" }
)

# =============================================================================
# 辅助函数
# =============================================================================

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $colors = @{ "INFO" = "Cyan"; "SUCCESS" = "Green"; "WARN" = "Yellow"; "ERROR" = "Red"; "DEBUG" = "Gray" }
    $color = if ($colors.ContainsKey($Level)) { $colors[$Level] } else { "White" }
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry -ForegroundColor $color
    if (-not (Test-Path $HealthLogDir)) {
        New-Item -ItemType Directory -Force -Path $HealthLogDir | Out-Null
    }
    Add-Content -Path $HealthLogFile -Value $logEntry
}

function Test-Port {
    param([string]$HostName = "localhost", [int]$Port, [int]$Timeout = 5000)
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $connection = $client.BeginConnect($HostName, $Port, $null, $null)
        $success = $connection.AsyncWaitHandle.WaitOne($Timeout, $false)
        if ($success) {
            $client.EndConnect($connection)
            $client.Close()
            return $true
        }
        $client.Close()
        return $false
    } catch {
        return $false
    }
}

function Test-HttpHealth {
    param([string]$Url, [int]$Timeout = 10000)
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec ($Timeout / 1000) -UseBasicParsing -ErrorAction Stop
        return @{ Success = $true; StatusCode = $response.StatusCode; ResponseTime = 0 }
    } catch {
        return @{ Success = $false; StatusCode = $_.Exception.Response.StatusCode.value__; ResponseTime = 0 }
    }
}

function Get-ContainerHealth {
    param([string]$ContainerName)
    try {
        $inspect = docker inspect $ContainerName 2>$null | ConvertFrom-Json
        if (-not $inspect) {
            return @{ Exists = $false; Status = "not_found"; Health = "unknown"; Uptime = "unknown"; RestartCount = 0 }
        }

        $state = $inspect[0].State
        $health = if ($state.Health) { $state.Health.Status } else { "none" }
        $uptime = if ($state.StartedAt -and $state.StartedAt -ne "0001-01-01T00:00:00Z") {
            $startTime = [DateTime]::Parse($state.StartedAt)
            $duration = (Get-Date) - $startTime
            "$([math]::Floor($duration.TotalHours))h $([math]::Floor($duration.TotalMinutes % 60))m"
        } else { "unknown" }

        return @{
            Exists = $true
            Status = $state.Status
            Health = $health
            Uptime = $uptime
            RestartCount = $state.RestartCount
            ExitCode = $state.ExitCode
        }
    } catch {
        return @{ Exists = $false; Status = "error"; Health = "unknown"; Uptime = "unknown"; RestartCount = 0; ExitCode = -1 }
    }
}

function Restart-Container {
    param([string]$ContainerName)
    Write-Log "正在重启容器: $ContainerName" "WARN"
    try {
        docker restart $ContainerName 2>$null | Out-Null
        Start-Sleep -Seconds 5
        $newHealth = Get-ContainerHealth -ContainerName $ContainerName
        if ($newHealth.Status -eq "running") {
            Write-Log "容器重启成功: $ContainerName" "SUCCESS"
            return $true
        } else {
            Write-Log "容器重启后仍未正常运行: $ContainerName" "ERROR"
            return $false
        }
    } catch {
        Write-Log "容器重启失败: $ContainerName - $_" "ERROR"
        return $false
    }
}

function Send-Alert {
    param([string]$Message, [string]$Severity = "warning")
    $webhookUrl = if ($AlertWebhook) { $AlertWebhook } else { $env:ALERT_WEBHOOK_URL }
    if (-not $webhookUrl) { return }

    try {
        $payload = @{
            text = "AI MCP 健康检查告警"
            severity = $Severity
            message = $Message
            timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
            hostname = $env:COMPUTERNAME
        } | ConvertTo-Json

        Invoke-RestMethod -Uri $webhookUrl -Method POST -Body $payload -ContentType "application/json" -TimeoutSec 10 | Out-Null
        Write-Log "告警已发送" "INFO"
    } catch {
        Write-Log "告警发送失败: $_" "WARN"
    }
}

function Get-ContainerStats {
    param([string]$ContainerName)
    try {
        $stats = docker stats $ContainerName --no-stream --format "{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}|{{.BlockIO}}" 2>$null
        if ($stats) {
            $parts = $stats -split '\|'
            return @{
                CPU = $parts[0].Trim()
                Memory = $parts[1].Trim()
                Network = $parts[2].Trim()
                Disk = $parts[3].Trim()
            }
        }
    } catch {}
    return @{ CPU = "N/A"; Memory = "N/A"; Network = "N/A"; Disk = "N/A" }
}

# =============================================================================
# 健康检查主逻辑
# =============================================================================

function Invoke-HealthCheck {
    Write-Log "============================================" "INFO"
    Write-Log "开始健康检查" "INFO"
    Write-Log "============================================" "INFO"

    $results = @()
    $issues = @()
    $restartCount = 0

    foreach ($svc in $AllServices) {
        Write-Log "检查服务: $($svc.Display)" "DEBUG"

        $result = [PSCustomObject]@{
            Service = $svc.Display
            Category = $svc.Category
            Port = $svc.Port
            Container = $svc.Container
            ContainerStatus = "unknown"
            DockerHealth = "unknown"
            PortOpen = $false
            HttpHealth = $false
            Uptime = "unknown"
            Stats = @{}
            Issues = @()
        }

        # 1. 检查容器状态
        $containerHealth = Get-ContainerHealth -ContainerName $svc.Container
        $result.ContainerStatus = $containerHealth.Status
        $result.DockerHealth = $containerHealth.Health
        $result.Uptime = $containerHealth.Uptime

        if (-not $containerHealth.Exists) {
            $result.Issues += "容器不存在"
            $issues += "$($svc.Display): 容器不存在"
        } elseif ($containerHealth.Status -ne "running") {
            $result.Issues += "容器未运行 (状态: $($containerHealth.Status))"
            $issues += "$($svc.Display): 容器未运行"

            # 自动重启
            if ($AutoRestart) {
                if (Restart-Container -ContainerName $svc.Container) {
                    $restartCount++
                    $result.ContainerStatus = "running"
                }
            }
        } elseif ($containerHealth.Health -eq "unhealthy") {
            $result.Issues += "Docker 健康检查失败"
            $issues += "$($svc.Display): 健康检查失败"

            if ($AutoRestart) {
                if (Restart-Container -ContainerName $svc.Container) {
                    $restartCount++
                    $result.DockerHealth = "starting"
                }
            }
        }

        # 2. 检查端口
        if ($result.ContainerStatus -eq "running") {
            $portOpen = Test-Port -Port $svc.Port -Timeout 3000
            $result.PortOpen = $portOpen
            if (-not $portOpen) {
                $result.Issues += "端口 $($svc.Port) 无响应"
                $issues += "$($svc.Display): 端口无响应"
            }
        }

        # 3. HTTP 健康检查
        if ($result.PortOpen) {
            $healthUrl = "http://localhost:$($svc.Port)/health"
            $httpResult = Test-HttpHealth -Url $healthUrl -Timeout 5000
            $result.HttpHealth = $httpResult.Success
            if (-not $httpResult.Success) {
                $result.Issues += "HTTP 健康端点返回 $($httpResult.StatusCode)"
            }
        }

        # 4. 获取资源统计
        if ($containerHealth.Exists) {
            $result.Stats = Get-ContainerStats -ContainerName $svc.Container
        }

        # 输出结果
        $statusColor = if ($result.Issues.Count -eq 0) { "SUCCESS" } else { "WARN" }
        $statusText = if ($result.Issues.Count -eq 0) { "健康" } else { "异常 ($($result.Issues.Count))" }
        Write-Log "$($svc.Display): $statusText" $statusColor

        if ($result.Issues.Count -gt 0) {
            foreach ($issue in $result.Issues) {
                Write-Log "  - $issue" "WARN"
            }
        }

        $results += $result
    }

    # 摘要
    Write-Log "============================================" "INFO"
    Write-Log "健康检查摘要" "INFO"
    Write-Log "============================================" "INFO"

    $healthy = ($results | Where-Object { $_.Issues.Count -eq 0 }).Count
    $unhealthy = ($results | Where-Object { $_.Issues.Count -gt 0 }).Count
    $total = $results.Count

    Write-Log "总服务数: $total" "INFO"
    Write-Log "健康: $healthy" "SUCCESS"
    Write-Log "异常: $unhealthy" $(if ($unhealthy -gt 0) { "WARN" } else { "INFO" })

    if ($AutoRestart -and $restartCount -gt 0) {
        Write-Log "自动重启: $restartCount 个容器" "INFO"
    }

    # 发送告警
    if ($issues.Count -gt 0) {
        $alertMessage = "发现 $($issues.Count) 个问题:`n" + ($issues -join "`n")
        Write-Log "发送告警通知..." "WARN"
        Send-Alert -Message $alertMessage -Severity "warning"
    }

    # 生成报告
    if ($Report) {
        Export-HealthReport -Results $results -Healthy $healthy -Unhealthy $unhealthy -RestartCount $restartCount
    }

    return @{ Results = $results; Healthy = $healthy; Unhealthy = $unhealthy; Issues = $issues }
}

# =============================================================================
# 报告生成
# =============================================================================

function Export-HealthReport {
    param($Results, [int]$Healthy, [int]$Unhealthy, [int]$RestartCount)

    $html = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AI MCP 健康检查报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .stat-box { padding: 15px 25px; border-radius: 6px; text-align: center; }
        .stat-box.success { background: #d4edda; color: #155724; }
        .stat-box.warning { background: #fff3cd; color: #856404; }
        .stat-box.danger { background: #f8d7da; color: #721c24; }
        .stat-number { font-size: 2em; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #007acc; color: white; }
        tr:hover { background: #f5f5f5; }
        .status-ok { color: #28a745; font-weight: bold; }
        .status-error { color: #dc3545; font-weight: bold; }
        .issues { color: #856404; font-size: 0.9em; }
        .timestamp { color: #666; font-size: 0.9em; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI MCP 健康检查报告</h1>
        <div class="summary">
            <div class="stat-box success">
                <div class="stat-number">$Healthy</div>
                <div>健康</div>
            </div>
            <div class="stat-box $(if ($Unhealthy -gt 0) { 'danger' } else { 'success' })">
                <div class="stat-number">$Unhealthy</div>
                <div>异常</div>
            </div>
            <div class="stat-box warning">
                <div class="stat-number">$RestartCount</div>
                <div>重启</div>
            </div>
        </div>
        <table>
            <tr>
                <th>服务</th>
                <th>类别</th>
                <th>容器状态</th>
                <th>Docker 健康</th>
                <th>端口</th>
                <th>HTTP</th>
                <th>运行时间</th>
                <th>CPU</th>
                <th>内存</th>
                <th>问题</th>
            </tr>
"@

    foreach ($r in $Results) {
        $statusClass = if ($r.Issues.Count -eq 0) { "status-ok" } else { "status-error" }
        $statusText = if ($r.Issues.Count -eq 0) { "正常" } else { "异常" }
        $issuesText = if ($r.Issues.Count -gt 0) { $r.Issues -join "; " } else { "-" }
        $cpu = if ($r.Stats.CPU) { $r.Stats.CPU } else { "N/A" }
        $mem = if ($r.Stats.Memory) { $r.Stats.Memory } else { "N/A" }

        $html += @"
            <tr>
                <td>$($r.Service)</td>
                <td>$($r.Category)</td>
                <td>$($r.ContainerStatus)</td>
                <td>$($r.DockerHealth)</td>
                <td>$(if ($r.PortOpen) { "开放" } else { "关闭" })</td>
                <td class="$statusClass">$statusText</td>
                <td>$($r.Uptime)</td>
                <td>$cpu</td>
                <td>$mem</td>
                <td class="issues">$issuesText</td>
            </tr>
"@
    }

    $html += @"
        </table>
        <div class="timestamp">生成时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</div>
    </div>
</body>
</html>
"@

    $html | Out-File -FilePath $ReportFile -Encoding UTF8
    Write-Log "报告已生成: $ReportFile" "SUCCESS"
}

# =============================================================================
# 主程序
# =============================================================================

function Main {
    Write-Log "========================================" "INFO"
    Write-Log "    AI MCP 健康检查系统" "INFO"
    Write-Log "========================================" "INFO"

    if ($Continuous) {
        Write-Log "持续运行模式，间隔: $Interval 秒" "INFO"
        if ($AutoRestart) {
            Write-Log "自动重启: 已启用" "INFO"
        }
        if ($AlertWebhook -or $env:ALERT_WEBHOOK_URL) {
            Write-Log "告警通知: 已启用" "INFO"
        }

        while ($true) {
            Invoke-HealthCheck
            Write-Log "等待 $Interval 秒后进行下一次检查..." "INFO"
            Start-Sleep -Seconds $Interval
        }
    } else {
        Invoke-HealthCheck
    }
}

Main
