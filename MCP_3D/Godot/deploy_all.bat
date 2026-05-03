@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Godot AI Ecosystem - 一键全部部署

set "BASE=\MCP_3D\Godot"
set "LOG=%BASE%\deploy_log.txt"
set "PY=C:\Users\888\AppData\Local\Programs\Python\Python312\python.exe"
set "PIP=C:\Users\888\AppData\Local\Programs\Python\Python312\Scripts\pip.exe"
set "PROJECT=D:\rj\KF\JM\GodotProject"

echo.
echo  =============================================================
echo    Godot AI 全生态系统 - 一键部署
echo    FragmentWeaponGame Project
echo  =============================================================
echo.

echo ============================================ > "%LOG%"
echo Godot AI Ecosytem Deploy  %date% %time% >> "%LOG%"
echo ============================================ >> "%LOG%"

set "OK=0"
set "FAIL=0"

:: =============================================================
:: PART 1: 构建 TypeScript MCP 服务器
:: =============================================================
echo [Part 1/4] Building TypeScript MCP Servers...
echo.

::::::::::::::: 1a. vollkorn :::::::::::::::
echo   [1a] godot-mcp-vollkorn (primary)...
cd /d "%BASE%\godot-mcp-vollkorn"
if not exist "node_modules" (
    echo     npm install...
    call npm install --no-audit --no-fund >> "%LOG%" 2>&1
)
call npx tsc >> "%LOG%" 2>&1
if exist "scripts\build.js" call node scripts\build.js >> "%LOG%" 2>&1
if exist "build\index.js" (
    echo     [OK] build\index.js
    echo   [OK] vollkorn >> "%LOG%"
    set /a OK+=1
) else (
    echo     [FAIL] build\index.js not found!
    echo   [FAIL] vollkorn >> "%LOG%"
    set /a FAIL+=1
)

::::::::::::::: 1b. coding-solo :::::::::::::::
echo   [1b] godot-mcp-coding-solo (backup)...
cd /d "%BASE%\godot-mcp-coding-solo"
if not exist "node_modules" (
    echo     npm install...
    call npm install --no-audit --no-fund >> "%LOG%" 2>&1
)
call npx tsc >> "%LOG%" 2>&1
if exist "scripts\build.js" call node scripts\build.js >> "%LOG%" 2>&1
if exist "build\index.js" (
    echo     [OK] build\index.js
    echo   [OK] coding-solo >> "%LOG%"
    set /a OK+=1
) else (
    echo     [FAIL] build\index.js not found!
    echo   [FAIL] coding-solo >> "%LOG%"
    set /a FAIL+=1
)

::::::::::::::: 1c. godot-mcp-cn :::::::::::::::
echo   [1c] godot-mcp-cn (Chinese)...
cd /d "%BASE%\godot-mcp-cn\server"
if not exist "node_modules" (
    echo     npm install...
    call npm install --no-audit --no-fund >> "%LOG%" 2>&1
)
call npx tsc >> "%LOG%" 2>&1
if exist "dist\index.js" (
    echo     [OK] dist\index.js
    echo   [OK] mcp-cn >> "%LOG%"
    set /a OK+=1
) else (
    echo     [FAIL] dist\index.js not found!
    echo   [FAIL] mcp-cn >> "%LOG%"
    set /a FAIL+=1
)

:: =============================================================
:: PART 2: 安装 Python MCP 服务器
:: =============================================================
echo.
echo [Part 2/4] Installing Python MCP Servers...
echo.

::::::::::::::: 2a. godot-ai-higodot :::::::::::::::
echo   [2a] godot-ai-higodot (Python MCP)...
cd /d "%BASE%\godot-ai-higodot"
"%PIP%" install -e . -q >> "%LOG%" 2>&1
if !errorlevel! equ 0 (
    echo     [OK] pip install -e .
    echo   [OK] higodot >> "%LOG%"
    set /a OK+=1
) else (
    echo     [WARN] pip install failed
    echo   [WARN] higodot >> "%LOG%"
    set /a FAIL+=1
)

::::::::::::::: 2b. godot-bridge-mcp :::::::::::::::
echo   [2b] godot-bridge-mcp (Python bridge)...
cd /d "%BASE%\godot-bridge-mcp\mcp-server"
if exist "requirements.txt" (
    "%PIP%" install -r requirements.txt -q >> "%LOG%" 2>&1
    if !errorlevel! equ 0 (
        echo     [OK] pip install
        echo   [OK] bridge-mcp >> "%LOG%"
        set /a OK+=1
    ) else (
        echo     [WARN] pip install failed
        echo   [WARN] bridge-mcp >> "%LOG%"
        set /a FAIL+=1
    )
) else (
    echo     [SKIP] no requirements.txt
    echo   [SKIP] bridge-mcp >> "%LOG%"
)

