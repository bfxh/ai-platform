<#
.SYNOPSIS
    AI MCP Docker 镜像构建脚本
    构建基础镜像和所有 MCP 服务镜像

.DESCRIPTION
    该脚本执行以下操作:
    1. 构建 ai/mcp-base 基础镜像
    2. 为每个 MCP 服务构建独立镜像
    3. 管理镜像标签 (latest, version, timestamp)
    4. 记录构建日志

.PARAMETER Tag
    指定镜像标签，默认为 "latest"

.PARAMETER Services
    指定要构建的服务列表，默认为所有服务

.PARAMETER SkipBase
    跳过基础镜像构建

.PARAMETER Push
    构建完成后推送到仓库

.EXAMPLE
    .\build-all.ps1
    构建所有镜像，标签为 latest

.EXAMPLE
    .\build-all.ps1 -Tag v1.0.0 -Services blender-mcp,code-quality
    只构建 blender-mcp 和 code-quality 服务，标签为 v1.0.0

.EXAMPLE
    .\build-all.ps1 -SkipBase
    跳过基础镜像构建，只构建服务镜像
#>

[CmdletBinding()]
param(
    [string]$Tag = "latest",
    [string[]]$Services = @(),
    [switch]$SkipBase,
    [switch]$Push,
    [string]$Registry = ""
)

# =============================================================================
# 配置
# =============================================================================
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BuildLogDir = Join-Path $ScriptDir "build-logs"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BuildLogFile = Join-Path $BuildLogDir "build-$Timestamp.log"

# 服务定义
$AllServices = @(
    # JM 类服务
    @{ Name = "blender-mcp"; Image = "ai/mcp-jm-blender"; Dockerfile = "services/blender.Dockerfile"; Port = 8001 },
    @{ Name = "unity-mcp"; Image = "ai/mcp-jm-unity"; Dockerfile = "services/unity.Dockerfile"; Port = 8002 },
    @{ Name = "ue-mcp"; Image = "ai/mcp-jm-ue"; Dockerfile = "services/ue.Dockerfile"; Port = 8003 },
    @{ Name = "godot-mcp"; Image = "ai/mcp-jm-godot"; Dockerfile = "services/godot.Dockerfile"; Port = 8004 },

    # BC 类服务
    @{ Name = "code-quality"; Image = "ai/mcp-bc-quality"; Dockerfile = "services/code-quality.Dockerfile"; Port = 8005 },
    @{ Name = "github-dl"; Image = "ai/mcp-bc-github"; Dockerfile = "services/github-dl.Dockerfile"; Port = 8006 },
    @{ Name = "vs-mgr"; Image = "ai/mcp-bc-vsmgr"; Dockerfile = "services/vs-mgr.Dockerfile"; Port = 8007 },
    @{ Name = "dev-mgr"; Image = "ai/mcp-bc-devmgr"; Dockerfile = "services/dev-mgr.Dockerfile"; Port = 8008 },

    # Tools 类服务
    @{ Name = "download-manager"; Image = "ai/mcp-tools-download"; Dockerfile = "services/download-manager.Dockerfile"; Port = 8009 },
    @{ Name = "network-optimizer"; Image = "ai/mcp-tools-network"; Dockerfile = "services/network-optimizer.Dockerfile"; Port = 8010 },
    @{ Name = "memory-monitor"; Image = "ai/mcp-tools-memory"; Dockerfile = "services/memory-monitor.Dockerfile"; Port = 8011 }
)

# =============================================================================
# 辅助函数
# =============================================================================

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $BuildLogFile -Value $logEntry
}

function Test-DockerAvailable {
    try {
        $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $dockerVersion
        }
    } catch {
        return $null
    }
    return $null
}

function Build-Image {
    param(
        [string]$ImageName,
        [string]$Dockerfile,
        [string]$BuildTag,
        [string]$Context = $ProjectRoot
    )

    Write-Log "开始构建镜像: $ImageName`:$BuildTag" "INFO"
    Write-Log "Dockerfile: $Dockerfile" "DEBUG"
    Write-Log "构建上下文: $Context" "DEBUG"

    $dockerfilePath = Join-Path $ScriptDir $Dockerfile
    if (-not (Test-Path $dockerfilePath)) {
        Write-Log "Dockerfile 不存在: $dockerfilePath" "ERROR"
        return $false
    }

    $buildArgs = @(
        "build",
        "-f", $dockerfilePath,
        "-t", "$ImageName`:$BuildTag",
        "--build-arg", "BUILD_DATE=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')",
        "--build-arg", "VCS_REF=$(git rev-parse --short HEAD 2>$null || echo 'unknown')",
        $Context
    )

    $startTime = Get-Date
    try {
        & docker @buildArgs 2>&1 | Tee-Object -FilePath $BuildLogFile -Append
        $buildResult = $LASTEXITCODE
    } catch {
        Write-Log "构建异常: $_" "ERROR"
        return $false
    }
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds

    if ($buildResult -eq 0) {
        Write-Log "镜像构建成功: $ImageName`:$BuildTag (耗时: $([math]::Round($duration, 2)) 秒)" "SUCCESS"

        # 添加额外标签
        if ($BuildTag -ne "latest") {
            docker tag "$ImageName`:$BuildTag" "$ImageName`:latest" 2>&1 | Out-Null
            Write-Log "添加标签: $ImageName`:latest" "INFO"
        }

        # 添加时间戳标签
        $timestampTag = "$ImageName`:$Timestamp"
        docker tag "$ImageName`:$BuildTag" $timestampTag 2>&1 | Out-Null
        Write-Log "添加标签: $timestampTag" "INFO"

        return $true
    } else {
        Write-Log "镜像构建失败: $ImageName`:$BuildTag (退出码: $buildResult)" "ERROR"
        return $false
    }
}

