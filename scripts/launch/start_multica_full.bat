@echo off
chcp 65001 >nul
echo ==============================================
echo        Multica 完整服务启动脚本
echo ==============================================
echo.

set "CLAUSE_DIR="

:: 添加 Docker 到 PATH
set "DOCKER_PATH=C:\Program Files\Docker\Docker\resources\bin"
if exist "%DOCKER_PATH%" (
    set "PATH=%PATH%;%DOCKER_PATH%"
)

:: 检查 Docker
echo [1/7] 检查 Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Docker 未安装或未启动
    echo   请先安装 Docker Desktop 并启动
    echo   安装脚本: \python\scripts\launch\install_docker_admin.bat
    echo   或手动安装: 双击 %TEMP%\DockerDesktopInstaller.exe
    pause
    exit /b 1
)
echo ✓ Docker 已就绪

:: 检查 Docker 引擎
echo.
echo [2/7] 检查 Docker 引擎...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Docker 引擎未运行
    echo   请启动 Docker Desktop 后重试
    pause
    exit /b 1
)
echo ✓ Docker 引擎运行中

:: 创建 .env 文件
echo.
echo [3/7] 配置环境变量...
cd /d "%CLAUSE_DIR%"
if not exist ".env" (
    copy .env.example .env
    echo ✓ 已创建 .env 文件
) else (
    echo ✓ .env 文件已存在
)

:: 启动 PostgreSQL
echo.
echo [4/7] 启动 PostgreSQL 容器...
docker compose up -d postgres
if %errorlevel% equ 0 (
    echo ✓ PostgreSQL 容器启动成功
) else (
    echo ✗ PostgreSQL 启动失败，尝试重启...
    docker restart multica-postgres-1 2>nul
    docker compose -f docker-compose.yml up -d postgres
)

:: 等待 PostgreSQL
echo.
echo [5/7] 等待 PostgreSQL 就绪...
timeout /t 15 /nobreak >nul
echo ✓ PostgreSQL 就绪

:: 数据库迁移
echo.
echo [6/7] 运行数据库迁移...
cd /d "%CLAUSE_DIR%\server"
set DATABASE_URL=postgres://multica:multica@localhost:5432/multica?sslmode=disable
set JWT_SECRET=dev-secret-change-me
set MULTICA_DEV_VERIFICATION_CODE=888888
set ALLOW_SIGNUP=true
go run ./cmd/migrate up
if %errorlevel% equ 0 (
    echo ✓ 数据库迁移成功
) else (
    echo ✗ 数据库迁移失败
    pause
    exit /b 1
)

:: 启动后端
echo.
echo [7/7] 启动后端服务...
echo.
echo ==============================================
echo   Multica 服务已启动！
echo   后端: http://localhost:8080
echo   前端: 需要另开终端运行 npm run dev
echo ==============================================
echo.
go run ./cmd/server

pause
