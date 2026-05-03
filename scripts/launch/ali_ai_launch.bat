@echo off
chcp 65001 >nul 2>&1
title 阿里 AI 生态 - 一键启动
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║           阿里 AI 生态 - 全项目一键启动                  ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

:MENU
echo ┌─────────────────────────────────────────────────────────┐
echo │  [1] 启动 Qoder (阿里云 AI IDE)                         │
echo │  [2] 启动 QClaw (AI 网关 + 技能平台)                     │
echo │  [3] 启动 Ollama + Qwen 模型                            │
echo │  [4] 启动全部 (Qoder + QClaw + Ollama)                   │
echo │  ─────────────────────────────────────────────────────  │
echo │  [5] 拉取更多 Qwen 模型                                  │
echo │  [6] 配置 QClaw 微信机器人                               │
echo │  [7] 配置 QClaw QQ 机器人                                │
echo │  [8] 配置 QClaw 钉钉连接器                               │
echo │  ─────────────────────────────────────────────────────  │
echo │  [9] 初始化 self-improving 记忆系统                      │
echo │  [A] 安装 bdpan 百度网盘 CLI                             │
echo │  [B] 配置 kdocs 金山文档 Token                           │
echo │  ─────────────────────────────────────────────────────  │
echo │  [0] 退出                                                │
echo └─────────────────────────────────────────────────────────┘
echo.

set /p choice=请选择操作:

if "%choice%"=="1" goto START_QODER
if "%choice%"=="2" goto START_QCLAW
if "%choice%"=="3" goto START_OLLAMA
if "%choice%"=="4" goto START_ALL
if "%choice%"=="5" goto PULL_MODELS
if "%choice%"=="6" goto CONFIG_WECHAT
if "%choice%"=="7" goto CONFIG_QQBOT
if "%choice%"=="8" goto CONFIG_DINGTALK
if "%choice%"=="9" goto INIT_SELF_IMPROVING
if /i "%choice%"=="A" goto INSTALL_BDPAN
if /i "%choice%"=="B" goto CONFIG_KDOCS
if "%choice%"=="0" goto END
goto MENU

:START_QODER
echo.
echo [启动] Qoder - 阿里云 AI IDE...
start "" "%SOFTWARE_DIR%\AI\Qoder\Qoder.exe"
echo [完成] Qoder 已启动！
echo.
pause
goto MENU

:START_QCLAW
echo.
echo [启动] QClaw - AI 网关 + 技能平台...
start "" "%SOFTWARE_DIR%\AI\QClaw\QClaw.exe"
echo [完成] QClaw 已启动！
echo.
pause
goto MENU

:START_OLLAMA
echo.
echo [启动] Ollama 服务...
set OLLAMA_MODELS=%OLLAMA_DIR%\.ollama\models
start "Ollama Server" /MIN "%OLLAMA_DIR%\ollama.exe" serve
timeout /t 3 /nobreak >nul
echo [当前模型列表:]
"%OLLAMA_DIR%\ollama.exe" list
echo.
echo [完成] Ollama 已启动！
echo.
pause
goto MENU

:START_ALL
echo.
echo [启动] 全部服务...
echo.
echo [1/3] 启动 Ollama...
set OLLAMA_MODELS=%OLLAMA_DIR%\.ollama\models
start "Ollama Server" /MIN "%OLLAMA_DIR%\ollama.exe" serve
timeout /t 3 /nobreak >nul
echo [完成] Ollama 已启动
echo.
echo [2/3] 启动 QClaw...
start "" "%SOFTWARE_DIR%\AI\QClaw\QClaw.exe"
echo [完成] QClaw 已启动
echo.
echo [3/3] 启动 Qoder...
start "" "%SOFTWARE_DIR%\AI\Qoder\Qoder.exe"
echo [完成] Qoder 已启动
echo.
echo ══════════════════════════════════════════════════════════
echo   全部服务已启动！
echo   - Ollama: 本地模型服务 (qwen2.5-coder:7b)
echo   - QClaw:  AI 网关 (微信/QQ/钉钉/飞书)
echo   - Qoder:  阿里云 AI IDE (通义灵码)
echo ══════════════════════════════════════════════════════════
echo.
pause
goto MENU

