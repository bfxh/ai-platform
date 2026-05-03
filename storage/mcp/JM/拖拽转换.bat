@echo off
chcp 65001 >nul 2>&1
title 拖拽转换工具 v2.0 - 3D模型转Godot/UE5
echo.
echo   ╔══════════════════════════════════════════════╗
echo   ║   拖拽转换工具 v2.0 (core模块)              ║
echo   ║   把3D模型文件拖到这个窗口上即可转换        ║
echo   ║   支持: OBJ FBX glTF GLB DAE ABC USD STL    ║
echo   ╚══════════════════════════════════════════════╝
echo.

if "%~1"=="" (
    echo   [提示] 请把3D模型文件拖到这个bat文件上
    echo.
    echo   或者直接输入文件路径:
    set /p FILEPATH="   文件路径: "
) else (
    set "FILEPATH=%~1"
)

echo.
echo   正在转换: %FILEPATH%
echo.

cd /d \python\storage\mcp\JM
"%USERPROFILE%\AppData\Local\Programs\Python\Python310\python.exe" drag_convert.py "%FILEPATH%"

echo.
pause
