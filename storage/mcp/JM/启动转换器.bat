@echo off
chcp 65001 >nul 2>&1
title 引擎资产转换器 v2.1
echo.
echo   ========================================
echo     引擎资产转换器 v2.1 - 启动中...
echo   ========================================
echo.
cd /d \python\storage\mcp\JM
"%USERPROFILE%\AppData\Local\Programs\Python\Python310\python.exe" engine_converter_ui.py
if %errorlevel% neq 0 (
    echo.
    echo   [ERROR] 启动失败，尝试用 python3...
    python3 engine_converter_ui.py
    if %errorlevel% neq 0 (
        echo.
        echo   [ERROR] python3 也失败了，尝试用 python...
        python engine_converter_ui.py
    )
)
echo.
pause
