# 安装 Ubuntu WSL 脚本

# 确保 WSL 2 已启用
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 下载 Ubuntu 22.04 LTS 分发版（使用官方方法）
Write-Host "Installing Ubuntu 22.04 LTS..."
wsl --install -d Ubuntu-22.04

# 等待安装完成
Start-Sleep -Seconds 10

# 检查安装状态
wsl --list --verbose

Write-Host "Ubuntu WSL installation completed!"
Write-Host "Use 'wsl' command to start Ubuntu"
