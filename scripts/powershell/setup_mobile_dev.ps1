$ErrorActionPreference = "Continue"
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  TRAE 华为鸿蒙 + 苹果iOS 开发环境配置脚本" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/5] 检查 Node.js 环境..." -ForegroundColor Yellow
$nodeVersion = node -v 2>$null
if (-not $nodeVersion) {
    Write-Host "  [错误] Node.js 未安装，请先安装 Node.js 18+" -ForegroundColor Red
    exit 1
}
Write-Host "  Node.js 版本: $nodeVersion" -ForegroundColor Green

Write-Host ""
Write-Host "[2/5] 安装 TRAE 华为鸿蒙开发插件..." -ForegroundColor Yellow

Write-Host "  安装 ArkTS 语法支持插件..." -ForegroundColor White
trae --install-extension ohosvscode.arkts 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] ArkTS 插件安装成功" -ForegroundColor Green
} else {
    Write-Host "  [提示] ArkTS 插件可能需要从VSCode市场手动安装" -ForegroundColor DarkYellow
    Write-Host "  搜索: ohosvscode.arkts 或 ArkTS Language Support" -ForegroundColor DarkYellow
}

Write-Host "  安装 ArkTS 诊断插件..." -ForegroundColor White
$arktsDiagnosticUrl = "https://github.com/open-deveco/deveco-toolbox/releases/latest/download/arkts-diagnostic-0.0.1.vsix"
$arktsVsix = "$env:TEMP\arkts-diagnostic-0.0.1.vsix"
try {
    Invoke-WebRequest -Uri $arktsDiagnosticUrl -OutFile $arktsVsix -ErrorAction Stop
    trae --install-extension $arktsVsix 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] ArkTS 诊断插件安装成功" -ForegroundColor Green
    } else {
        Write-Host "  [提示] 请手动下载安装: $arktsDiagnosticUrl" -ForegroundColor DarkYellow
    }
} catch {
    Write-Host "  [提示] ArkTS 诊断插件下载失败，请手动从GitHub下载" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "[3/5] 安装 TRAE 苹果 iOS 开发插件..." -ForegroundColor Yellow

Write-Host "  安装 Swift 语言支持..." -ForegroundColor White
trae --install-extension sswg.swift-lang 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Swift 插件安装成功" -ForegroundColor Green
} else {
    Write-Host "  [提示] Swift 插件可能需要从VSCode市场手动安装" -ForegroundColor DarkYellow
}

Write-Host "  安装 SweetPad (iOS构建运行)..." -ForegroundColor White
trae --install-extension sweetpad.sweetpad 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] SweetPad 插件安装成功" -ForegroundColor Green
} else {
    Write-Host "  [提示] SweetPad 插件可能需要从VSCode市场手动安装" -ForegroundColor DarkYellow
}

Write-Host "  安装 CodeLLDB (调试支持)..." -ForegroundColor White
trae --install-extension vadimcn.vscode-lldb 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] CodeLLDB 插件安装成功" -ForegroundColor Green
} else {
    Write-Host "  [提示] CodeLLDB 插件可能需要从VSCode市场手动安装" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "[4/5] 验证 DevEco MCP Toolbox 配置..." -ForegroundColor Yellow
$mcpConfig = Get-Content "\python\mcp.json" -Raw | ConvertFrom-Json
if ($mcpConfig.mcpServers.'deveco-mcp') {
    Write-Host "  [OK] DevEco MCP Toolbox 已配置" -ForegroundColor Green
    Write-Host "  DevEco 路径: $($mcpConfig.mcpServers.'deveco-mcp'.env.DEVECO_PATH)" -ForegroundColor White
} else {
    Write-Host "  [错误] DevEco MCP 配置未找到" -ForegroundColor Red
}

Write-Host ""
Write-Host "[5/5] 检查 DevEco Studio 安装..." -ForegroundColor Yellow
$devecoPath = "%DEVECO_PATH%"
if (Test-Path "$devecoPath\bin\devecostudio64.exe") {
    Write-Host "  [OK] DevEco Studio 已安装" -ForegroundColor Green
    Write-Host "  路径: $devecoPath" -ForegroundColor White
} else {
    Write-Host "  [错误] DevEco Studio 未找到" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  安装完成! 以下是已配置的开发能力:" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  华为鸿蒙开发:" -ForegroundColor Green
Write-Host "    - DevEco MCP Toolbox (知识库/语法检查/UI分析/构建运行)" -ForegroundColor White
Write-Host "    - ArkTS 语法高亮/补全/类型提示" -ForegroundColor White
Write-Host "    - ArkTS 诊断插件 (LSP实时校验)" -ForegroundColor White
Write-Host ""
Write-Host "  苹果 iOS 开发:" -ForegroundColor Green
Write-Host "    - Swift 语言支持" -ForegroundColor White
Write-Host "    - SweetPad (Xcode项目构建运行)" -ForegroundColor White
Write-Host "    - CodeLLDB (调试支持)" -ForegroundColor White
Write-Host ""
Write-Host "  注意事项:" -ForegroundColor Yellow
Write-Host "    - iOS开发需要Mac电脑+Xcode，Windows仅支持代码编辑" -ForegroundColor DarkYellow
Write-Host "    - 华为实况窗(灵动岛)需HarmonyOS 5.0+设备" -ForegroundColor DarkYellow
Write-Host "    - 实况窗服务需在AppGallery Connect申请权益" -ForegroundColor DarkYellow
Write-Host "    - 重启TRAE后MCP工具和插件才会生效" -ForegroundColor DarkYellow
Write-Host ""
Write-Host "  如果插件安装失败，请在TRAE中手动搜索安装:" -ForegroundColor Yellow
Write-Host "    1. 打开TRAE插件市场" -ForegroundColor White
Write-Host "    2. 设置Extension Market URL为: https://marketplace.visualstudio.com/" -ForegroundColor White
Write-Host "    3. 搜索插件名称安装" -ForegroundColor White
Write-Host ""
