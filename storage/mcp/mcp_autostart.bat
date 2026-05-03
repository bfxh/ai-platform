@echo off
:: MCP Core 开机自启注册器
:: 运行一次即可，之后每次开机自动后台启动MCP Core

set TASK_NAME=MCP-Core-AutoStart
set SCRIPT_PATH=\python\MCP\mcp_start.bat

:: 检查是否已注册
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] 自启任务已存在: %TASK_NAME%
    echo      取消自启: schtasks /delete /tn "%TASK_NAME%" /f
    timeout /t 3
    exit /b 0
)

:: 注册开机自启任务
schtasks /create /tn "%TASK_NAME%" /tr "\"%SCRIPT_PATH%\"" /sc onlogon /rl highest /f
if %errorlevel%==0 (
    echo [OK] 已注册开机自启: %TASK_NAME%
    echo      取消自启: schtasks /delete /tn "%TASK_NAME%" /f
) else (
    echo [FAIL] 注册失败，请以管理员身份运行
)
timeout /t 3