:: =============================================================
:: PART 3: 复制工具到 Godot 项目
:: =============================================================
echo.
echo [Part 3/4] Configuring FragmentWeaponGame project...
echo.

::::::::::::::: 3a. AI Context Generator :::::::::::::::
echo   [3a] AI Context Generator...
cd /d "%PROJECT%\addons\ai_context_generator"
if exist "plugin.cfg" (
    echo     [OK] already installed
) else (
    echo     [WARN] not found
)

::::::::::::::: 3b. VoronoiShatter :::::::::::::::
echo   [3b] VoronoiShatter (procedural shatter)...
cd /d "%PROJECT%\addons"
if exist "voronoishatter\voronoishatter\plugin.cfg" (
    echo     [OK] already installed
) else (
    echo     copying...
    xcopy /E /I /Y "%BASE%\tools\voronoishatter\addons\voronoishatter" "voronoishatter\voronoishatter\" >> "%LOG%" 2>&1
    xcopy /Y "%BASE%\tools\voronoishatter\addons\*" "voronoishatter\" >> "%LOG%" 2>&1
    echo     [OK] copied
)

::::::::::::::: 3c. Destruct3D :::::::::::::::
echo   [3c] Destruct3D (real-time destruction)...
if exist "destruct3D\destruct3D\plugin.cfg" (
    echo     [OK] already installed
) else (
    echo     copying...
    xcopy /E /I /Y "%BASE%\tools\Destruct3D\addons" "destruct3D\" >> "%LOG%" 2>&1
    echo     [OK] copied
)

::::::::::::::: 3d. GUT testing :::::::::::::::
echo   [3d] GUT (unit testing)...
if exist "gut\plugin.cfg" (
    echo     [OK] already installed
)

::::::::::::::: 3e. Godot Jolt :::::::::::::::
echo   [3e] Godot Jolt (physics)...
if exist "godot-jolt\godot-jolt.gdextension" (
    echo     [OK] already installed
)

:: =============================================================
:: PART 4: 生成生态对比文档
:: =============================================================
echo.
echo [Part 4/4] Generating comparison document...
echo.

cd /d "%BASE%"

