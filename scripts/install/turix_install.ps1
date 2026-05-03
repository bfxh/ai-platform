# TuriX CUA 安装配置脚本

$InstallPath = "\python\turix-cua"

Write-Host "=== TuriX CUA 安装 ==="

# 创建目录
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force
    Write-Host "创建目录: $InstallPath"
}

# 检查 Python
$pythonPath = "$env:USERPROFILE\AppData\Local\Programs\Python\Python310\python.exe"
if (-not (Test-Path $pythonPath)) {
    Write-Host "错误: 未找到 Python，请安装 Python 3.10+"
    exit 1
}
Write-Host "找到 Python: $pythonPath"

# 创建虚拟环境
$venvPath = "$InstallPath\venv"
if (-not (Test-Path $venvPath)) {
    & $pythonPath -m venv $venvPath
    Write-Host "创建虚拟环境"
}

# 安装依赖
$pipExe = "$venvPath\Scripts\pip.exe"
if (Test-Path $pipExe) {
    Write-Host "安装依赖..."
    & $pipExe install pywin32 pyautogui opencv-python numpy pillow requests beautifulsoup4
    & $pipExe install openai langchain langchain-core langchain-community
    Write-Host "依赖安装完成"
}

# 克隆仓库
$repoPath = "$InstallPath\TuriX-CUA"
if (-not (Test-Path $repoPath)) {
    Write-Host "克隆仓库..."
    git clone https://github.com/TurixAI/TuriX-CUA.git $repoPath
    Set-Location $repoPath
    git checkout multi-agent-windows
}

# 创建配置文件目录
New-Item -ItemType Directory -Path "$repoPath\examples" -Force | Out-Null

Write-Host "安装完成！路径: $InstallPath"
