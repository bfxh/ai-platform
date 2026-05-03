# Tasks

- [ ] Task 1: 修复 6 个已确认 Bug
  - [ ] 1.1 queue_server.py: `127.0.0.1` → `0.0.0.0`（已修复，验证）
  - [ ] 1.2 start.bat: Python312 → Python310（已修复，验证）
  - [ ] 1.3 remote_control_server.py: 添加 `import secrets`（已修复，验证）
  - [ ] 1.4 3个服务文件: 添加 UTF-8 编码保护（已修复，验证剩余文件）
  - [ ] 1.5 code_reviewer.py: 添加 `_probe_backends()`（已修复，验证）
  - [ ] 1.6 orchestrator.py: 添加 `--redis` 和 `-i` 参数（已修复，验证）
  - [ ] 1.7 为 queue_server.py、orchestrator.py、full_system.py、phone_connector.py、share_server.py 补充 UTF-8 编码保护

- [ ] Task 2: 清理冗余迭代版本文件
  - [ ] 2.1 创建 `storage/CC/2_Old/remote-control-iterations/` 目录
  - [ ] 2.2 移动 auto_click_v1~v3.py 到 2_Old
  - [ ] 2.3 移动 auto_test_v1~v6.py + auto_test_wrapper.py 到 2_Old
  - [ ] 2.4 移动 auto_world_v2.py 到 2_Old
  - [ ] 2.5 移动 check_log.py, check_version_json.py 到 2_Old
  - [ ] 2.6 移动 create_swarm_mod.py, create_swarm_mod2.py 到 2_Old
  - [ ] 2.7 移动 fix_dig_speed_v3.py 到 2_Old
  - [ ] 2.8 移动 launch_manifest.py, launch_manifest2.py 到 2_Old
  - [ ] 2.9 移动 launch_hmcl_api/direct/jdk17/wildcard.py 到 2_Old（保留 launch_hmcl_final.py）
  - [ ] 2.10 移动 test_launch.py, test_launch2.py 到 2_Old
  - [ ] 2.11 移动 pipeline_engine_backup_*.py 到 2_Old
  - [ ] 2.12 移动 simple_scan.py, scan_files.py 到 2_Old
  - [ ] 2.13 移动 send_message.py 到 2_Old
  - [ ] 2.14 移动 test_sql_review.py 到 2_Old
  - [ ] 2.15 验证清理后所有保留文件可正常导入运行

- [ ] Task 3: 创建统一服务管理器
  - [ ] 3.1 创建 `\python\remote-control\service_manager.py`
  - [ ] 3.2 实现 ServiceConfig 数据类（名称、端口、启动命令、健康检查URL）
  - [ ] 3.3 实现 `start` 命令：单个服务 / all
  - [ ] 3.4 实现 `stop` 命令：按端口查找PID并终止
  - [ ] 3.5 实现 `restart` 命令
  - [ ] 3.6 实现 `status` 命令：表格输出服务状态
  - [ ] 3.7 Ollama 启动自动设置 OLLAMA_HOST=0.0.0.0
  - [ ] 3.8 端口冲突自动检测和处理
  - [ ] 3.9 更新 start.bat 调用 service_manager.py

- [ ] Task 4: 代码审查器接入任务队列
  - [ ] 4.1 在 worker.py 的 TaskExecutor 中注册 CODE_REVIEW handler
  - [ ] 4.2 CODE_REVIEW handler 调用 code_reviewer.CodeReviewer.review()
  - [ ] 4.3 支持参数：code, lang, rules_file
  - [ ] 4.4 测试：通过 queue_server 提交 CODE_REVIEW 任务并获取结果

- [ ] Task 5: 升级健康检查工具
  - [ ] 5.1 debug_diagnose.py 添加 `--fix` 参数
  - [ ] 5.2 实现 `--fix` 自动修复：UTF-8 保护、端口绑定
  - [ ] 5.3 添加 `--json` 输出格式
  - [ ] 5.4 集成到 service_manager.py 的 status 命令

- [ ] Task 6: 删除废弃文件
  - [ ] 6.1 删除 start_all_services.py（已被 service_manager.py 替代）

# Task Dependencies
- Task 1 → Task 3（Bug 修复后再创建服务管理器）
- Task 1 → Task 4（编码修复后再接入任务队列）
- Task 2（独立，可与 Task 1 并行）
- Task 3 → Task 5（服务管理器创建后集成健康检查）
- Task 3 → Task 6（服务管理器就绪后删除废弃文件）
