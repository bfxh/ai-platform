# 根除残留Bug — GitHub项目彻底解决方案 Spec

## Why
Bug知识库中仍有17个⚠️残留问题无法通过"打补丁"方式彻底解决，同类漏洞反复出现。需要引入成熟的GitHub开源项目，从架构层面替换不安全模式，使这些问题**从根本上不可能再出现**。

## What Changes
- 引入6个GitHub开源项目替换不安全代码模式
- 修复17个残留Bug中的14个（3个设计限制类保留监控）
- 创建安全工具函数库 `core/secure_utils.py` 统一封装安全操作
- 更新 Semgrep/Ruff 自定义规则，检测旧模式并提示新API
- 更新 Bug 知识库，标记修复状态

### 引入的GitHub项目

| 项目 | GitHub | 解决的Bug | 替换模式 |
|------|--------|----------|---------|
| restricted-exec | gaussian/restricted-exec | CMD-011, CMD-012 | 黑名单→白名单命令执行 |
| defusedxml | tiran/defusedxml | XXE-002, XXE-003 | xml.etree→defusedxml |
| simpleeval | danthedeckie/simpleeval | DES-006, DES-007 | eval/exec→simpleeval |
| httpx | encode/httpx | ASY-003 | 同步requests→异步httpx |
| keyring | jaraco/keyring | KEY-003, KEY-004 | 硬编码密钥→系统密钥环 |
| certifi | certifi/python-certifi | SSL-002~009 | verify=False→certifi.where() |

### 残留Bug修复计划

| ID | 类别 | 修复方案 | 状态 |
|----|------|---------|------|
| CMD-011 | 命令注入 | restricted-exec 白名单 | 🔧修复 |
| CMD-012 | 命令注入 | restricted-exec 白名单 | 🔧修复 |
| DES-005 | 反序列化 | 第三方库，添加 # nosec 注释 + Bandit忽略 | 📋监控 |
| DES-006 | eval绕过 | simpleeval 替换 eval() | 🔧修复 |
| DES-007 | exec外部文件 | importlib + simpleeval 替换 exec() | 🔧修复 |
| XXE-002 | XXE | defusedxml 替换 ET.fromstring | 🔧修复 |
| XXE-003 | XXE | defusedxml 替换 ET.fromstring | 🔧修复 |
| KEY-003 | 硬编码密钥 | keyring 存储密钥 + 启动时检查 | 🔧修复 |
| KEY-004 | 硬编码密钥 | keyring 存储 HMAC 密钥 | 🔧修复 |
| KEY-005 | 凭据泄露 | python-dotenv + .gitignore | 🔧修复 |
| KEY-006 | 凭据泄露 | 日志脱敏函数 | 🔧修复 |
| SSL-002~009 | SSL禁用 | certifi + 安全SSL上下文工厂 | 🔧修复 |
| NET-003 | 网络暴露 | 配置项控制（设计意图，保留） | 📋监控 |
| INF-005~006 | 信息泄露 | 安全异常处理装饰器 | 🔧修复 |
| ASY-003 | async阻塞 | httpx.AsyncClient 替换 requests | 🔧修复 |
| RAC-002 | 竞态条件 | asyncio.Lock 封装 | 🔧修复 |

## Impact
- Affected specs: security-automation (扩展工具链)
- Affected code:
  - `core/ai_agent.py` — CMD-011
  - `storage/mcp/Tools/da.py` — CMD-012
  - `storage/mcp/BC/unified_workflow.py` — DES-006
  - `storage/mcp/JM/blender_automation.py` — DES-007
  - `UFO/ufo/client/mcp/http_servers/mobile_mcp_server.py` — XXE-002
  - `UFO/record_processor/parser/psr_record_parser.py` — XXE-003
  - `remote-control/protocol.py` — KEY-003, RAC-002
  - `storage/mcp/Tools/hybrid_cache.py` — KEY-004
  - `remote-control/exo_bridge.py` — ASY-003
  - `storage/mcp/Tools/net_pro.py` — SSL-002
  - `storage/mcp/Tools/aria2_mcp.py` — SSL-003
  - `storage/mcp/BC/github_dl.py` — SSL-004
  - `storage/mcp/BC/github_auto_commit.py` — SSL-005
  - `storage/mcp/BC/github_accelerator.py` — SSL-006
  - `storage/mcp/BC/dev_mgr.py` — SSL-007
  - `security-tools/tools/vuln_scanner.py` — SSL-008
  - `security-tools/tools/web_security.py` — SSL-009
  - `UFO/ufo/automator/ui_control/ui_tree.py` — INF-005
  - `UFO/ufo/automator/ui_control/controller.py` — INF-006
- 新增文件: `core/secure_utils.py` (安全工具函数库)
- 修改文件: `requirements.txt`, `.semgrep.yml`, `pyproject.toml`

## ADDED Requirements

