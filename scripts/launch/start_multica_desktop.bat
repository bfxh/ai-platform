@echo off
chcp 65001 >nul 2>&1
set "PATH=C:\Users\888\AppData\Roaming\npm;%PATH%"
set "PROJECT="

echo ===== Starting Multica Desktop =====
echo.

cd /d "%PROJECT%"
pnpm dev:desktop

