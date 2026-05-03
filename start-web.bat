@echo off
chcp 65001 >nul 2>&1
set "PATH=C:\Users\888\AppData\Roaming\npm;%PATH%"
set "PROJECT=%~dp0"
set "PROJECT=%PROJECT:~0,-1%"

echo ============================================
echo    Multica Web 启动
echo ============================================
echo.

:: Start backend
echo 启动后端 (Go server)...
start "Multica Backend" cmd /k "cd /d %PROJECT%\server && go run ./cmd/server"

timeout /t 3 /nobreak >nul

:: Start frontend
echo 启动前端 (Next.js)...
start "Multica Frontend" cmd /k "cd /d %PROJECT% && pnpm dev:web"

echo.
echo ============================================
echo    服务已启动！
echo ============================================
echo   前端: http://localhost:3000
echo   后端: http://localhost:8080
echo   登录验证码: 888888
echo.
