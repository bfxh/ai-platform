@echo off
chcp 65001 >nul
echo ========================================
echo D盘项目快速查询工具
echo ========================================
echo.
echo 用法:
echo   diskq godot      - 搜索godot
echo   diskq rust       - 搜索rust
echo   diskq -c ai      - 按分类筛选
echo   diskq -t python - 按技术筛选
echo   diskq --stats   - 显示统计
echo   diskq --list    - 列出所有
echo   diskq --scan    - 重新扫描
echo.
echo ========================================

set PYTHON=%SOFTWARE_DIR%\KF\JM\blender\5.1\python\bin\python.exe
set SCRIPT=\python\MCP\Tools\disk_query.py
set SCANNER=\python\MCP\Tools\disk_scanner.py

if "%1"=="" goto :eof
if "%1"=="--scan" goto scan
if "%1"=="-scan" goto scan

"%PYTHON%" "%SCRIPT%" %*

goto end

:scan
"%PYTHON%" "%SCANNER%" scan
echo.
echo 扫描完成! 请使用 diskq <关键词> 进行查询

:end
pause
