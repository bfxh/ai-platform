# \python 知识库索引

> 38402行代码 → 4个主题知识页 | 更新: 2026-04-28

## 主题页 (MOC)

| 主题 | 文件 | 涵盖代码 | 压缩比 |
|------|------|----------|--------|
| [RemoteLink架构](knowledge/topics/remotelink-architecture.md) | remote-control/ (7775L) | 15个核心模块 | ~50:1 |
| [Core核心模块](knowledge/topics/core-modules.md) | core/ (19816L) | 12个核心模块 | ~60:1 |
| [代码审查官](knowledge/topics/code-reviewer.md) | code_reviewer.py (370L) | 审查+规则 | ~10:1 |
| [跨引擎3D资产转换](knowledge/topics/cross-engine-3d-asset-conversion.md) | engine_converter/ (224K) | 1610条转换路径 | ~80:1 |

## 端口速查

| 端口 | 服务 | 启动命令 |
|------|------|----------|
| 11434 | Ollama | `$env:OLLAMA_HOST="0.0.0.0:11434"; D:\rj\Ollama\ollama.exe serve` |
| 8080 | 文件上传 | `python file_upload_server.py` |
| 8081 | 远程控制 | `python remote_control_server.py` |
| 8082 | 通知推送 | `python notification_service.py` |
| 52416 | 任务队列 | `python queue_server.py` |
| 50050 | WS控制 | protocol.py内置 |
| 50052 | 设备发现 | discovery.py内置 |
| 52415 | EXO集群 | exo_bridge.py内置 |

## 冗余文件清单 (可清理)

以下为迭代版本文件，最新版已包含其全部功能:

| 冘余文件 | 行数 | 保留版本 |
|----------|------|----------|
| auto_click_v1~v4.py | 365L | auto_click_v4.py |
| auto_test_v1~v7.py | 949L | auto_test_v7.py |
| auto_world_v2~v3.py | 238L | auto_world_v3.py |
| check_log/2.py, check_version_json.py | 92L | check_log2.py |
| create_swarm_mod/mod2/mod3.py | 662L | create_swarm_mod3.py |
| fix_dig_speed_v3/v4.py | 171L | fix_dig_speed_v4.py |
| launch_manifest/2/3.py | 407L | launch_manifest3.py |
| launch_hmcl_*.py (5个) | 387L | launch_hmcl_final.py |
| test_launch/2/3.py | 278L | test_launch3.py |
| pipeline_engine_backup_*.py (2个) | 822L | pipeline_engine.py |
| simple_scan/2.py, scan_files.py | 193L | simple_scan2.py |
| send_message/2.py | 62L | send_message2.py |
| **合计可清理** | **~4626L** | |

## 关键配置路径

| 配置 | 路径 |
|------|------|
| 规则库 | \python\ai-plugin\rules\code_review_rules.md |
| Plugin清单 | \python\ai-plugin\plugin.yaml |
| 共享目录 | D:\Shared |
| 上下文 | \python\user\context.json |
| 模型信息 | \python\storage\models\model_info.json |
| 共享上下文 | \python\storage\shared_context/ |
| 沙盒trash | \python\storage\trash |
