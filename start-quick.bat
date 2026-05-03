@echo off
echo ===============================================
echo          Multica 快速启动脚本
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
set DATABASE_URL=postgres://multica:multica@localhost:5432/multica?sslmode=disable

echo.
echo 2. 启动 PostgreSQL...
docker run -d --name multica-postgres -e POSTGRES_DB=multica -e POSTGRES_USER=multica -e POSTGRES_PASSWORD=multica -p 5432:5432 postgres:16

echo 等待数据库启动...
timeout /t 15 /nobreak >nul

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
echo.
echo 注意: 已绕过登录验证，无需邮箱即可使用
echo.
pause
