@echo off
chcp 65001 >nul 2>&1
set "PATH=C:\Users\888\AppData\Roaming\npm;%PATH%"
set "PROJECT="

echo ===== Starting Multica Web =====
echo.

echo Starting backend (Go server)...
start "Multica Backend" cmd /k "cd /d %PROJECT%\server && go run ./cmd/server"

timeout /t 3 /nobreak >nul

echo Starting frontend (Next.js)...
start "Multica Frontend" cmd /k "cd /d %PROJECT% && pnpm dev:web"

echo.
echo ===== Services Started =====
echo   Backend:  http://localhost:8080
echo   Frontend: http://localhost:3000
echo   Login code: 888888
echo.
