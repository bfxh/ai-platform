@echo off
echo ===============================================
echo          启动 Multica 完整服务
echo ===============================================
echo.

set "GO_PATH=\go126\go\bin"
set "CLAUSE_DIR="

cd /d "%CLAUSE_DIR%"

echo 1. 启动 PostgreSQL (Docker)...
docker run -d --name multica-postgres -e POSTGRES_DB=multica -e POSTGRES_USER=multica -e POSTGRES_PASSWORD=multica -p 5432:5432 postgres:16

echo 等待数据库启动...
timeout /t 15 /nobreak >nul

echo.
echo 2. 设置环境变量...
set PATH=%GO_PATH%;%PATH%
set GOCACHE=%LOCALAPPDATA%\go-build
set MULTICA_DEV_VERIFICATION_CODE=888888
set ALLOW_SIGNUP=true

echo.
echo 3. 运行数据库迁移...
cd server
go run ./cmd/migrate up

echo.
echo 4. 启动后端服务...
start "Multica Backend" go run ./cmd/server

echo.
echo 5. 启动前端服务...
cd ..
start "Multica Frontend" pnpm dev:web

echo.
echo ===============================================
echo          服务启动完成！
echo ===============================================
echo.
echo 后端: http://localhost:8080
echo 前端: http://localhost:3000
echo 登录方式: 任意邮箱 + 验证码 888888
echo.
pause
