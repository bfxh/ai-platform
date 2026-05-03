@echo off
chcp 65001 >nul 2>nul

REM 仅启动后台服务，不启动 Claude Code TUI

REM Ollama
curl.exe -s http://127.0.0.1:11434/api/tags >nul 2>nul
if errorlevel 1 (
    start "" /MIN ollama serve
    ping -n 6 127.0.0.1 >nul
)

REM VCPToolBox API (6005)
curl.exe -s -o nul -w "%%{http_code}" http://127.0.0.1:6005/v1/models -H "Authorization: Bearer vcp-bridge-key" 2>nul | findstr "200" >nul
if errorlevel 1 (
    cd /d "\python\downloads\VCPToolBox\VCPToolBox-main"
    start "VCPToolBox-API" /MIN node server.js
    ping -n 16 127.0.0.1 >nul
)

REM VCPToolBox Admin Panel (6006)
curl.exe -s -o nul -w "%%{http_code}" http://127.0.0.1:6006/AdminPanel/login.html 2>nul | findstr "200" >nul
if errorlevel 1 (
    cd /d "\python\downloads\VCPToolBox\VCPToolBox-main"
    start "VCPToolBox-Admin" /MIN node adminServer.js
    ping -n 9 127.0.0.1 >nul
)
