@echo off
chcp 65001 >nul
echo MCP Core 启动脚本
echo ================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请安装 Python 3.8+
    exit /b 1
)

REM 切换到工作目录
cd /d "\python\MCP_Core"

REM 自动启动GStack技能管理系统
echo [INFO] 启动GStack技能管理系统初始化...
python gstack_init.py
echo.

REM 显示菜单
echo 请选择操作:
echo   1. 启动 MCP Server
echo   2. 列出技能
echo   3. 列出工作流
echo   4. 查看状态
echo   5. 运行测试
echo   6. 安装新技能
echo   7. 退出
echo.

set /p choice="输入选项 (1-7): "

if "%choice%"=="1" goto start_server
if "%choice%"=="2" goto list_skills
if "%choice%"=="3" goto list_workflows
if "%choice%"=="4" goto status
if "%choice%"=="5" goto run_tests
if "%choice%"=="6" goto install_skill
if "%choice%"=="7" goto exit

echo [错误] 无效选项
goto end

:start_server
echo 启动 MCP Server...
python server.py
goto end

:list_skills
echo 列出技能...
python cli.py skill list -v
goto end

:list_workflows
echo 列出工作流...
python cli.py workflow list
goto end

:status
echo 查看状态...
python cli.py status
goto end

:run_tests
echo 运行测试...
cd tests
python run_tests.py -v
cd ..
goto end

:install_skill
echo 安装新技能...
set /p skill_name="技能名称: "
set /p skill_desc="技能描述: "
python skill_installer.py create %skill_name% --description "%skill_desc%"
echo.
echo 是否立即注册？(Y/N)
set /p register=""
if /i "%register%"=="Y" (
    python skill_installer.py register %skill_name%
)
goto end

:exit
echo 再见!

:end
pause
