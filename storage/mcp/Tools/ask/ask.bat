@echo off
REM Agent Skill Kit (ASK) 启动脚本

set ASK_DIR=\python\MCP\Tools\ask
set PYTHON_EXE=python

if not exist "%ASK_DIR%\ask.py" (
    echo 错误: ASK 主文件不存在
    pause
    exit /b 1
)

%PYTHON_EXE% "%ASK_DIR%\ask.py" %*

pause
