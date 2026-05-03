@echo off
chcp 65001 >nul 2>nul
cd /d ""
set PATH=C:\Users\888\AppData\Roaming\npm;%PATH%
copy /Y "\python\scripts\launch\clause_env" ".env" >nul 2>nul
echo Starting Claude Code...
echo.
echo Model: qwen2.5-coder:7b via VCPToolBox
echo Panel: http://127.0.0.1:6006/AdminPanel/
echo.
bun --env-file=.env ./src/entrypoints/cli.tsx