:PULL_MODELS
echo.
echo ┌─────────────────────────────────────────────────────────┐
echo │  可拉取的 Qwen 模型:                                     │
echo │  [1] qwen2.5-coder:7b      (4.7GB, 代码生成)           │
echo │  [2] qwen2.5:7b             (4.7GB, 通用对话)           │
echo │  [3] qwen2.5:14b            (9GB, 高质量对话)           │
echo │  [4] qwen2.5-coder:14b      (9GB, 高质量代码)           │
echo │  [5] qwen2.5:32b            (20GB, 专业级对话)          │
echo │  [6] qwen2.5-coder:32b      (20GB, 专业级代码)          │
echo │  [7] qwen3:8b               (5GB, 最新推理模型)         │
echo │  [8] qwen3:14b              (9GB, 最新推理模型)         │
echo │  [0] 返回主菜单                                         │
echo └─────────────────────────────────────────────────────────┘
echo.
set /p model_choice=请选择要拉取的模型:

if "%model_choice%"=="1" set MODEL=qwen2.5-coder:7b
if "%model_choice%"=="2" set MODEL=qwen2.5:7b
if "%model_choice%"=="3" set MODEL=qwen2.5:14b
if "%model_choice%"=="4" set MODEL=qwen2.5-coder:14b
if "%model_choice%"=="5" set MODEL=qwen2.5:32b
if "%model_choice%"=="6" set MODEL=qwen2.5-coder:32b
if "%model_choice%"=="7" set MODEL=qwen3:8b
if "%model_choice%"=="8" set MODEL=qwen3:14b
if "%model_choice%"=="0" goto MENU

if defined MODEL (
    echo.
    echo [拉取] %MODEL% ...
    set OLLAMA_MODELS=%OLLAMA_DIR%\.ollama\models
    "%OLLAMA_DIR%\ollama.exe" pull %MODEL%
    echo [完成] %MODEL% 拉取完毕！
) else (
    echo [错误] 无效选择
)
echo.
pause
goto MENU

:CONFIG_WECHAT
echo.
echo ══════════════════════════════════════════════════════════
echo   配置 QClaw 微信机器人
echo ══════════════════════════════════════════════════════════
echo.
echo 步骤:
echo   1. 确保 QClaw 已启动
echo   2. 在 QClaw 中打开终端/命令行
echo   3. 运行: openclaw plugins install "@tencent-weixin/openclaw-weixin"
echo   4. 运行: openclaw config set plugins.entries.openclaw-weixin.enabled true
echo   5. 运行: openclaw channels login --channel openclaw-weixin
echo   6. 用手机微信扫码授权
echo   7. 运行: openclaw gateway restart
echo.
echo 多账号隔离:
echo   openclaw config set agents.mode per-channel-per-peer
echo.
pause
goto MENU

:CONFIG_QQBOT
echo.
echo ══════════════════════════════════════════════════════════
echo   配置 QClaw QQ 机器人
echo ══════════════════════════════════════════════════════════
echo.
echo 步骤:
echo   1. 在 QQ 开放平台 (bot.q.qq.com) 创建机器人
echo   2. 获取 AppID 和 Token
echo   3. 在 QClaw 中配置 QQ Bot 插件
echo   4. 支持: 私聊、群聊@、富媒体、语音STT/TTS
echo   5. 热更新: 私聊发送 /bot-upgrade
echo.
echo 功能:
echo   - C2C 私聊 / 群聊 @消息
echo   - 图片/语音/视频/文件收发
echo   - 语音转文字 + 文字转语音
echo   - 定时推送 / URL 发送 / Markdown
echo   - 命令执行审批 (按钮确认)
echo.
pause
goto MENU

:CONFIG_DINGTALK
echo.
echo ══════════════════════════════════════════════════════════
echo   配置 QClaw 钉钉连接器
echo ══════════════════════════════════════════════════════════
echo.
echo 步骤:
echo   1. 在钉钉开放平台创建机器人
echo   2. 获取 Client ID 和 Client Secret
echo   3. 在 QClaw 中配置 dingtalk-connector 插件
echo   4. 支持: AI Card 流式输出、文档解析
echo.
echo 依赖:
echo   - dingtalk-stream ^2.1.4
echo   - ffmpeg (语音处理)
echo   - mammoth (Word 文档解析)
echo   - pdf-parse (PDF 解析)
echo.
pause
goto MENU

