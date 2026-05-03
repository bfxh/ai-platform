@echo off
chcp 65001 >nul

echo ========================================
echo   GStackCore - GitHub智能助手
echo ========================================
echo.

cd /d "%~dp0"

echo [1] 启动Web界面 (http://localhost:8000)
echo [2] 运行测试
echo [3] 查看帮助
echo.
set /p choice="请选择 (1-3): "

if "%choice%"=="1" goto web
if "%choice%"=="2" goto test
if "%choice%"=="3" goto help

:web
echo.
echo 启动Web界面...
python web_ui.py
goto end

:test
echo.
echo 运行测试...
python -c "from gstack_core import GStackCore; c = GStackCore(); print('✅ GStackCore 初始化成功'); r = c.execute('get_user', {'username': 'octocat'}); print('✅ get_user 测试成功' if r.get('success') else '❌ get_user 测试失败'); r = c.execute('search_repos', {'query': 'python', 'limit': 3}); print('✅ search_repos 测试成功' if r.get('success') else '❌ search_repos 测试失败')"
goto end

:help
echo.
echo GStackCore 使用帮助:
echo.
echo 1. 启动Web界面后，在浏览器中访问 http://localhost:8000
echo 2. 可以查询用户、仓库、搜索仓库、分析仓库等
echo 3. 所有操作都会自动重试和缓存
echo.
echo 或者直接使用Python API:
echo   from gstack_core import GStackCore
echo   core = GStackCore()
echo   result = core.execute('get_user', {'username': 'octocat'})
echo.
:end
pause
