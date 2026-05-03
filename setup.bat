@echo off
chcp 65001 >nul 2>&1
set "PATH=C:\Users\888\AppData\Roaming\npm;%PATH%"
set "PROJECT=%~dp0"
set "PROJECT=%PROJECT:~0,-1%"

echo ============================================
echo    Multica 一键安装配置
echo ============================================
echo.

:: Step 1: .env
echo [1/6] 配置 .env 文件...
if not exist "%PROJECT%\.env" (
    copy "%PROJECT%\.env.example" "%PROJECT%\.env" >nul
    echo   已创建 .env，开发验证码: 888888
) else (
    echo   .env 已存在，跳过
)

:: Step 2: pnpm install
echo.
echo [2/6] 安装前端依赖...
cd /d "%PROJECT%"
call pnpm install
echo   前端依赖安装完成

:: Step 3: Go
echo.
echo [3/6] 检查 Go...
where go >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    go version
    echo   Go 已就绪
) else (
    echo   Go 未安装！请下载安装:
    echo   国内: https://studygolang.com/dl
    echo   官方: https://go.dev/dl/go1.24.3.windows-amd64.msi
)

:: Step 4: Docker
echo.
echo [4/6] 检查 Docker...
where docker >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    docker --version
    echo   Docker 已就绪
) else (
    echo   Docker 未安装！请下载安装:
    echo   国内: https://mirrors.aliyun.com/docker-toolbox/
    echo   官方: https://desktop.docker.com/win/main/amd64/Docker%%20Desktop%%20Installer.exe
)

:: Step 5: PostgreSQL
echo.
echo [5/6] 启动 PostgreSQL...
where docker >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    cd /d "%PROJECT%"
    docker compose up -d postgres
    timeout /t 5 /nobreak >nul
    echo   PostgreSQL 已启动
) else (
    echo   跳过 (Docker 不可用)
)

:: Step 6: Migrations
echo.
echo [6/6] 运行数据库迁移...
where go >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    cd /d "%PROJECT%\server"
    go run ./cmd/migrate up
    echo   迁移完成
) else (
    echo   跳过 (Go 不可用)
)

echo.
echo ============================================
echo    配置完成！双击 start-web.bat 或 start-desktop.bat 启动
echo ============================================
pause
