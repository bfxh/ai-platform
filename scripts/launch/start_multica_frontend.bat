@echo off
chcp 65001 >nul
echo ==============================================
echo        Multica 前端服务启动
echo ==============================================
echo.

set "CLAUSE_DIR="

cd /d "%CLAUSE_DIR%"

:: 检查 node_modules
if not exist "node_modules" (
    echo [1/2] 安装依赖...
    pnpm install
    if %errorlevel% neq 0 (
        npm install
    )
) else (
    echo [1/2] 依赖已安装
)

echo.
echo [2/2] 启动前端开发服务器...
echo   前端地址: http://localhost:3000
echo.

pnpm dev:web
if %errorlevel% neq 0 (
    npm run dev
)

pause
