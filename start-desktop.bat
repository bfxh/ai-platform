@echo off
chcp 65001 >nul 2>&1
set "PATH=C:\Users\888\AppData\Roaming\npm;%PATH%"
set "PROJECT=%~dp0"
set "PROJECT=%PROJECT:~0,-1%"

echo ============================================
echo    Multica Desktop 启动
echo ============================================
echo.

cd /d "%PROJECT%"
pnpm dev:desktop
