@echo off
title GDExtension Build Guide - GDLlama + Mesh Slicer
chcp 65001 >nul

echo.
echo  ============================================================
echo    Godot GDExtension C++ Build Guide
echo  ============================================================
echo.
echo  Prerequisites:
echo    1. Visual Studio 2022 (with C++ Desktop workload)
echo    2. CMake 3.20+
echo    3. Git (for submodules)
echo.
echo  ============================================================
echo.
echo  [1] Build GDLlama (游戏内本地LLM推理)
echo  ============================================================
echo.
echo  Step 1: Clone with submodules
echo    cd \MCP_3D\Godot\gdextension\GDLlama
echo    git submodule update --init --recursive
echo.
echo  Step 2: Configure (manual - modify CMakePresets.json if needed)
echo    cmake --preset default
echo.
echo  Step 3: Build
echo    cmake --build --preset default --config Release
echo.
echo  Step 4: Copy to project
echo    copy plugin\* D:\rj\KF\JM\GodotProject\addons\gdllama\
echo    copy build\*.dll D:\rj\KF\JM\GodotProject\addons\gdllama\
echo.
echo  ============================================================
echo.
echo  [2] Build Mesh Slicing GDExtension (高性能C++网格切片)
echo  ============================================================
echo.
echo  Note: This requires the godot-cpp bindings as a submodule.
echo.
echo  Step 1: Clone with submodules  
echo    cd \MCP_3D\Godot\gdextension\mesh-slicing-gdextension
echo    git submodule update --init --recursive
echo.
echo  Step 2: Build with SCons
echo    # 需要安装 Python + SCons
echo    pip install scons
echo    scons target=template_release
echo.
echo  Step 3: Copy to project (already has plugin structure)
echo    copy bin\*.dll D:\rj\KF\JM\GodotProject\addons\mesh-slicing-gdextension\demo\bin\
echo.
echo  ============================================================
echo.
echo  Simplest approach: Download pre-built binaries
echo  ============================================================
echo.
echo  GDLlama:    https://github.com/xarillian/GDLlama/releases
echo  Godot Llm:  https://github.com/Adriankhl/godot-llm/releases
echo.
pause
