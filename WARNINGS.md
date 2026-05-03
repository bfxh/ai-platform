# [!!] WARNINGS — AI 必须知道的系统记忆

> 本文件由 `/python/intervention/update_memory.py` 自动生成和更新
> 最后更新: 2026-04-28
> 每个 AI Agent 在执行任何任务前，必须先读完这个文件的前 5 个部分

---

## 1. 关键软件路径 (别再用默认路径了)

| 软件 | 实际路径 | AI常犯错误 |
|------|---------|-----------|
| Git | `D:/rj/KF/Git/cmd/git.exe` | 用 `C:\Program Files\Git` 或系统PATH中的git |
| Ollama | `D:/rj/Ollama/ollama.exe` | 用 `ollama` 命令而没指定全路径 |
| Python | `D:/rj/Python310/python.exe` | 用系统自带的python |
| 软件目录 | `D:/rj/` (SOFTWARE_DIR) | 用 `C:\Program Files\` |
| 项目根 | `/python/` | AI_PATH 和 PROJECT_ROOT 都指向这里 |

**强制规则**: 任何外部命令必须用绝对路径或 `%VAR%` 环境变量，禁止依赖系统PATH。

---

## 2. 环境变量 (TRAE登录必需)

| 变量 | 值 | 存储位置 |
|------|-----|---------|
| OLLAMA_DIR | D:/rj/Ollama | HKCU\Environment (REG_EXPAND_SZ) |
| GIT_DIR | D:/rj/KF/Git | HKCU\Environment (REG_EXPAND_SZ) |
| SOFTWARE_DIR | D:/rj | HKCU\Environment (REG_EXPAND_SZ) |
| AI_PATH | /python | HKCU\Environment (REG_EXPAND_SZ) |
| MCP_PATH | /python/MCP | HKCU\Environment (REG_EXPAND_SZ) |
| MCP_LOG_PATH | /python/logs | HKCU\Environment (REG_EXPAND_SZ) |

**TRAE 的 `config.toml` 用 `%OLLAMA_DIR%/ollama.exe` 这样的格式引用。如果变量不存在，TRAE 登录失败。**

验证命令: `py -c "import os; print(os.environ.get('GIT_DIR', 'NOT SET'))"`

---

## 3. Bug 记忆 — 已经犯过的错误

### BUG-001: 环境变量丢失导致 TRAE 登录失败
- **复发次数**: 2
- **现象**: TRAE 启动后无法登录，找不到 ollama.exe / git.exe
- **根因**: `OLLAMA_DIR`, `GIT_DIR` 等环境变量未在 Windows 注册表中设置
- **修复**: 用 `scripts/set_trae_env.py` 写入注册表 `HKCU\Environment`
- **预防**: 重装系统/清理注册表后必须重新运行 `py scripts/set_trae_env.py`
- **检测**: 打开 TRAE 前运行 `py intervention/check_env.py`

### BUG-002: Python 代码放在 .md 文件里不会自动执行
- **复发次数**: 1
- **现象**: BugMemory/Brain 系统建好了但从没被调用过
- **根因**: AI Agent (TRAE/Qoder) 把 `.md` 当作提示词阅读，不会执行其中的 Python 代码块
- **教训**: 不能在 markdown 里放 Python 代码并期望 AI 自动执行
- **正确做法**: 
  - 记忆用纯文本写入 `WARNINGS.md`（本文件）
  - 需要执行的脚本用 `py path/to/script.py` 明确调用
  - hooks 用 `.bat`/`.sh` 文件，放在 `scripts/` 下

### BUG-003: 文件编码问题 (gbk vs utf-8)
- **复发次数**: 2
- **现象**: `UnicodeEncodeError: 'gbk' codec can't encode character`
- **触发条件**: Windows 控制台默认用 GBK，Python 输出中文或 emoji 时报错
- **修复**: 所有 emoji 改用 ASCII 替代 (`[!]`, `[!!]`, `[OK]`, `[FAIL]`)
- **预防**: 代码输出用纯 ASCII，文档注释用中文没问题

---

## 4. 反模式 (重复3次以上的错误模式)

无 — 上述 bug 复发次数均不足3次。

---

## 5. 会话检查清单

**每次 AI 会话开始时，确认以下事项**:

- [ ] 读取了本文件 (`/python/WARNINGS.md`)
- [ ] `GIT_DIR` 环境变量指向 `D:/rj/KF/Git` 且目录存在
- [ ] `OLLAMA_DIR` 环境变量指向 `D:/rj/Ollama` 且 ollama.exe 存在
- [ ] 要执行的外部命令用了绝对路径，不是依赖 PATH
- [ ] 如果要修改架构文件 (`ai_architecture.json`)，先备份
- [ ] 中文输出只用 GBK 安全字符，避免 emoji

检查脚本: `py /python/intervention/pre_session_check.py`

---

## 6. 更新日志

| 日期 | 变更 | 来源 |
|------|------|------|
| 2026-04-28 | 初始创建 | Phase 1-3 总结 |
| 2026-04-28 | BUG-002 记录 | Brain 从未被调用 |
