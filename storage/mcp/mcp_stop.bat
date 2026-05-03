@echo off
:: MCP Core 停止器
echo [Stopping] MCP Core...

:: 通过窗口标题杀
taskkill /F /FI "WINDOWTITLE eq MCP-Core-BG" >nul 2>&1

:: 通过端口杀
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":19800.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":19801.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [OK] MCP Core stopped
timeout /t 2