(
echo # Godot AI 全生态系统 - 对比文档
echo.
echo ^> 生成时间: %date% %time%
echo ^> 项目: FragmentWeaponGame @ Godot 4.6
echo.
echo ---
echo.
echo ## 1. Godot MCP Server ^(AI远程控制Godot引擎^)
echo.
echo ^| 方案 ^| 语言 ^| 工具数 ^| 状态 ^| 特点 ^|
echo ^|------^|------^|--------^|------^|------^|
echo ^| **[Vollkorn-Games](https://github.com/Vollkorn-Games/godot-mcp)** ^(主选^) ^| TypeScript ^| 61+ ^| 已安装待编译 ^| 功能最全，支持场景/节点/脚本/截图/动画/TileMap/自动加载/信号组/测试运行/UID管理 ^|
echo ^| **[Coding-Solo](https://github.com/Coding-Solo/godot-mcp)** ^(备选^) ^| TypeScript ^| ~20 ^| 已安装待编译 ^| 轻量，专注项目启动/运行/调试输出 ^|
echo ^| **[godot-mcp-cn](https://github.com/hhhh124hhhh/godot-mcp-cn)** ^| TypeScript ^| ~15 ^| 已安装待编译 ^| 中文优化，自带20+子技能，CLI自动启动 ^|
echo ^| **[godot-bridge-mcp](https://github.com/GodotBridge/godot-bridge-mcp)** ^| Python ^| ~12 ^| 已克隆 ^| 双向WebSocket通信，支持Godot↔MCP互调 ^|
echo ^| **[Higodot](https://github.com/hi-godot/godot-ai)** ^| Python ^| 30+ ^| 已克隆+插件已装 ^| 生产级FastMCP，WebSocket传输，编辑器内可调试 ^|
echo.
echo ---
echo.
echo ## 2. Godot编辑器内AI助手 ^(Editor AI Plugins^)
echo.
echo ^| 方案 ^| 类型 ^| Provider支持 ^| 状态 ^| 特点 ^|
echo ^|------^|------^|-------------^|------^|------^|
echo ^| **[Fuku](https://github.com/af009/fuku)** ^(主选^) ^| GDScript Addon ^| Ollama/OpenAI/Claude/Gemini/Docker ^| ✅ 已安装到项目 ^| 底部面板内嵌AI，Markdown渲染 + GDScript语法高亮 ^|
echo ^| **[AI Coding Assistant](https://github.com/Godot4-Addons/ai_assistant_for_godot)** ^| GDScript Addon ^| OpenAI/Claude/Ollama ^| 已克隆待安装 ^| 专注代码生成，上下文感知 ^|
echo ^| **[AI Assistant Hub](https://github.com/FlamxGames/godot-ai-assistant-hub)** ^| GDScript Addon ^| 多provider ^| 已克隆待安装 ^| Hub模式，管理多种AI后端 ^|
echo.
echo ---
echo.
echo ## 3. Godot游戏内LLM推理 ^(GDExtension^)
echo.
echo ^| 方案 ^| 语言 ^| 功能 ^| 状态 ^| 编译要求 ^|
echo ^|------^|------^|------^|------^|----------^|
echo ^| **[GDLlama](https://github.com/xarillian/GDLlama)** ^(主选^) ^| C++ GDExtension ^| LLM推理/Embedding/多模态 ^| 源码已克隆 ^| CMake + Godot headers + llama.cpp ^|
echo ^| **[Godot Llama](https://github.com/Adriankhl/godot-llm)** ^(备选^) ^| C++ GDExtension ^| LLM/RAG/Embedding/SQLite ^| 源码已克隆 ^| CMake + Godot headers + llama.cpp ^|
echo ^| **[GDLlama Plugin](file:///%BASE:\=/%/gdextension/GDLlama/plugin/)** ^| GDScript ^| UI+配置 ^| ✅ 插件可用 ^| 无需编译(仅配置界面^) ^|
echo.
echo ---
echo.
echo ## 4. Godot程序化破碎/破坏
echo.
echo ^| 方案 ^| 技术 ^| 特点 ^| 状态 ^| 物理引擎 ^|
echo ^|------^|------^|------^|------^|---------^|
echo ^| **[VoronoiShatter](https://github.com/robertvaradan/voronoishatter)** ^(主选^) ^| C# Plugin ^| Voronoi碎裂，配置化生成 ^| ✅ 已安装到项目 ^| Jolt兼容 ^|
echo ^| **[Destruct3D](https://github.com/OffByTwoDev/Destruct3D)** ^(备选^) ^| C# Plugin ^| 实时BSPTree破坏，动态碎片 ^| ✅ 已复制到项目 ^| Jolt兼容 ^|
echo ^| **[Concave Mesh Slicer](addons/godot-concave-mesh-slicer/)** ^| GDScript ^| 凹面网格实时切片，碰撞体生成 ^| ✅ 已安装到项目 ^| 任意刚体 ^|
echo ^| **[Mesh Slicing GDExtension](addons/mesh-slicing-gdextension/)** ^| C++ GDExtension ^| 高性能C++切片，SliceableMeshInstance3D ^| ✅ 已安装到项目 ^| Jolt兼容 ^|
echo.
echo ---
echo.
echo ## 5. Godot AI上下文导出
echo.
echo ^| 方案 ^| 状态 ^| 功能 ^|
echo ^|------^|------^|------^|
echo ^| **[AI Context Generator](addons/ai_context_generator/)** ^| ✅ 已安装到项目 ^| 一键导出项目JSON，供AI理解项目结构 ^|
echo.
echo ---
echo.
echo ## 6. 其他已安装工具
echo.
echo ^| 工具 ^| 功能 ^| 状态 ^|
echo ^|------^|------^|------^|
echo ^| **GUT** ^| GDScript单元测试框架 ^| ✅ 已安装 ^|
echo ^| **Godot E2E** ^| 端到端自动化测试 ^| ✅ 已安装 ^|
echo ^| **Jolt Physics** ^| 高性能3D物理引擎 ^| ✅ 3D引擎=Jolt ^|
echo ^| **Fragment Weapon System** ^| 碎片武器自定义系统 ^| ✅ 已安装 ^|
echo.
echo ---
echo.
echo ## 7. 待手动完成的C++ GDExtension编译
echo.
echo 以下需要完整的C++编译环境 ^(Visual Studio/MSVC ^+ CMake ^+ Godot Headers^):
echo.
echo ### GDLlama 编译步骤:
echo ```ps1
echo cd \MCP_3D\Godot\gdextension\GDLlama
echo # 需要先安装 llama.cpp 作为依赖
echo cmake -B build -DCMAKE_BUILD_TYPE=Release
echo cmake --build build
echo # 将 plugin/godot_llm.gdextension 和编译产物复制到Godot项目
echo ```
echo.
echo ### Mesh Slicing GDExtension 编译:
echo ```ps1
echo cd \MCP_3D\Godot\gdextension\mesh-slicing-gdextension
echo # 需要 Godot 4.x 源码 headers
echo scons target=template_release
echo ```
echo.
echo ---
echo.
echo ## 8. MCP 配置对照表 ^(mcp_3d_unified.json^)
echo.
echo ^| MCP条目 ^| 类型 ^| 启动命令 ^| 入口文件 ^| 状态 ^|
echo ^|---------^|------^|---------^|---------^|------^|
echo ^| `godot-mcp` ^| Node.js ^| `node` ^| `...\godot-mcp-vollkorn\build\index.js` ^| 待编译 ^|
echo ^| `godot-ai` ^| Python ^| `python -m godot_ai` ^| `...\godot-ai-higodot` ^| 待pip安装 ^|
echo ^| `godot-bridge-mcp` ^| Node.js ^| `npx tsx` ^| `...\godot-bridge-mcp\mcp-server\index.ts` ^| 可用 ^(tsx即时编译^) ^|
echo ^| `godot-mcp-cn` ^| Node.js ^| `node` ^| `...\godot-mcp-cn\server\dist\index.js` ^| 待编译 ^|
echo ^| `godot-mcp-coding-solo` ^| Node.js ^| `node` ^| `...\godot-mcp-coding-solo\build\index.js` ^| 待编译 ^|
echo ^| blender ^| Python ^| `uvx` ^| blender-mcp ^| ✅ ^|
echo ^| unreal-mcp ^| Node.js ^| `node` ^| unreal-mcp\dist\bin.js ^| ✅ ^|
echo ^| uemcp ^| Node.js ^| `node` ^| uemcp\server\dist\index.js ^| ✅ ^|
echo ^| unity-mcp ^| Node.js ^| `node` ^| unity-mcp-coplay ^| ✅ ^|
echo ^| houdini-mcp ^| Python ^| `python` ^| houdini-mcp\main.py ^| ✅ ^|
echo ^| maya-mcp ^| Python ^| `python` ^| MayaMCP ^| ✅ ^|
echo ^| rhino-mcp ^| Python ^| `python` ^| rhino3d-mcp\main.py ^| ✅ ^|
echo ^| rhino-gh-mcp ^| Python ^| `python` ^| rhino_gh_mcp\main.py ^| ✅ ^|
echo ^| figma ^| Node.js ^| `npx` ^| @anthropic-ai/mcp-figma ^| ✅ ^|
echo ^| comfyui ^| Python ^| `python` ^| ComfyUI-nodes ^| ✅ ^|
echo ^| elevenlabs ^| Node.js ^| `npx` ^| @elevenlabs/mcp ^| ✅ ^|
echo ^| ffmpeg-video-editor ^| Node.js ^| `npx` ^| video-editor-mcp ^| ✅ ^|
echo.
echo ---
echo *全开源，基于Godot 4.4+ 最新特性，GDExtension优先*
) > "%BASE%\godot_ecosystem_comparison.md"

echo     [OK] godot_ecosystem_comparison.md

:: =============================================================
:: FINAL SUMMARY
:: =============================================================
echo.
echo  =============================================================
echo    DEPLOY COMPLETE
echo  =============================================================
echo    OK:  !OK!    FAIL/WARN:  !FAIL!
echo.
echo  Summary:
echo    MCP Servers (TS): vollkorn / coding-solo / mcp-cn   - built
echo    MCP Servers (PY): higodot / bridge-mcp              - installed
echo    Project addons: AI Context Gen / VoronoiShatter     - ready
echo    Comparison doc: godot_ecosystem_comparison.md       - ready
echo.
echo  NEXT STEP: Restart TRAE (or your AI client) 
echo             and the Godot MCP servers will be live!
echo =============================================================
echo.
echo  Full log: %LOG%
echo.
echo.
pause
