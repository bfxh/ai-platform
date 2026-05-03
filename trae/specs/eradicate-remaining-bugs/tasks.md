# Tasks

- [x] Task 1: 安装GitHub开源项目依赖
  - [x] SubTask 1.1: pip install defusedxml simpleeval httpx keyring certifi python-dotenv (restricted-exec需Python>=3.11，改用自实现白名单)
  - [x] SubTask 1.2: 验证所有库安装成功
  - [x] SubTask 1.3: 更新 requirements.txt 添加新依赖

- [x] Task 2: 创建 core/secure_utils.py 安全工具函数库
  - [x] SubTask 2.1: 实现 safe_exec_command() — 自实现白名单命令执行
  - [x] SubTask 2.2: 实现 safe_xml_parse() — 基于 defusedxml 安全XML解析
  - [x] SubTask 2.3: 实现 safe_eval_expr() — 基于 simpleeval 安全表达式求值
  - [x] SubTask 2.4: 实现 SecureKeyManager 类 — 基于 keyring 密钥管理（含环境变量降级）
  - [x] SubTask 2.5: 实现 create_ssl_context() — 基于 certifi 安全SSL上下文工厂
  - [x] SubTask 2.6: 实现 get_http_client() — httpx 同步/异步客户端工厂
  - [x] SubTask 2.7: 实现 safe_error_handler 装饰器 — 异常脱敏
  - [x] SubTask 2.8: 编写模块级文档和使用示例

- [x] Task 3: 修复 CMD-011/CMD-012 — 命令注入白名单替换
  - [x] SubTask 3.1: 修改 core/ai_agent.py — _run_bash 改用 safe_exec_command()
  - [x] SubTask 3.2: 修改 storage/mcp/Tools/da.py — 命令执行改用 safe_exec_command()
  - [x] SubTask 3.3: 移除两处 _DANGEROUS_CMDS/_BLOCKED 黑名单

- [x] Task 4: 修复 DES-006/DES-007 — eval/exec替换
  - [x] SubTask 4.1: 修改 storage/mcp/BC/unified_workflow.py — eval() 改用 safe_eval_expr()
  - [x] SubTask 4.2: 修改 storage/mcp/JM/blender_automation.py — exec() 改用 importlib 动态导入

- [x] Task 5: 修复 XXE-002/XXE-003 — defusedxml替换
  - [x] SubTask 5.1: 修改 UFO/ufo/client/mcp/http_servers/mobile_mcp_server.py — ET.fromstring 改用 safe_xml_parse()
  - [x] SubTask 5.2: 修改 UFO/record_processor/parser/psr_record_parser.py — ET.fromstring 改用 safe_xml_parse()

- [x] Task 6: 修复 KEY-003/KEY-004 — 密钥管理
  - [x] SubTask 6.1: 修改 remote-control/protocol.py — 默认密码改用 SecureKeyManager
  - [x] SubTask 6.2: 修改 storage/mcp/Tools/hybrid_cache.py — HMAC密钥改用 SecureKeyManager
  - [x] SubTask 6.3: 创建密钥初始化脚本 scripts/check/init_keys.py

- [x] Task 7: 修复 KEY-005/KEY-006 — 凭据泄露
  - [x] SubTask 7.1: 修改 UFO/galaxy/webui/server.py 和 UFO/ufo/server/app.py — API Key 打印改用日志脱敏
  - [x] SubTask 7.2: 检查 StepFun .env 是否在 .gitignore 中

- [x] Task 8: 修复 SSL-002~009 — SSL证书验证
  - [x] SubTask 8.1: 修改 storage/mcp/Tools/net_pro.py — ssl.CERT_NONE 改用 create_ssl_context()
  - [x] SubTask 8.2: 修改 storage/mcp/Tools/aria2_mcp.py — SSL验证修复
  - [x] SubTask 8.3: 修改 storage/mcp/BC/github_dl.py — verify=False 改用 certifi
  - [x] SubTask 8.4: 修改 storage/mcp/BC/github_auto_commit.py — verify=False 改用 certifi
  - [x] SubTask 8.5: 修改 storage/mcp/BC/github_accelerator.py — verify=False 改用 certifi (2处)
  - [x] SubTask 8.6: 修改 storage/mcp/BC/dev_mgr.py — verify=False 改用 certifi
  - [x] SubTask 8.7: 修改 security-tools/tools/vuln_scanner.py — verify=False 改用 certifi (2处)
  - [x] SubTask 8.8: 修改 security-tools/tools/web_security.py — verify=False 改用 certifi

- [x] Task 9: 修复 INF-005/INF-006 — 信息泄露
  - [x] SubTask 9.1: 修改 UFO/ufo/automator/ui_control/ui_tree.py — 堆栈跟踪改用日志脱敏
  - [x] SubTask 9.2: 修改 UFO/ufo/automator/ui_control/controller.py — 堆栈跟踪改用日志脱敏

- [x] Task 10: 修复 ASY-003 — async阻塞
  - [x] SubTask 10.1: 修改 remote-control/exo_bridge.py — requests.post 改用 httpx.AsyncClient

- [x] Task 11: 修复 RAC-002 — 竞态条件
  - [x] SubTask 11.1: 修改 remote-control/protocol.py — clients dict 添加 asyncio.Lock

- [x] Task 12: 更新安全规则和配置
  - [x] SubTask 12.1: 更新 .semgrep.yml 添加6条新规则（检测旧模式→提示新API）
  - [x] SubTask 12.2: 更新 pyproject.toml 添加新依赖配置
  - [x] SubTask 12.3: 更新 Bug 知识库标记修复状态

- [x] Task 13: 运行全量验证
  - [x] SubTask 13.1: 运行 security_scan.py --quick 确认无新增高危问题
  - [x] SubTask 13.2: Bandit 扫描 0 个问题，Ruff S 规则问题均为预存问题
  - [x] SubTask 13.3: 验证 core/secure_utils.py 所有函数可正常调用 (11/11 passed)
  - [x] SubTask 13.4: 确认17个残留Bug中14个已标记为✅，仅2个📋监控

# Task Dependencies
- [Task 2] depends on [Task 1] (需要库安装后才能封装)
- [Task 3~11] depends on [Task 2] (需要 secure_utils.py 封装完成)
- [Task 12] depends on [Task 3~11] (修复完成后更新规则)
- [Task 13] depends on [Task 12] (规则更新后验证)
- [Task 3, 4, 5, 6, 7, 8, 9, 10, 11] 可并行执行 (互不依赖)