function Push-Image {
    param([string]$ImageName, [string]$BuildTag)

    if (-not $Push) { return }

    $fullImageName = if ($Registry) { "$Registry/$ImageName" } else { $ImageName }

    Write-Log "推送镜像: $fullImageName`:$BuildTag" "INFO"

    if ($Registry) {
        docker tag "$ImageName`:$BuildTag" "$fullImageName`:$BuildTag" 2>&1 | Out-Null
    }

    $pushResult = docker push "$fullImageName`:$BuildTag" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "镜像推送成功: $fullImageName`:$BuildTag" "SUCCESS"
    } else {
        Write-Log "镜像推送失败: $fullImageName`:$BuildTag" "ERROR"
    }
}

# =============================================================================
# 主程序
# =============================================================================

function Main {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "    AI MCP Docker 镜像构建系统" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    # 创建日志目录
    if (-not (Test-Path $BuildLogDir)) {
        New-Item -ItemType Directory -Force -Path $BuildLogDir | Out-Null
    }

    Write-Log "构建开始 - 标签: $Tag" "INFO"
    Write-Log "项目根目录: $ProjectRoot" "INFO"

    # 检查 Docker 是否可用
    $dockerVersion = Test-DockerAvailable
    if (-not $dockerVersion) {
        Write-Log "Docker 未安装或未运行，请先安装 Docker Desktop" "ERROR"
        exit 1
    }
    Write-Log "Docker 版本: $dockerVersion" "INFO"

    # 确定要构建的服务
    $servicesToBuild = if ($Services.Count -gt 0) {
        $serviceNames = $Services -split '[,;]'
        $AllServices | Where-Object { $serviceNames -contains $_.Name }
    } else {
        $AllServices
    }

    Write-Log "将要构建 $($servicesToBuild.Count) 个服务" "INFO"

    # 构建基础镜像
    if (-not $SkipBase) {
        Write-Log "============================================" "INFO"
        Write-Log "构建基础镜像: ai/mcp-base" "INFO"
        Write-Log "============================================" "INFO"

        $baseDockerfile = Join-Path $ScriptDir "base\Dockerfile"
        if (Test-Path $baseDockerfile) {
            $baseBuildArgs = @(
                "build",
                "-f", $baseDockerfile,
                "-t", "ai/mcp-base:$Tag",
                "-t", "ai/mcp-base:latest",
                $ScriptDir
            )

            $startTime = Get-Date
            & docker @baseBuildArgs 2>&1 | Tee-Object -FilePath $BuildLogFile -Append
            $baseResult = $LASTEXITCODE
            $duration = ((Get-Date) - $startTime).TotalSeconds

            if ($baseResult -eq 0) {
                Write-Log "基础镜像构建成功 (耗时: $([math]::Round($duration, 2)) 秒)" "SUCCESS"
            } else {
                Write-Log "基础镜像构建失败，退出码: $baseResult" "ERROR"
                exit 1
            }
        } else {
            Write-Log "基础 Dockerfile 不存在: $baseDockerfile" "ERROR"
            exit 1
        }
    } else {
        Write-Log "跳过基础镜像构建" "WARN"
    }

    # 构建服务镜像
    Write-Log "============================================" "INFO"
    Write-Log "构建服务镜像" "INFO"
    Write-Log "============================================" "INFO"

    $successCount = 0
    $failCount = 0
    $buildResults = @()

    foreach ($service in $servicesToBuild) {
        Write-Log "--------------------------------------------" "INFO"
        Write-Log "构建服务: $($service.Name)" "INFO"
        Write-Log "镜像名称: $($service.Image)" "INFO"
        Write-Log "服务端口: $($service.Port)" "INFO"
        Write-Log "--------------------------------------------" "INFO"

        $result = Build-Image -ImageName $service.Image -Dockerfile $service.Dockerfile -BuildTag $Tag

        if ($result) {
            $successCount++
            Push-Image -ImageName $service.Image -BuildTag $Tag
            Push-Image -ImageName $service.Image -BuildTag "latest"
        } else {
            $failCount++
        }

        $buildResults += [PSCustomObject]@{
            Service = $service.Name
            Image = $service.Image
            Port = $service.Port
            Status = if ($result) { "成功" } else { "失败" }
        }
    }

    # 构建摘要
    Write-Log "============================================" "INFO"
    Write-Log "构建完成摘要" "INFO"
    Write-Log "============================================" "INFO"
    Write-Log "总服务数: $($servicesToBuild.Count)" "INFO"
    Write-Log "成功: $successCount" "SUCCESS"
    Write-Log "失败: $failCount" $(if ($failCount -gt 0) { "ERROR" } else { "INFO" })
    Write-Log "日志文件: $BuildLogFile" "INFO"

    Write-Host ""
    Write-Host "构建结果:" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Gray
    $buildResults | Format-Table -AutoSize | Out-String | Write-Host

    # 显示镜像列表
    Write-Log "当前 MCP 镜像列表:" "INFO"
    docker images --filter=reference="ai/mcp-*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" 2>&1 | Tee-Object -FilePath $BuildLogFile -Append

    if ($failCount -gt 0) {
        Write-Log "部分服务构建失败，请检查日志" "ERROR"
        exit 1
    } else {
        Write-Log "所有服务构建成功!" "SUCCESS"
    }
}

# 执行主程序
Main
