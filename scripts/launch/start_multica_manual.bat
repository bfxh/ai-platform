@echo off
chcp 65001 >nul
echo ==============================================
echo        Multica 服务启动脚本 (手动模式)
echo ==============================================
echo.

set "CLAUSE_DIR="
set "POSTGRES_DB=multica"
set "POSTGRES_USER=multica"
set "POSTGRES_PASSWORD=multica"

echo [1/5] 检查 Docker 是否已安装...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Docker 已安装
) else (
    echo ✗ Docker 未安装
    echo   请先安装 Docker Desktop:
    echo   1. 访问 https://www.docker.com/products/docker-desktop/
    echo   2. 下载并安装 Docker Desktop
    echo   3. 启动 Docker Desktop
    echo   4. 重新运行此脚本
    pause
    exit /b 1
)

echo.
echo [2/5] 启动 PostgreSQL 容器...
cd /d "%CLAUSE_DIR%"
docker compose up -d postgres
if %errorlevel% equ 0 (
    echo ✓ PostgreSQL 容器启动成功
) else (
    echo ✗ PostgreSQL 容器启动失败
    pause
    exit /b 1
)

echo.
echo [3/5] 等待 PostgreSQL 启动...
timeout /t 15 /nobreak >nul

echo.
echo [4/5] 设置环境变量并运行数据库迁移...
set DATABASE_URL=postgres://%POSTGRES_USER%:%POSTGRES_PASSWORD%@localhost:5432/%POSTGRES_DB%?sslmode=disable
cd /d "%CLAUSE_DIR%\server"
go run ./cmd/migrate up
if %errorlevel% equ 0 (
    echo ✓ 数据库迁移成功
) else (
    echo ✗ 数据库迁移失败
    pause
    exit /b 1
)

echo.
echo [5/5] 启动后端服务...
echo 后端服务将在 http://localhost:8080 运行
go run ./cmd/server

pause
