# 平台健壮性与代码瘦身 Spec

## Why
\python 经过 debug 诊断发现 6 个代码级 bug（端口绑定错误、Python路径错误、缺少 import、GBK编码崩溃、后端不可达无容错、参数缺失），38402 行代码中有 ~4626 行冗余迭代版本，5 个独立服务需要手动逐个启动且无统一生命周期管理，代码审查器缺少与分布式任务队列的集成。需要系统性修复 bug、清理冗余、统一服务管理、打通审查器与任务队列。

## What Changes
- 修复 6 个已确认 bug（queue_server 绑定、start.bat Python路径、remote_control_server import/编码、code_reviewer 后端容错、orchestrator --redis 参数）
- 清理 ~4626 行冗余迭代版本文件，移至 `storage/CC/2_Old/`
- 创建统一服务管理器 `service_manager.py`，一键启停全部 5 个服务 + Ollama
- 将 code_reviewer 注册为 Celery/HTTP 任务类型，接入 queue_server
- 所有服务统一 UTF-8 编码保护，消除 GBK 崩溃
- 更新诊断脚本 `debug_diagnose.py` 为持续可用的健康检查工具

## Impact
- Affected specs: ai-platform-restructure（已完成，本 spec 是其后续维护）
- Affected code: remote-control/ 全部服务文件、code_reviewer.py、debug_diagnose.py
- Affected config: start.bat、Ollama 启动配置

## ADDED Requirements

### Requirement: Bug 修复
系统 SHALL 修复以下 6 个已确认 bug：

| # | Bug | 文件 | 修复方式 |
|---|-----|------|----------|
| B1 | queue_server 绑定 127.0.0.1，局域网不可达 | queue_server.py | 改为 0.0.0.0 |
| B2 | start.bat Python312 路径错误 | start.bat | 改为 Python310 |
| B3 | remote_control_server 缺少 import secrets | remote_control_server.py | 添加 import |
| B4 | emoji 在 GBK 终端导致 UnicodeEncodeError | 3个服务文件 | 添加 sys.stdout.reconfigure |
| B5 | code_reviewer 后端不可达时仍尝试连接 | code_reviewer.py | 添加 _probe_backends() |
| B6 | orchestrator 缺少 --redis 和 -i 参数 | orchestrator.py | 添加参数 |

#### Scenario: GBK 终端运行服务
- **WHEN** 在 Windows 中文终端启动 notification_service.py
- **THEN** 服务正常输出含 emoji 的日志，不崩溃

#### Scenario: 台式机 Ollama 离线
- **WHEN** code_reviewer 的 192.168.1.6:11434 后端不可达
- **THEN** 自动探测并跳过，使用 127.0.0.1:11434，不报错不卡顿

### Requirement: 冗余代码清理
系统 SHALL 将 ~4626 行迭代版本文件移至 `storage/CC/2_Old/`，保留每个迭代链的最新版本：

| 冗余文件组 | 行数 | 保留 |
|-----------|------|------|
| auto_click_v1~v3.py | 251L | auto_click_v4.py |
| auto_test_v1~v6.py + auto_test_wrapper.py | 949L | auto_test_v7.py |
| auto_world_v2.py | 126L | auto_world_v3.py |
| check_log.py, check_version_json.py | 63L | check_log2.py |
| create_swarm_mod/mod2.py | 348L | create_swarm_mod3.py |
| fix_dig_speed_v3.py | 82L | fix_dig_speed_v4.py |
| launch_manifest/2.py | 270L | launch_manifest3.py |
| launch_hmcl_api/direct/jdk17/final/wildcard.py | 387L | launch_hmcl_final.py |
| test_launch/2.py | 185L | test_launch3.py |
| pipeline_engine_backup_*.py (2个) | 822L | pipeline_engine.py |
| simple_scan.py, scan_files.py | 175L | simple_scan2.py |
| send_message.py | 28L | send_message2.py |
| test_sql_review.py | 52L | code_reviewer.py --test |

#### Scenario: 清理后项目结构
- **WHEN** 执行清理操作
- **THEN** 迭代版本文件移至 storage/CC/2_Old/，原位只保留最新版，项目功能不受影响

### Requirement: 统一服务管理器
系统 SHALL 提供 `service_manager.py`，一键管理全部服务：

- 支持 `start` / `stop` / `restart` / `status` 命令
- 管理 6 个服务：Ollama、通知(8082)、远程控制(8081)、文件上传(8080)、任务队列(52416)、代码审查
- 启动时自动检测端口占用，冲突时先停止旧进程
- Ollama 启动自动设置 `OLLAMA_HOST=0.0.0.0:11434`
- `status` 命令显示所有服务运行状态和端口
- 支持 `start ollama` / `start all` 单独或全部启动

#### Scenario: 一键启动全部服务
- **WHEN** 用户执行 `python service_manager.py start all`
- **THEN** Ollama + 5 个服务依次启动，每个启动后验证端口可用，输出状态表

#### Scenario: 端口冲突自动处理
- **WHEN** 8082 端口被旧进程占用
- **THEN** 自动终止占用进程，重新启动通知服务

#### Scenario: 查看服务状态
- **WHEN** 用户执行 `python service_manager.py status`
- **THEN** 输出表格：服务名 | 端口 | 状态 | PID

### Requirement: 代码审查器接入任务队列
系统 SHALL 将 code_reviewer 注册为 queue_server 的任务类型：

- queue_server 新增 `CODE_REVIEW` 任务类型支持
- 提交 CODE_REVIEW 任务时，自动调用 code_reviewer.review()
- 审查结果作为任务结果返回
- 支持指定语言参数 `lang`
- 支持指定规则文件路径 `rules_file`

#### Scenario: 通过任务队列审查代码
- **WHEN** 向 queue_server 提交 `{"task_type":"CODE_REVIEW","params":{"code":"...","lang":"python"}}`
- **THEN** Worker 调用 code_reviewer 审查，返回修正后代码

### Requirement: UTF-8 编码统一保护
所有服务文件 SHALL 在入口处添加 UTF-8 编码保护：

```python
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
```

适用文件：notification_service.py、remote_control_server.py、file_upload_server.py、queue_server.py、orchestrator.py、full_system.py、phone_connector.py、share_server.py

#### Scenario: 任何终端环境
- **WHEN** 在 GBK/UTF-8/任意编码终端运行服务
- **THEN** 日志输出不崩溃，emoji 正常显示或安全替换

### Requirement: 健康检查工具
系统 SHALL 将 debug_diagnose.py 升级为持续可用的健康检查工具：

- 支持 `--fix` 参数自动修复已知问题（端口绑定、编码保护等）
- 支持 `--json` 输出 JSON 格式结果
- 集成到 service_manager.py 的 `status` 命令
- 检查项：模块导入、依赖、配置文件、端口、Ollama、局域网、代码逻辑

#### Scenario: 自动修复
- **WHEN** 用户执行 `python debug_diagnose.py --fix`
- **THEN** 自动检测并修复 queue_server 绑定地址、缺失的 UTF-8 保护等

## MODIFIED Requirements

### Requirement: start.bat 启动脚本
原 start.bat 硬编码 Python312 路径且只启动 orchestrator。现修改为：
- 使用 Python310 正确路径
- 改为调用 service_manager.py start all
- 保留 -i 交互模式支持

## REMOVED Requirements

### Requirement: start_all_services.py 独立启动脚本
**Reason**: 功能已被 service_manager.py 完全替代
**Migration**: 删除 start_all_services.py，所有启动逻辑迁移到 service_manager.py
