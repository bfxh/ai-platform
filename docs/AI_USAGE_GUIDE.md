# \python AI 使用指南

> **目标读者**: Claude, GPT, Kimi, DeepSeek, 以及其他所有 AI 助手
> **版本**: v4.2
> **更新日期**: 2026-04-22

---

## 你必须知道的事情

### 1. \python 是什么

\python 不是一个简单的文件夹，它是一个**完整的 AI 操作系统**。包含：
- **GSTACK 工作流引擎** - 控制所有 AI 工作流程
- **MCP 工具系统** - 108 个分类工具 (JM/BC/Tools)
- **Skills 技能系统** - 29 个可调用技能
- **CLL_Projects** - 44 个 LLM 开源项目
- **CC 三级缓存** - 文件分类存储系统
- **自动化系统** - 每日备份和更新

### 2. 你的职责

作为 AI 助手，你的职责是：
1. **保护架构完整性** - 不要随意修改核心文件
2. **正确分类文件** - 新文件必须放到正确位置
3. **维护索引更新** - 移动文件后更新 INDEX.md
4. **执行自动化任务** - 帮助用户运行备份/更新
5. **报告状态** - 每次对话开始时报告架构状态

### 3. 绝对禁止

- ❌ 直接删除任何文件（必须先移到 CC/3_Unused）
- ❌ 修改 ai_architecture.json 不备份
- ❌ 把 JM 文件放到 BC 目录
- ❌ 忽略 GSTACK 状态
- ❌ 不读 AGENTS.md 就操作架构

---

## 快速开始

### 第一步：检查 GSTACK

每次对话开始时，执行：
```python
# 调用 GSTACK
mcp_trae-gstack_gstack
```

如果 GSTACK 不可用：
- 告知用户
- 切换到 fallback_mode
- 继续使用 Python/MCP 脚本

### 第二步：读取 AGENTS.md

在操作 \python 之前，必须读取：
```
\python\AGENTS.md (2090 行)
```

这是完整的架构文档，包含所有规则。

### 第三步：报告状态

向用户报告当前架构状态：
```
✅ GSTACK v3.1 Ready
✅ MCP: JM(30) BC(46) Tools(32)
✅ Skills: 29 available
✅ CC Cache: 3 categories
✅ CLL Projects: 44 projects
```

---

## 文件分类指南

### 新文件来了怎么办？

```
新文件到达
    ↓
步骤 1: 判断类型
    - 是 MCP 工具？→ 步骤 2
    - 是项目代码？→ 步骤 3
    - 是文档/脚本？→ 步骤 4
    - 不知道？→ 步骤 5

步骤 2: MCP 分类
    - 建模相关 (Blender, 3D, Unity, UE, Godot) → \python\MCP\JM\
    - 代码相关 (GitHub, 搜索, 修复, 工作流) → \python\MCP\BC\
    - 工具相关 (下载, 网络, 系统, 监控) → \python\MCP\Tools\
    - 更新 mcp-config.json
    - 更新对应目录的 README.md

步骤 3: 项目分类
    - LLM/AI 开源项目 → \python\CLL_Projects\
    - 其他项目 → CC/1_Raw/Projects/ 或 CC/3_Unused/Projects/
    - 更新 CLL_Projects/INDEX.md

步骤 4: 文档/脚本分类
    - 原始下载 → CC/1_Raw/Others/
    - 旧版本 → CC/2_Old/Others/
    - 未使用 → CC/3_Unused/Others/
    - 更新对应 INDEX.md

步骤 5: 不确定时
    - 读取文件内容判断
    - 询问用户
    - 默认放到 CC/3_Unused/Others/
    - 记录到 INDEX.md
```

### 分类关键词对照表

| 关键词 | 分类 | 目录 |
|--------|------|------|
| blender, 3d, model, unity, ue, godot, video, vision | JM | \python\MCP\JM\ |
| code, github, git, find, fix, search, workflow, dev | BC | \python\MCP\BC\ |
| download, network, system, monitor, auto, config | Tools | \python\MCP\Tools\ |
| llm, gpt, transformer, neural, ai model | CLL | \python\CLL_Projects\ |
| .bat, .ps1, 临时, test, old | Unused | CC/3_Unused/ |

---

## 常用操作

### 检查架构

```bash
# 完整检查
python \python\scripts\check_architecture.py

# 仅检查 MCP
python \python\scripts\check_architecture.py --component mcp

# 仅检查 CC
python \python\scripts\check_architecture.py --component cc
```

### 备份系统

```bash
# 立即备份
python \python\scripts\backup_architecture.py --name emergency_backup

# 每日备份
python \python\scripts\daily_backup.py
```

### 清理文件

```bash
# 预览清理
python \python\scripts\cleanup_architecture.py --dry-run

# 执行清理
python \python\scripts\cleanup_architecture.py --execute
```

### 更新 GitHub 项目

```bash
# 检查所有项目更新
python \python\scripts\update_github_projects.py

# 更新指定项目
python \python\scripts\update_github_projects.py --repos vllm,trl,peft
```

---

## 核心文件说明

### ai_architecture.json

这是架构的核心配置文件。**修改前必须备份**。

