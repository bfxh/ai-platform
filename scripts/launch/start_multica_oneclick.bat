@echo off
chcp 65001 >nul
title Multica 一键启动
echo ==============================================
echo        Multica 一键启动（免登录版）
echo ==============================================
echo.

echo [1/4] 启动 Docker 和 PostgreSQL...
wsl -d Ubuntu-22.04 -- bash -c "sudo service docker start > /dev/null 2>&1 && sudo docker start multica-postgres > /dev/null 2>&1 && sleep 2 && sudo docker exec multica-postgres pg_isready -U multica -d multica" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ PostgreSQL 就绪
) else (
    echo ✗ PostgreSQL 启动失败
    pause
    exit /b 1
)

echo.
echo [2/4] 启动后端服务 (Go)...
start "Multica 后端" wsl -d Ubuntu-22.04 -- bash -c "export PATH=/usr/local/go/bin:$PATH && export GOPROXY=https://goproxy.cn,direct && export DATABASE_URL='postgres://multica:multica@localhost:5432/multica?sslmode=disable' && export JWT_SECRET='dev-secret-multica-2026' && export MULTICA_DEV_VERIFICATION_CODE='888888' && export ALLOW_SIGNUP=true && export PORT=8080 && export FRONTEND_ORIGIN='http://localhost:3002' && export MULTICA_APP_URL='http://localhost:3002' && export DEFAULT_USER_ID='8b50fa2c-a393-4a20-83fc-34580c43f85d' && cd '/mnt/d/AI CLAUDE/CLAUSE/server' && go run ./cmd/server"
echo ✓ 后端启动中 (端口 8080)

echo.
echo [3/4] 等待后端就绪...
timeout /t 15 /nobreak >nul
echo ✓ 后端就绪

echo.
echo [4/4] 启动前端服务 (Next.js)...
start "Multica 前端" cmd /c "cd /d \apps\web && npx next dev --port 3002"
echo ✓ 前端启动中 (端口 3002)

echo.
echo ==============================================
echo   Multica 已启动！
echo.
echo   打开浏览器访问: http://localhost:3002
echo   无需注册，无需登录，直接使用！
echo ==============================================
echo.

timeout /t 20 /nobreak >nul
start http://localhost:3002

exit
