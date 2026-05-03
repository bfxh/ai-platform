@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "BASE=\MCP_3D\Godot"
set "LOG=%BASE%\build_log.txt"
set "PY=C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe"
set "PIP=C:\Users\888\AppData\Local\Programs\Python\Python312\Scripts\pip.exe"

echo ============================================ > "%LOG%"
echo Godot MCP Server 全构建开始  %date% %time% >> "%LOG%"
echo ============================================ >> "%LOG%"

:: ===== 1. godot-mcp-vollkorn (主选) =====
echo.
echo [1/5] 构建 godot-mcp-vollkorn ...
echo [1/5] godot-mcp-vollkorn >> "%LOG%"
cd /d "%BASE%\godot-mcp-vollkorn"

if not exist "node_modules" (
    echo   安装依赖 (npm install)...
    echo   npm install >> "%LOG%"
    call npm install --no-audit --no-fund >> "%LOG%" 2>&1
)

echo   编译 TypeScript...
echo   tsc >> "%LOG%"
call npx tsc >> "%LOG%" 2>&1
if exist "scripts\build.js" (
    call node scripts\build.js >> "%LOG%" 2>&1
)

if exist "build\index.js" (
    echo   [OK] build\index.js 已生成
    echo   [OK] build\index.js >> "%LOG%"
) else (
    echo   [FAIL] build\index.js 不存在！
    echo   [FAIL] build\index.js >> "%LOG%"
)

:: ===== 2. godot-mcp-coding-solo (备选) =====
echo.
echo [2/5] 构建 godot-mcp-coding-solo ...
echo [2/5] godot-mcp-coding-solo >> "%LOG%"
cd /d "%BASE%\godot-mcp-coding-solo"

if not exist "node_modules" (
    echo   安装依赖 (npm install)...
    call npm install --no-audit --no-fund >> "%LOG%" 2>&1
)

echo   编译 TypeScript...
call npx tsc >> "%LOG%" 2>&1
if exist "scripts\build.js" (
    call node scripts\build.js >> "%LOG%" 2>&1
)

if exist "build\index.js" (
    echo   [OK] build\index.js 已生成
    echo   [OK] build\index.js >> "%LOG%"
) else (
    echo   [FAIL] build\index.js 不存在！
    echo   [FAIL] build\index.js >> "%LOG%"
)

:: ===== 3. godot-mcp-cn =====
echo.
echo [3/5] 构建 godot-mcp-cn ...
echo [3/5] godot-mcp-cn >> "%LOG%"
cd /d "%BASE%\godot-mcp-cn\server"

if not exist "node_modules" (
    echo   安装依赖 (npm install)...
    call npm install --no-audit --no-fund >> "%LOG%" 2>&1
)

echo   编译 TypeScript...
call npx tsc >> "%LOG%" 2>&1

if exist "dist\index.js" (
    echo   [OK] server\dist\index.js 已生成
    echo   [OK] dist\index.js >> "%LOG%"
) else (
    echo   [FAIL] server\dist\index.js 不存在！
    echo   [FAIL] dist\index.js >> "%LOG%"
)

:: ===== 4. godot-bridge-mcp =====
echo.
echo [4/5] 安装 godot-bridge-mcp ...
echo [4/5] godot-bridge-mcp >> "%LOG%"
cd /d "%BASE%\godot-bridge-mcp\mcp-server"

if exist "requirements.txt" (
    echo   安装 Python 依赖...
    "%PIP%" install -r requirements.txt -q >> "%LOG%" 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] Python 依赖已安装
        echo   [OK] Python deps >> "%LOG%"
    ) else (
        echo   [WARN] pip 安装可能有误
        echo   [WARN] pip failed >> "%LOG%"
    )
) else (
    echo   [SKIP] 无 requirements.txt
    echo   [SKIP] no requirements.txt >> "%LOG%"
)

:: ===== 5. godot-ai-higodot =====
echo.
echo [5/5] 安装 godot-ai-higodot ...
echo [5/5] godot-ai-higodot >> "%LOG%"
cd /d "%BASE%\godot-ai-higodot"

echo   安装 Python 包 (pip install -e)...
"%PIP%" install -e . -q >> "%LOG%" 2>&1
if !errorlevel! equ 0 (
    echo   [OK] godot-ai-higodot 已安装
    echo   [OK] pip install -e >> "%LOG%"
) else (
    echo   [WARN] 安装可能有误
    echo   [WARN] pip install -e failed >> "%LOG%"
)

:: ===== 验证 =====
echo.
echo ============================================
echo   验证构建结果
echo ============================================

set "ALL_OK=1"

if exist "%BASE%\godot-mcp-vollkorn\build\index.js" (
    echo   [OK] godot-mcp-vollkorn
) else (
    echo   [MISS] godot-mcp-vollkorn
    set "ALL_OK=0"
)

if exist "%BASE%\godot-mcp-coding-solo\build\index.js" (
    echo   [OK] godot-mcp-coding-solo
) else (
    echo   [MISS] godot-mcp-coding-solo
    set "ALL_OK=0"
)

if exist "%BASE%\godot-mcp-cn\server\dist\index.js" (
    echo   [OK] godot-mcp-cn
) else (
    echo   [MISS] godot-mcp-cn
    set "ALL_OK=0"
)

echo.
echo ============================================
if "!ALL_OK!"=="1" (
    echo   全部构建成功！可以重启 TRAE 使用了。
) else (
    echo   部分构建失败，查看 build_log.txt 了解详情。
)
echo ============================================
echo.
echo 日志文件: %LOG%
echo.
pause