:INIT_SELF_IMPROVING
echo.
echo [初始化] self-improving 自我改进记忆系统...
set SI_DIR=%USERPROFILE%\self-improving
if not exist "%SI_DIR%" mkdir "%SI_DIR%"
if not exist "%SI_DIR%\projects" mkdir "%SI_DIR%\projects"
if not exist "%SI_DIR%\domains" mkdir "%SI_DIR%\domains"
if not exist "%SI_DIR%\archive" mkdir "%SI_DIR%\archive"

if not exist "%SI_DIR%\memory.md" (
echo # HOT Memory - Always Loaded ^(%%^) > "%SI_DIR%\memory.md"
echo. >> "%SI_DIR%\memory.md"
echo ## Confirmed Preferences >> "%SI_DIR%\memory.md"
echo. >> "%SI_DIR%\memory.md"
echo ## Active Patterns >> "%SI_DIR%\memory.md"
echo [创建] memory.md
)

if not exist "%SI_DIR%\corrections.md" (
echo # Corrections Log >> "%SI_DIR%\corrections.md"
echo. >> "%SI_DIR%\corrections.md"
echo ## Recent Corrections >> "%SI_DIR%\corrections.md"
echo [创建] corrections.md
)

if not exist "%SI_DIR%\index.md" (
echo # Topic Index >> "%SI_DIR%\index.md"
echo. >> "%SI_DIR%\index.md"
echo ## Projects >> "%SI_DIR%\index.md"
echo ## Domains >> "%SI_DIR%\index.md"
echo [创建] index.md
)

if not exist "%SI_DIR%\heartbeat-state.md" (
echo # Heartbeat State >> "%SI_DIR%\heartbeat-state.md"
echo. >> "%SI_DIR%\heartbeat-state.md"
echo last_run: never >> "%SI_DIR%\heartbeat-state.md"
echo reviewed_change: none >> "%SI_DIR%\heartbeat-state.md"
echo action_notes: "" >> "%SI_DIR%\heartbeat-state.md"
echo [创建] heartbeat-state.md
)

echo.
echo [完成] self-improving 记忆系统已初始化！
echo   目录: %SI_DIR%\
echo   - memory.md (HOT: 始终加载)
echo   - corrections.md (纠正日志)
echo   - index.md (主题索引)
echo   - heartbeat-state.md (心跳状态)
echo   - projects/ (项目级记忆)
echo   - domains/ (领域级记忆)
echo   - archive/ (冷存储)
echo.
pause
goto MENU

:INSTALL_BDPAN
echo.
echo [安装] 百度网盘 CLI (bdpan)...
echo.
echo 注意: 安装需要从百度 CDN 下载，将自动校验 SHA256
echo.
bash "%SOFTWARE_DIR%\AI\QClaw\resources\openclaw\config\skills\bdpan-storage\scripts\install.sh" --yes
echo.
echo [完成] bdpan 安装完毕！
echo   登录: bash @skills/bdpan-storage/scripts/login.sh
echo.
pause
goto MENU

:CONFIG_KDOCS
echo.
echo ══════════════════════════════════════════════════════════
echo   配置金山文档 (kdocs) Token
echo ══════════════════════════════════════════════════════════
echo.
echo 步骤:
echo   1. 浏览器访问 https://www.kdocs.cn/latest (需已登录WPS)
echo   2. 点击右上角头像旁主菜单 → "龙虾专属入口" → 复制 Token
echo   3. 在 QClaw 中运行:
echo      node scripts/get-token.js
echo   4. 或手动配置:
echo      mcporter config add kdocs-qclaw "https://mcp-center.wps.cn/skill_hub/mcp" --header "Authorization=Bearer <TOKEN>" --header "X-Skill-Version=1.3.6" --header "X-Request-Source=qclaw" --transport http --scope home
echo.
echo 支持的文档类型:
echo   .otl (智能文档) / .docx (Word) / .xlsx (Excel)
echo   .pdf / .pptx (PPT) / .ksheet (智能表格) / .dbt (多维表格)
echo.
pause
goto MENU

:END
echo.
echo 再见！
exit /b 0