### Requirement: 安全工具函数库 (core/secure_utils.py)
系统 SHALL 提供 `core/secure_utils.py` 模块，封装所有安全操作为统一API：

```python
# 命令执行 — 白名单模式
from core.secure_utils import safe_exec_command
safe_exec_command(["git", "status"], allowed_commands={"git", "python", "pip"})

# XML解析 — XXE安全
from core.secure_utils import safe_xml_parse
tree = safe_xml_parse(xml_string)

# 表达式求值 — 无eval
from core.secure_utils import safe_eval_expr
result = safe_eval_expr("a + b > 10", names={"a": 5, "b": 8})

# 密钥管理 — 系统密钥环
from core.secure_utils import SecureKeyManager
km = SecureKeyManager()
km.set("remote-control/secret", "my-secret-value")
secret = km.get("remote-control/secret")

# SSL上下文 — 安全默认
from core.secure_utils import create_ssl_context
ctx = create_ssl_context()  # 默认验证开启，使用certifi

# HTTP客户端 — 异步优先
from core.secure_utils import get_http_client
async with get_http_client() as client:
    resp = await client.get("https://api.example.com")

# 异常脱敏 — 防止信息泄露
from core.secure_utils import safe_error_handler
@safe_error_handler
async def handler(request):
    ...
```

#### Scenario: 开发者需要执行外部命令
- **WHEN** 开发者调用 `safe_exec_command(cmd, allowed_commands=...)`
- **THEN** 仅允许白名单中的命令执行
- **AND** 非白名单命令抛出 `CommandNotAllowedError`
- **AND** 所有执行记录写入审计日志

#### Scenario: 开发者需要解析XML
- **WHEN** 开发者调用 `safe_xml_parse(xml_string)`
- **THEN** 使用 defusedxml 安全解析
- **AND** 自动拦截 ENTITY/DOCTYPE 声明

#### Scenario: 开发者需要求值表达式
- **WHEN** 开发者调用 `safe_eval_expr(expr, names=...)`
- **THEN** 使用 simpleeval 安全求值
- **AND** 不可能执行任意代码

### Requirement: restricted-exec 白名单命令执行
系统 SHALL 使用 `restricted-exec` (github.com/gaussian/restricted-exec) 替代黑名单模式：

1. `ai_agent.py` 的 `_run_bash` 方法改用白名单
2. `da.py` 的命令执行改用白名单
3. 白名单定义在 `core/secure_utils.py` 中统一管理
4. 新增命令需显式注册到白名单

#### Scenario: 尝试执行未注册的命令
- **WHEN** 代码尝试执行 `rm -rf /`
- **THEN** restricted-exec 拒绝执行
- **AND** 返回 `CommandNotAllowedError` 而非执行

### Requirement: defusedxml 安全XML解析
系统 SHALL 使用 `defusedxml` (github.com/tiran/defusedxml) 替换所有 `xml.etree.ElementTree.fromstring`：

1. `mobile_mcp_server.py` 的 XML 解析
2. `psr_record_parser.py` 的 XML 解析
3. `core/secure_utils.py` 封装 `safe_xml_parse()` 函数

#### Scenario: 解析包含XXE攻击的XML
- **WHEN** XML包含 `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>`
- **THEN** defusedxml 拒绝解析
- **AND** 抛出 `EntitiesForbiddenError`

### Requirement: simpleeval 安全表达式求值
系统 SHALL 使用 `simpleeval` (github.com/danthedeckie/simpleeval) 替换 `eval()`/`exec()`：

1. `unified_workflow.py` 的条件表达式求值
2. `blender_automation.py` 的外部文件执行改用 `importlib`
3. `core/secure_utils.py` 封装 `safe_eval_expr()` 函数

#### Scenario: 求值包含恶意代码的表达式
- **WHEN** 表达式为 `__import__('os').system('rm -rf /')`
- **THEN** simpleeval 拒绝求值
- **AND** 抛出 `FeatureNotAvailable` 异常

### Requirement: httpx 异步HTTP客户端
系统 SHALL 使用 `httpx` (github.com/encode/httpx) 替换 async 函数中的同步 `requests`：

1. `exo_bridge.py` 的 `requests.post` 改为 `httpx.AsyncClient.post`
2. `core/secure_utils.py` 封装 `get_http_client()` 工厂函数
3. 支持同步/异步双模式（httpx 原生支持）

#### Scenario: async函数发起HTTP请求
- **WHEN** async函数调用 `get_http_client()`
- **THEN** 返回 `httpx.AsyncClient` 实例
- **AND** 请求不阻塞事件循环

### Requirement: keyring 密钥管理
系统 SHALL 使用 `keyring` (github.com/jaraco/keyring) 管理敏感密钥：

1. `protocol.py` 的默认密码改用 keyring 读取
2. `hybrid_cache.py` 的 HMAC 密钥改用 keyring 读取
3. `core/secure_utils.py` 封装 `SecureKeyManager` 类
4. 首次运行时自动生成随机密钥并存入 keyring
5. keyring 不可用时降级到环境变量 + 警告日志