关键字段：
- `version` - 架构版本 (当前 v4.2)
- `gstack` - GSTACK 配置
- `mcp` - MCP 分类配置
- `skills` - Skills 系统配置
- `cc` - CC 缓存配置
- `cll_projects` - CLL 项目配置
- `directories` - 目录映射
- `protection` - 保护规则

### index.json

主索引文件，记录所有目录和文件的位置。

### mcp-config.json

MCP 服务器配置文件 (v2.0)。

每个服务必须包含：
```json
{
  "name": "服务名",
  "path": "文件路径",
  "category": "JM/BC/Tools",
  "status": "active",
  "last_validated": "日期"
}
```

---

## 目录结构速查

```
\python\
├── AGENTS.md              # ← 你正在读的文件
├── ai_architecture.json   # ← 核心配置
├── index.json             # ← 主索引
├── .gstack_protected      # ← 保护标记
│
├── MCP\                   # ← 工具目录 (108个文件)
│   ├── JM\                # ← 建模类 (30个)
│   ├── BC\                # ← 代码类 (46个)
│   └── Tools\             # ← 工具类 (32个)
│
├── MCP_Core\              # ← 核心系统
│   └── skills\            # ← 29个 Skills
│
├── CLL_Projects\          # ← 44个 LLM项目
│   ├── Qwen\              # 通义千问
│   ├── vllm\              # 推理引擎
│   ├── llama.cpp\         # C++推理
│   ├── DeepSpeed\         # 训练框架
│   └── ... (40 more)
│
├── CC\                    # ← 三级缓存
│   ├── 1_Raw\             # 原始文件
│   ├── 2_Old\             # 旧版本
│   └── 3_Unused\          # 未使用
│
├── scripts\               # ← 自动化脚本
│   ├── arch_core.py       # 核心逻辑
│   ├── check_architecture.py
│   ├── backup_architecture.py
│   ├── cleanup_architecture.py
│   ├── update_github_projects.py
│   ├── daily_github_update.py
│   ├── daily_backup.py
│   └── schedule_tasks.bat
│
├── gstack_core\           # ← GSTACK 核心
├── Skills\                # ← 技能定义
├── Workflows\             # ← 工作流
├── Brain\                 # ← 记忆系统
├── Tools\                 # ← AI工具
├── Config\                # ← 配置
└── logs\                  # ← 日志
```

---

## 错误处理

### 常见错误 1: GSTACK 不可用

```
症状: 调用 mcp_trae-gstack_gstack 无响应
处理:
  1. 报告用户: "GSTACK 暂时不可用"
  2. 切换到 fallback_mode = "legacy"
  3. 使用 Python 脚本继续操作
  4. 记录到日志
```

### 常见错误 2: 文件分类冲突

```
症状: 一个文件同时匹配 JM 和 BC
处理:
  1. 读取文件内容判断主要功能
  2. 如果是混合功能，放到 BC (代码优先)
  3. 记录到 INDEX.md 说明原因
  4. 询问用户确认
```

### 常见错误 3: 索引不同步

```
症状: 文件存在但 INDEX.md 没记录
处理:
  1. 扫描实际文件列表
  2. 对比 INDEX.md 内容
  3. 更新 INDEX.md 添加缺失项
  4. 标记最后更新时间
```

### 常见错误 4: 配置损坏

```
症状: ai_architecture.json 无法解析
处理:
  1. 检查 CC/2_Old/ 是否有备份
  2. 如果有备份，恢复备份
  3. 如果没有，从 Git 恢复
  4. 如果都没有，重建默认配置
  5. 报告用户所有操作
```

---

## 与其他 AI 协作

### 如果你是 Claude

- 使用你的代码分析能力检查文件内容
- 使用你的长上下文读取 AGENTS.md
- 使用你的推理能力判断文件分类

### 如果你是 GPT

- 使用你的广泛知识识别项目类型
- 使用你的生成能力创建索引文件
- 使用你的理解能力解析配置文件

### 如果你是 Kimi

- 使用你的中文能力处理中文文档
- 使用你的长文本能力读取大文件
- 使用你的搜索能力查找相关信息

### 通用规则

无论你是谁：
1. **先读 AGENTS.md**
2. **再检查 GSTACK**
3. **然后操作**
4. **最后更新索引**

---

## 每日任务清单

### 每天应该做的事

- [ ] 检查 GSTACK 状态
- [ ] 运行架构检查 (/check)
- [ ] 查看日志文件
- [ ] 确认备份完成

### 每周应该做的事

- [ ] 检查 GitHub 项目更新
- [ ] 审查 CC/3_Unused/ 文件
- [ ] 验证索引文件同步
- [ ] 检查磁盘空间

### 每月应该做的事

- [ ] 清理旧备份 (超过7天)
- [ ] 更新 ai_architecture.json 统计
- [ ] 验证所有配置文件
- [ ] 生成架构健康报告

---

## 联系与反馈

如果发现架构问题：
1. 记录到 \python\logs\issues.log
2. 备份相关文件到 CC/2_Old/
3. 尝试修复
4. 如果无法修复，报告用户

---

## 最后的话

\python 是一个活的系统，需要所有 AI 助手共同维护。

**记住：**
- 保护 > 修改
- 分类 > 混乱
- 备份 > 后悔
- 索引 > 遗忘

感谢你维护这个系统！
