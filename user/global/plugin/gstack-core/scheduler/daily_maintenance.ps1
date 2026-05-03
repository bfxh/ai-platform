# 每日维护脚本
# 由 GSTACK 自动创建，用于 Windows 任务计划程序

$aiPath = "\python"
$pythonExe = "python"
$reportsDir = "$aiPath\reports\daily"

# 创建报告目录
if (-not (Test-Path $reportsDir)) {
    New-Item -ItemType Directory -Force -Path $reportsDir
}

$logFile = "$reportsDir\$(Get-Date -Format 'yyyyMMdd')_maintenance.log"

# 开始日志
"=====================================" | Out-File -Append $logFile
"GSTACK 每日维护任务" | Out-File -Append $logFile
"执行时间: $(Get-Date)" | Out-File -Append $logFile
"=====================================" | Out-File -Append $logFile

# 1. 执行 CC 目录清理
"\n1. 执行 CC 目录清理..." | Out-File -Append $logFile
try {
    $ccHousekeeper = "$aiPath\MCP_Core\skills\cc_housekeeper\skill.py"
    if (Test-Path $ccHousekeeper) {
        & $pythonExe $ccHousekeeper | Out-File -Append $logFile
        "✅ CC 清理完成" | Out-File -Append $logFile
    } else {
        "❌ CC 清理工具不存在" | Out-File -Append $logFile
    }
} catch {
    "❌ CC 清理失败: $($_.Exception.Message)" | Out-File -Append $logFile
}

# 2. 执行 MCP 健康度检查
"\n2. 执行 MCP 健康度检查..." | Out-File -Append $logFile
try {
    $mcpHealth = "$aiPath\MCP_Core\skills\mcp_health_monitor\skill.py"
    if (Test-Path $mcpHealth) {
        & $pythonExe $mcpHealth | Out-File -Append $logFile
        "✅ MCP 健康检查完成" | Out-File -Append $logFile
    } else {
        "❌ MCP 健康检查工具不存在" | Out-File -Append $logFile
    }
} catch {
    "❌ MCP 健康检查失败: $($_.Exception.Message)" | Out-File -Append $logFile
}

# 3. 执行依赖检查
"\n3. 执行依赖检查..." | Out-File -Append $logFile
try {
    $dependencyChecker = "$aiPath\MCP_Core\skills\dependency_checker\skill.py"
    if (Test-Path $dependencyChecker) {
        & $pythonExe $dependencyChecker | Out-File -Append $logFile
        "✅ 依赖检查完成" | Out-File -Append $logFile
    } else {
        "❌ 依赖检查工具不存在" | Out-File -Append $logFile
    }
} catch {
    "❌ 依赖检查失败: $($_.Exception.Message)" | Out-File -Append $logFile
}

# 4. 生成维护报告
"\n4. 生成维护报告..." | Out-File -Append $logFile
try {
    $reportContent = @"
# GSTACK 每日维护报告

## 执行时间
$(Get-Date)

## 执行内容
1. CC 目录清理
2. MCP 健康度检查
3. 依赖检查

## 详细日志
查看: $logFile

## 系统信息
- 操作系统: $env:OS
- PowerShell 版本: $PSVersionTable.PSVersion
- Python 版本: $(& $pythonExe --version 2>&1)
"@
    
    $reportFile = "$reportsDir\$(Get-Date -Format 'yyyyMMdd')_maintenance_report.md"
    $reportContent | Out-File -Encoding UTF8 $reportFile
    "✅ 维护报告生成: $reportFile" | Out-File -Append $logFile
} catch {
    "❌ 报告生成失败: $($_.Exception.Message)" | Out-File -Append $logFile
}

"\n=====================================" | Out-File -Append $logFile
"维护任务完成" | Out-File -Append $logFile
"=====================================" | Out-File -Append $logFile

# 可选: 发送邮件通知
# 这里可以添加邮件发送代码
# 例如使用 Send-MailMessage cmdlet