#### Scenario: 首次启动无密钥
- **WHEN** 系统首次启动，keyring中无密钥
- **THEN** 自动生成随机密钥并存入系统密钥环
- **AND** 日志记录"已生成新密钥，请妥善保管"

#### Scenario: keyring不可用
- **WHEN** 系统密钥环服务不可用
- **THEN** 降级到环境变量读取
- **AND** 日志记录警告"密钥环不可用，使用环境变量降级模式"

### Requirement: certifi 安全SSL上下文
系统 SHALL 使用 `certifi` (github.com/certifi/python-certifi) 提供SSL证书验证：

1. 所有 `verify=False` 替换为 `verify=certifi.where()`
2. 所有 `ssl.CERT_NONE` 替换为 `ssl.CERT_REQUIRED`
3. 所有 `ssl._create_unverified_context` 替换为安全上下文
4. `core/secure_utils.py` 封装 `create_ssl_context()` 工厂函数
5. 开发环境可通过 `\python\config\ssl_dev_mode.json` 临时禁用（需明确声明）

#### Scenario: 生产环境SSL请求
- **WHEN** 代码发起HTTPS请求
- **THEN** 默认使用 certifi CA证书验证
- **AND** 证书验证失败时拒绝连接

#### Scenario: 开发环境需要绕过SSL
- **WHEN** 开发者创建 `ssl_dev_mode.json` 配置文件
- **THEN** 仅对配置中列出的域名禁用验证
- **AND** 日志记录"开发模式：SSL验证已对 xxx 域名禁用"

### Requirement: 安全异常处理装饰器
系统 SHALL 提供异常脱敏机制，防止堆栈跟踪泄露到客户端：

1. `core/secure_utils.py` 封装 `safe_error_handler` 装饰器
2. UFO `ui_tree.py` 和 `controller.py` 使用该装饰器
3. 异常信息记录到日志，但返回给客户端的是通用错误消息

#### Scenario: 内部异常发生
- **WHEN** 处理请求时发生 `ValueError("database connection failed: host=10.0.0.5")`
- **THEN** 客户端收到 `{"error": "Internal server error"}`
- **AND** 完整异常信息记录到服务器日志

### Requirement: asyncio.Lock 竞态条件修复
系统 SHALL 修复 `protocol.py` 的 `clients` 字典竞态条件：

1. 添加 `asyncio.Lock` 保护 `clients` 字典的增删改查
2. 所有访问 `clients` 的协程必须先获取锁

#### Scenario: 多协程并发修改clients
- **WHEN** 两个协程同时尝试修改 clients 字典
- **THEN** asyncio.Lock 确保串行访问
- **AND** 不会出现数据竞争

### Requirement: 更新Semgrep/Ruff规则
系统 SHALL 更新自定义安全规则，检测旧模式并提示新API：

1. 新增规则: 检测 `subprocess.run(..., shell=True)` → 提示使用 `safe_exec_command()`
2. 新增规则: 检测 `ET.fromstring()` → 提示使用 `safe_xml_parse()`
3. 新增规则: 检测 `eval()` → 提示使用 `safe_eval_expr()`
4. 新增规则: 检测 `requests.post/get` 在 async 函数中 → 提示使用 `httpx.AsyncClient`
5. 新增规则: 检测硬编码密钥字符串 → 提示使用 `SecureKeyManager`
6. 新增规则: 检测 `verify=False` → 提示使用 `create_ssl_context()`

## MODIFIED Requirements

### Requirement: requirements.txt 安全工具依赖
在现有 requirements.txt 中追加新依赖：

```
# Security Libraries (replacing unsafe patterns)
restricted-exec>=0.1.0
defusedxml>=0.8.0
simpleeval>=1.0.0
httpx>=0.27.0
keyring>=25.0.0
certifi>=2024.0.0
python-dotenv>=1.0.0
```

### Requirement: Bug知识库更新
更新 `user/knowledge/knowledge/topics/bug-knowledge-base.md`：
- 14个 ⚠️ 改为 ✅（已通过GitHub项目彻底解决）
- 3个保留 📋监控状态（DES-005 第三方库、NET-003 设计意图、KEY-005 外部项目）
- 每个修复项注明使用的GitHub项目

## REMOVED Requirements

### Requirement: 黑名单命令过滤
**Reason**: restricted-exec 白名单模式完全替代黑名单，更安全且不可能被绕过
**Migration**: 所有 `_DANGEROUS_CMDS` / `_BLOCKED` 黑名单替换为 `safe_exec_command()` 白名单

### Requirement: 手动SSL验证配置
**Reason**: certifi + create_ssl_context() 工厂函数提供安全默认值
**Migration**: 所有手动 `verify=False` / `ssl.CERT_NONE` 替换为 `create_ssl_context()`
