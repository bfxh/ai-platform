@echo off
chcp 65001 >nul
echo ============================================
echo   局域网共享配置
echo   让笔记本和台式机互相访问文件
echo ============================================
echo.

set SHARED_DIR=\python\projects\3d-pipeline\shared

if not exist "%SHARED_DIR%" mkdir "%SHARED_DIR%"

echo 检测本机IP地址...
ipconfig | findstr /i "IPv4"
echo.

echo ===== 配置Windows文件共享 =====
echo.
echo 方式1: Windows文件夹共享 (推荐)
echo.
echo 步骤1: 共享文件夹
echo   右键点击 \python\projects\3d-pipeline\shared
echo   → 属性 → 共享 → 高级共享
echo   → 勾选"共享此文件夹"
echo   → 权限 → 添加 Everyone → 完全控制
echo.
echo 步骤2: 在另一台电脑上访问
echo   打开文件资源管理器
echo   地址栏输入: \\本机IP\shared
echo.

echo 正在自动配置共享...
net share shared="%SHARED_DIR%" /grant:Everyone,FULL 2>nul
if %ERRORLEVEL% EQU 0 (
    echo 共享创建成功!
) else (
    echo 需要管理员权限, 请右键以管理员身份运行此脚本
    echo 或手动配置共享
)
echo.

echo ===== 防火墙规则 =====
echo 添加防火墙入站规则允许文件共享...
netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes 2>nul
echo.

echo ===== 方式2: Python简易HTTP服务器 =====
echo 如果Windows共享不工作, 可以用Python启动HTTP服务器
echo.
echo 在数据所在电脑上运行:
echo   cd \python\projects\3d-pipeline\shared
echo   python -m http.server 8888
echo.
echo 在另一台电脑浏览器访问:
echo   http://对方IP:8888
echo.

echo ===== 方式3: SCP/SSH传输 =====
echo 如果两台电脑都安装了OpenSSH:
echo   发送: scp -r \python\projects\3d-pipeline\shared 用户名@对方IP:D:\data\
echo   接收: scp -r 用户名@对方IP:D:\data\3d-pipeline \python\projects\
echo.

echo ===== 网络检测 =====
echo.
echo 请确保两台电脑在同一局域网:
echo   1. 连接同一个WiFi路由器
echo   2. 或用网线直连 (需设置静态IP)
echo.
echo 测试连通性:
echo   ping 对方IP
echo.

echo 获取本机IP:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    echo   %%a
)
echo.

echo ============================================
echo   共享配置完成!
echo ============================================
echo.
echo 共享目录: %SHARED_DIR%
echo 在另一台电脑访问: \\本机IP\shared
echo.
pause
