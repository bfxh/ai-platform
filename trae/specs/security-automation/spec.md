# 安全防护自动化体系 Spec

## Why
\python 平台经过5轮深度安全审计，累计发现并修复90个安全漏洞（73个已修复，17个残留）。当前所有修复均为"打补丁"模式——逐个文件手动修复，同类漏洞反复出现。需要建立自动化防护体系，从工具链层面彻底杜绝同类问题再次发生。

## What Changes
- 安装并配置安全扫描工具链（Bandit + Ruff + Semgrep + detect-secrets）
- 创建 pre-commit hooks 配置，在提交前自动拦截安全问题
- 创建安全扫描脚本，支持一键全量扫描
- 创建 pyproject.toml 统一管理工具配置
- 创建自定义 Ruff/Semgrep 规则，覆盖项目特有模式
- 更新 ai-plugin/rules/ 安全规则文档

## Impact
- Affected specs: TRAE Pipeline v6.0 Phase 2 (安全审计)
- Affected code: 全项目 Python 文件（通过 lint 规则影响）
- 新增文件: pyproject.toml, .pre-commit-config.yaml, scripts/check/security_scan.py, .secrets.baseline
- 修改文件: requirements.txt (添加安全工具依赖)

## ADDED Requirements

### Requirement: 安全扫描工具链
系统 SHALL 提供以下安全扫描工具，覆盖 Bug 知识库中全部18类问题：

| 工具 | 覆盖漏洞类别 | 检测项 |
|------|-------------|--------|
| Bandit | 命令注入、pickle、eval、SSL、硬编码密钥、XXE | B602/B605/B607/B301/B307/B320/B501/B105 |
| Ruff (S规则) | 命令注入、pickle、eval、SSL、路径遍历 | S602/S605/S607/S301/S307/S501/S108 |
| detect-secrets | 硬编码密钥、API Token | 熵值分析+正则匹配 |
| Semgrep | 全部类别（最全面） | p/python + p/owasp-top-ten 规则集 |
| pip-audit | 依赖漏洞 | PyPA 官方 CVE 数据库 |

#### Scenario: 开发者提交包含 shell=True 的代码
- **WHEN** 开发者写 `subprocess.run(cmd, shell=True)` 并提交
- **THEN** pre-commit hook 中的 Bandit/Ruff 拦截提交，显示 B602/S602 警告
- **AND** 提交被阻止，直到开发者修复

#### Scenario: 开发者提交包含硬编码密钥的代码
- **WHEN** 开发者写 `api_key = "ghp_xxxx"` 并提交
- **THEN** detect-secrets 拦截提交，显示密钥泄露警告
- **AND** 提交被阻止

### Requirement: Pre-commit 安全 Hooks
系统 SHALL 在 `.pre-commit-config.yaml` 中配置以下安全 hooks：

1. **bandit** — Python 安全漏洞扫描（中高风险级别）
2. **ruff** — 超快 Linter，启用 S 系列安全规则
3. **detect-secrets** — 密钥泄露检测（基于 .secrets.baseline）
4. **pre-commit-hooks** — detect-private-key, check-merge-conflict, no-commit-to-branch
5. **自定义本地 hook** — 禁止裸 except: pass、禁止 == None

#### Scenario: 首次配置 pre-commit
- **WHEN** 开发者运行 `pre-commit install`
- **THEN** 所有安全 hooks 注册到 Git pre-commit 钩子
- **AND** 后续每次提交自动执行安全扫描

### Requirement: 一键安全扫描脚本
系统 SHALL 提供 `scripts/check/security_scan.py` 脚本，支持：

1. `--quick` 模式：仅运行 Ruff (S规则) + Bandit，30秒内完成
2. `--full` 模式：运行全部工具（Bandit + Ruff + Semgrep + detect-secrets + pip-audit）
3. `--fix` 模式：自动修复可修复的问题（如裸 except → except Exception）
4. 输出 JSON 报告到 `logs/security/` 目录

#### Scenario: 运行快速扫描
- **WHEN** 开发者执行 `python scripts/check/security_scan.py --quick`
- **THEN** 30秒内输出扫描结果
- **AND** 发现高危问题时返回非零退出码

### Requirement: pyproject.toml 统一配置
系统 SHALL 创建 `pyproject.toml` 统一管理所有工具配置：

```toml
[tool.bandit]
severity_level = "medium"
exclude_dirs = ["tests", "storage/cll", "UFO"]

[tool.ruff]
select = ["S", "E", "W", "F"]
ignore = ["E501"]

[tool.mypy]
strict = true
ignore_missing_imports = true
```

### Requirement: 自定义安全规则
系统 SHALL 提供以下项目特有的自定义规则：

1. **Ruff 自定义规则** (通过 pyproject.toml 配置):
   - 禁止 `asyncio.create_task()` 不保存引用
   - 禁止 `requests.Session()` 不在 `with` 或 `close()` 中使用
   - 禁止 `time.sleep()` 在 `async def` 函数中使用

2. **Semgrep 自定义规则** (通过 semgrep.yml):
   - 检测 `0.0.0.0` 绑定
   - 检测 `Access-Control-Allow-Origin: *`
   - 检测 `pickle.loads/pickle.load` 无 HMAC 校验
   - 检测 WebSocket 无 Origin 验证

#### Scenario: 开发者写 asyncio.create_task 不保存引用
- **WHEN** 开发者写 `asyncio.create_task(some_coroutine())` 不保存返回值
- **THEN** Semgrep 自定义规则检测到并报告
- **AND** 提示应保存到 `self._tasks` 集合

### Requirement: 安全基线文件
系统 SHALL 生成以下基线文件：

1. `.secrets.baseline` — detect-secrets 基线，记录已知密钥位置
2. `logs/security/bandit-baseline.json` — Bandit 扫描基线，记录已知问题

#### Scenario: 添加新的合法密钥
- **WHEN** 开发者需要添加新的 API Key 到配置文件
- **THEN** 运行 `detect-secrets scan --update .secrets.baseline` 更新基线
- **AND** 后续提交不再误报该密钥

## MODIFIED Requirements

### Requirement: requirements.txt 安全工具依赖
在现有 requirements.txt 中追加安全工具依赖：

```
# Security Tools
bandit>=1.7.9
detect-secrets>=1.5.0
pip-audit>=0.7.0
safety>=3.2.0
```

注：Ruff 和 Semgrep 通过 pip 单独安装，不纳入项目依赖。

## REMOVED Requirements

### Requirement: 手动安全审计
**Reason**: 自动化工具链替代手动审计，覆盖更全面、速度更快
**Migration**: 保留 Bug 知识库作为参考，但新代码的安全检查由工具链自动完成
