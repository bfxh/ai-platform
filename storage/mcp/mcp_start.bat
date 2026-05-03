@echo off
:: MCP Core 后台启动器 - 无窗口、无UI、开机即用
:: 双击运行后MCP Core在后台运行，不占用任何可见窗口
:: 关闭方式: 运行 mcp_stop.bat 或 taskkill /F /FI "WINDOWTITLE eq MCP-Core-BG"

title MCP-Core-BG
cd /d \python\storage\mcp

:: 检查是否已在运行
netstat -aon | findstr ":19800.*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] MCP Core already running on port 19800
    echo      Web UI: http://localhost:19801
    timeout /t 3
    exit /b 0
)

:: 后台启动（最小化窗口）
echo [Starting] MCP Core...
start /min "MCP-Core-BG" python "\python\storage\mcp\mcp_core.py"

:: 等待就绪
set /a count=0
:wait_loop
timeout /t 1 /nobreak >nul
netstat -aon | findstr ":19801.*LISTENING" >nul 2>&1
if %errorlevel%==0 goto ready
set /a count+=1
if %count% geq 20 goto timeout
goto wait_loop

:ready
echo [OK] MCP Core running
echo      Coordinator: 19800
echo      Web UI: http://localhost:19801
echo      This window will close in 3 seconds...
timeout /t 3
exit /b 0

:timeout
echo [WARN] MCP Core may still be starting, check logs at \python\storage\mcp\logs\core.log
timeout /t 5
exit /b 1
