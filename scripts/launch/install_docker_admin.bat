@echo off
:: Docker Desktop 一键安装脚本
:: 请右键此文件 -> "以管理员身份运行"

echo ==============================================
echo        Docker Desktop 安装脚本
echo ==============================================
echo.

set "INSTALLER=%TEMP%\DockerDesktopInstaller.exe"

if not exist "%INSTALLER%" (
    echo 安装包不存在，请先下载
    pause
    exit /b 1
)

echo 正在安装 Docker Desktop...
echo 请耐心等待，安装过程可能需要几分钟...
echo.

"%INSTALLER%" install --accept-license

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo   Docker Desktop 安装成功！
    echo ============================================
    echo.
    echo 接下来请：
    echo 1. 启动 Docker Desktop（桌面快捷方式或开始菜单）
    echo 2. 等待 Docker 引擎启动完成
    echo 3. 运行启动脚本: \python\scripts\launch\start_multica_full.bat
    echo.
) else (
    echo.
    echo 安装失败，错误代码: %errorlevel%
    echo.
)

pause
