# 根除残留Bug — 验证检查清单

## 依赖安装验证
- [x] restricted-exec 改用自实现白名单（Python 3.10 不兼容 restricted-exec 需≥3.11）
- [x] defusedxml 安装成功且 `from defusedxml.ElementTree import fromstring` 通过
- [x] simpleeval 安装成功且 `from simpleeval import simple_eval` 通过
- [x] httpx 安装成功且 `import httpx; httpx.__version__` 通过
- [x] keyring 安装成功且 `import keyring` 通过
- [x] certifi 安装成功且 `import certifi; certifi.where()` 通过
- [x] requirements.txt 包含全部6个新依赖（defusedxml, simpleeval, httpx, keyring, certifi, python-dotenv）

## core/secure_utils.py 功能验证
- [x] safe_exec_command() 白名单模式正常工作 — 允许的命令可执行，不允许的抛异常
- [x] safe_xml_parse() 正常解析合法XML，拦截XXE攻击 (EntitiesForbidden)
- [x] safe_eval_expr() 正常求值数学表达式，拒绝恶意代码 (__import__ 被拦截)
- [x] SecureKeyManager.get/set 正常工作 — keyring 可用时使用 keyring
- [x] SecureKeyManager 降级模式正常 — keyring 不可用时降级到环境变量
- [x] create_ssl_context() 返回启用证书验证的SSL上下文 (CERT_REQUIRED, check_hostname=True)
- [x] get_http_client() 返回 httpx.AsyncClient 实例
- [x] safe_error_handler 装饰器正常脱敏异常信息 (返回 {"error": "Internal server error"})

## Bug修复验证

### 命令注入 (CMD-011, CMD-012)
- [x] ai_agent.py 不再使用黑名单，改用 safe_exec_command() 白名单
- [x] da.py 不再使用 _DANGEROUS_CMDS 黑名单，改用 safe_exec_command() 白名单
- [x] 尝试执行非白名单命令时抛出 CommandNotAllowedError

### eval/exec替换 (DES-006, DES-007)
- [x] unified_workflow.py 不再使用 eval()，改用 safe_eval_expr()
- [x] blender_automation.py 不再使用 exec()，改用 importlib 动态导入
- [x] safe_eval_expr() 无法执行 __import__('os').system('...')

### XXE防护 (XXE-002, XXE-003)
- [x] mobile_mcp_server.py 使用 safe_xml_parse() 替代 ET.fromstring()
- [x] psr_record_parser.py 使用 safe_xml_parse() 替代 ET.fromstring()
- [x] 包含 ENTITY 声明的XML被 defusedxml 拦截 (EntitiesForbidden)

### 密钥管理 (KEY-003, KEY-004)
- [x] protocol.py 不再使用硬编码默认密码 'remotelink-secret'
- [x] hybrid_cache.py 不再使用硬编码 HMAC 密钥 b"hybrid_cache_integrity_v1"
- [x] 首次运行时自动生成随机密钥并存入 keyring
- [x] keyring 不可用时降级到环境变量并记录警告

### 凭据泄露 (KEY-005, KEY-006)
- [x] server.py/app.py 不再 print API Key，改用 mask_sensitive() 脱敏
- [x] StepFun .env 在 .gitignore 中（新建 .gitignore 添加 .env 规则）

### SSL验证 (SSL-002~009)
- [x] net_pro.py 不再使用 ssl.CERT_NONE
- [x] aria2_mcp.py SSL验证已启用
- [x] github_dl.py 不再使用 verify=False
- [x] github_auto_commit.py 不再使用 verify=False
- [x] github_accelerator.py 不再使用 verify=False (2处)
- [x] dev_mgr.py 不再使用 verify=False
- [x] vuln_scanner.py 不再使用 verify=False (2处)
- [x] web_security.py 不再使用 verify=False
- [x] 所有SSL请求默认使用 certifi CA证书

### 信息泄露 (INF-005, INF-006)
- [x] ui_tree.py 堆栈跟踪不再泄露到 UI 树
- [x] controller.py 堆栈跟踪不再泄露到返回值
- [x] safe_error_handler 装饰器正常工作

### async阻塞 (ASY-003)
- [x] exo_bridge.py 不再在 async 函数中使用同步 requests
- [x] 改用 httpx.AsyncClient 异步请求

### 竞态条件 (RAC-002)
- [x] protocol.py clients 字典操作受 asyncio.Lock 保护

## 安全规则验证
- [x] .semgrep.yml 包含6条新规则（检测旧模式→提示新API）
- [x] pyproject.toml 更新为 ruff.lint 新格式，添加 [tool.security] 配置
- [x] 新规则能检测到 shell=True/eval/verify=False/硬编码密钥等旧模式并提示新API

## 全量扫描验证
- [x] security_scan.py --quick Bandit 0个问题，Ruff S规则问题均为预存问题
- [x] Bug知识库中14个 ⚠️ 已改为 ✅
- [x] 仅2个保留 📋监控状态 (DES-005 第三方库漏洞, NET-003 设计意图)
