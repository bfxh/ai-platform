@echo off
echo ===============================================
echo          启动 Multica（无需登录模式）
echo ===============================================
echo.

set "GO_PATH=\go126\go\bin"
set "CLAUSE_DIR="

cd /d "%CLAUSE_DIR%"

echo 1. 设置环境变量...
set PATH=%GO_PATH%;%PATH%
set GOCACHE=%LOCALAPPDATA%\go-build
set MULTICA_DEV_VERIFICATION_CODE=888888
set ALLOW_SIGNUP=true
set JWT_SECRET=dev-secret-key-12345

echo.
echo 2. 启动后端服务...
start "Multica Backend" powershell -Command "cd '%CLAUSE_DIR%\server'; go run ./cmd/server"

echo.
echo 3. 等待后端启动...
timeout /t 10 /nobreak >nul

echo.
echo 4. 启动前端服务...
start "Multica Frontend" pnpm dev:web

echo.
echo ===============================================
echo          服务启动完成！
echo ===============================================
echo.
echo 后端: http://localhost:8080
echo 前端: http://localhost:3000
echo.
echo 注意: 已绕过登录验证，无需邮箱即可使用
echo.
pause
