# \python TRAE 完整参考手册

> **版本**: v1.0 | **更新**: 2026-04-23 | **目标**: 30分钟内理解完整架构

---

## 目录

1. [系统概述](#1-系统概述)
2. [核心架构](#2-核心架构)
3. [GSTACK 工作流系统](#3-gstack-工作流系统)
4. [MCP 分类系统](#4-mcp-分类系统)
5. [Skills 技能系统](#5-skills-技能系统)
6. [CC 缓存系统](#6-cc-缓存系统)
7. [CLL_Projects 项目集合](#7-cll_projects-项目集合)
8. [保护规则与操作规范](#8-保护规则与操作规范)
9. [故障排除](#9-故障排除)
10. [快速参考](#10-快速参考)

---

## 1. 系统概述

### 1.1 定义

**\python 不是一个文件夹，是一个完整的 AI 操作系统**

```
传统模式: 人 → IDE → 代码 → 运行
\python模式: 人 → AI助手 → \python系统 → 自动执行
```

### 1.2 关键数据

| 指标 | 数值 |
|------|------|
| 总目录数 | 50+ |
| 总文件数 | 2000+ |
| MCP 文件数 | 108+ |
| Skills 技能数 | 29+ |
| CLL 开源项目 | 44 |
| 自动化脚本 | 20+ |

### 1.3 五大核心哲学

| 哲学 | 说明 | 必须遵守 |
|------|------|---------|
| GSTACK 优先 | 所有工作流必须优先使用 GSTACK | 是 |
| 分类即秩序 | 新文件必须按 JM/BC/Tools 分类 | 是 |
| 缓存即历史 | 原始/旧版/未使用文件进入 CC 系统 | 是 |
| 技能即接口 | 所有功能通过 Skills 系统暴露 | 建议 |
| 保护即责任 | 受保护文件修改前必须备份 | 是 |

---

## 2. 核心架构

### 2.1 目录结构

```
\python\
├── .gstack_protected     # [极高] 保护标记，禁止修改
├── AGENTS.md             # [高] AI 操作指南
├── index.json             # [高] 目录索引
├── ai_architecture.json   # [高] 架构配置
│
├── MCP/                   # MCP 服务器 (108+ 文件)
│   ├── JM/               # 建模类: Blender, UE5, Unity, Godot
│   ├── BC/               # 代码类: GitHub, 搜索, 修复, 验证
│   └── Tools/            # 工具类: 下载, 监控, 配置
│
├── MCP_Core/              # 核心系统
│   ├── skills/           # 技能基类和注册
│   ├── workflow/         # 工作流引擎
│   ├── agent/            # Agent 系统
│   └── server.py         # MCP 服务器
│
├── gstack_core/           # GSTACK 工作流引擎
│   ├── gstack_core.py    # 主控制器
│   └── commands.ps1      # PowerShell 命令
│
├── CLL_Projects/          # 44个开源 AI 项目
│   ├── Qwen/             # 通义千问
│   ├── vllm/             # 高性能推理引擎
│   ├── trl/              # 强化学习微调
│   └── ... (44 个项目)
│
├── CC/                    # 分类缓存系统
│   ├── 1_Raw/            # 原始文件
│   ├── 2_Old/            # 旧版本
│   └── 3_Unused/         # 未使用文件
│
├── scripts/               # 自动化脚本
│   ├── daily_backup.py   # 每日备份
│   └── deep_check.py     # 系统检查
│
└── Brain/                # AI 记忆系统
```

### 2.2 核心文件速查

| 文件 | 用途 | 优先级 |
|------|------|--------|
| `gstack_core/gstack_core.py` | GSTACK 主入口 | P0 |
| `MCP_Core/server.py` | MCP 服务器 | P0 |
| `MCP_Core/skills/base.py` | 技能基类 | P0 |
| `AGENTS.md` | AI 操作指南 | P1 |
| `ai_architecture.json` | 架构配置 | P1 |

### 2.3 受保护文件等级

| 等级 | 文件 | 操作限制 |
|------|------|---------|
| **极高** | `.gstack_protected` | 禁止任何修改 |
| **高** | `AGENTS.md`, `index.json`, `ai_architecture.json` | 修改前必须备份到 CC/2_Old |
| **中** | `CC/*.md`, `.trae/*.md` | 建议备份后修改 |
| **低** | 普通代码文件 | 正常修改 |

---

## 3. GSTACK 工作流系统

### 3.1 什么是 GSTACK

**GSTACK = GitHub Tools Stack**，\python 的核心工作流引擎。

### 3.2 GSTACK 命令分类

#### 产品验证类

| 命令 | 说明 | 示例 |
|------|------|------|
| `office_hours` | YC 风格产品验证 | `gstack office_hours "我的AI工具"` |
| `plan_ceo_review` | CEO 视角评审 | `gstack plan_ceo_review` |
| `plan_eng_review` | 工程架构评审 | `gstack plan_eng_review` |

#### 代码质量类

| 命令 | 说明 | 示例 |
|------|------|------|
| `review` | 代码审查(带自动修复) | `gstack review file.py` |
| `investigate` | 根因分析 | `gstack investigate "崩溃原因"` |
| `qa` | 测试+自动修复 | `gstack qa` |
| `lint` | 代码质量检查 | `gstack lint` |

#### 部署发布类

| 命令 | 说明 | 示例 |
|------|------|------|
| `ship` | 自动化部署 | `gstack ship` |
| `document_release` | 更新文档 | `gstack document_release` |

#### 安全保护类

| 命令 | 说明 | 示例 |
|------|------|------|
| `careful` | 危险警告 | `gstack careful` |
| `freeze` | 文件锁定 | `gstack freeze file.py` |
| `guard` | 完全安全模式 | `gstack guard` |

#### 系统维护类

| 命令 | 说明 | 示例 |
|------|------|------|
| `skill_doctor` | Skills 自检与回滚 | `gstack skill_doctor` |
| `cc_cleanup` | CC 缓存清理 | `gstack cc_cleanup` |
| `git:status` | Git 状态检查 | `gstack git:status` |

### 3.3 GSTACK 调用方式

```python
# 方式1: 直接调用 (推荐)
from gstack_core import GStackCore
core = GStackCore()
result = core.execute("review", {"file": "test.py"})

# 方式2: CLI
python gstack_core.py review test.py

# 方式3: PowerShell
.\gstack_core\commands.ps1 -Command "review" -File "test.py"
```

### 3.4 工具链优先级

```
1. GSTACK 工作流      (最高优先级)
2. ASK (Agent Skill Kit)
3. Python 脚本
4. PowerShell 脚本
5. MCP 服务器
6. Batch 脚本
7. 系统命令           (最后手段)
```

---

## 4. MCP 分类系统

### 4.1 三类分类

```
MCP/
├── JM/     # 建模类 (Jiàn Mó)
├── BC/     # 代码类 (Biān Chéng)
└── Tools/  # 工具类
```

### 4.2 JM 建模类

**路径**: `\python\MCP\JM`

**关键词**: blender, 3d, modeling, character, scene, animation, mesh, texture, ue, godot, unity, vision, video

**主要文件**:
| 文件 | 用途 |
|------|------|
| `blender_mcp.py` | Blender MCP 主服务 |
| `blender_mcp_server.py` | Blender MCP 服务器 |
| `godot_mcp.py` | Godot MCP 主服务 |
| `ue5_manager.py` | UE5 管理器 |
| `unity_mcp.py` | Unity MCP 服务 |
| `scene_generator.py` | 场景生成器 |
| `vision_pro.py` | 视觉处理 |

### 4.3 BC 代码类

**路径**: `\python\MCP\BC`

**关键词**: code, github, git, find, fix, patch, verify, search, workflow, dev

**主要文件**:
| 文件 | 用途 |
|------|------|
| `github_workflow.py` | GitHub 工作流 |
| `github_dl.py` | GitHub 下载 |
| `code_quality.py` | 代码质量检查 |
| `find_prompt.py` | 提示查找 |
| `find_risk_check.py` | 风险检查 |
| `fix_all_blocking.py` | 修复所有阻塞 |
| `verify_one.py` | 单一验证 |
| `full_audit.py` | 完整审计 |

### 4.4 Tools 工具类

**路径**: `\python\MCP\Tools`

**关键词**: download, network, system, monitor, automation, config, memory, cache

**主要文件**:
| 文件 | 用途 |
|------|------|
| `aria2_mcp.py` | Aria2 下载管理 |
| `net_pro.py` | 网络工具 |
| `system_monitor.py` | 系统监控 |
| `gpu_config.py` | GPU 配置 |
| `ai_memory.py` | AI 记忆系统 |
| `aes_scan.py` | AES 密钥扫描 |
| `config_center.py` | 配置中心 |

### 4.5 文件分类决策

```python
def classify(filename: str, content: str = "") -> str:
    text = (filename + " " + content).lower()

    # JM 关键词
    jm_keywords = ["blender", "3d", "model", "mesh", "texture", "animation",
                   "scene", "character", "ue", "unity", "godot", "vision"]

    # BC 关键词
    bc_keywords = ["code", "github", "git", "find", "fix", "patch",
                   "verify", "search", "workflow", "dev", "lint"]

    for kw in jm_keywords:
        if kw in text:
            return "JM"

    for kw in bc_keywords:
        if kw in text:
            return "BC"

    return "Tools"
```

---

## 5. Skills 技能系统

### 5.1 技能架构

```
\python\MCP_Core\skills\
├── base.py              # 技能基类 (Skill, SkillRegistry)
└── [skill_name]/        # 各技能目录
    ├── skill.json       # 技能配置
    └── skill.py         # 技能实现
```

### 5.2 技能基类使用

```python
from skills.base import Skill, get_registry, skill

@skill(name="my_skill", description="我的技能", version="1.0")
class MySkill(Skill):
    def execute(self, action: str, params: dict) -> dict:
        if action == "hello":
            return {"success": True, "data": "Hello!"}
        return {"success": False, "error": "未知动作"}

# 调用
registry = get_registry()
result = registry.execute("my_skill", {"action": "hello"})
```

### 5.3 已注册技能 (29+)

| 类别 | 技能 | 说明 |
|------|------|------|
| GitHub | `smart_github_api_manager` | 智能 API 管理 |
| GitHub | `github_nlp_search` | 自然语言搜索 |
| GitHub | `github_pr_manager` | PR 管理 |
| GitHub | `github_issue_manager` | Issue 管理 |
| 系统 | `mcp_health_monitor` | 健康监控 |
| 系统 | `skill_doctor` | 技能自检 |
| 自动化 | `n8n_workflow` | n8n 工作流 |
| 自动化 | `automated_workflow` | 自动工作流 |
| Blender | `blender_mcp` | Blender 控制 |
| 部署 | `github_actions_manager` | Actions 工作流 |

---

## 6. CC 缓存系统

### 6.1 CC 是什么

**CC = Classification Cache**，\python 的文件历史博物馆。

### 6.2 三级缓存

```
CC/
├── 1_Raw/          # 原始文件 (网购、下载的最原始样子)
├── 2_Old/          # 旧版本 (被新版本替换后的旧文件)
└── 3_Unused/       # 未使用 (AI 未调用过的文件)
```

### 6.3 使用规则

| 缓存 | 用途 | 保留时间 |
|------|------|---------|
| 1_Raw | 网上下载的原始项目/文件 | 永久 |
| 2_Old | 被新版本替换的旧文件 | 永久 |
| 3_Unused | 超过 30 天未使用的文件 | 建议清理 |

### 6.4 CC 操作

```python
# 1. 新文件下载 -> 放入 1_Raw
shutil.copy("下载的文件.zip", "/python/CC/1_Raw/Projects/")

# 2. 文件更新 -> 旧版本移入 2_Old
shutil.move("/python/gstack_core/gstack_core.py",
            "/python/CC/2_Old/gstack_core_20260423.py")

# 3. 清理未使用 -> 移入 3_Unused
shutil.move("/python/temp/experiment.py",
            "/python/CC/3_Unused/experiment.py")
```

---

## 7. CLL_Projects 项目集合

### 7.1 什么是 CLL

**CLL = Collection of LLM Projects**，44 个主流 AI 开源项目。

### 7.2 项目分类

| 类别 | 项目数 | 示例 |
|------|--------|------|
| 大语言模型 | 6 | Qwen, ChatGLM, llama, pythia |
| 推理引擎 | 5 | vllm, llama.cpp, gpt-fast |
| 训练框架 | 5 | DeepSpeed, ColossalAI, ray |
| 量化工具 | 3 | AutoGPTQ, llm-awq |
| 微调工具 | 5 | LoRA, peft, trl, axolotl |
| 向量数据库 | 3 | milvus, qdrant |
| RLHF/RLAF | 3 | rl, spinningup, retro |
| 移动端 | 2 | MNN, orca |

### 7.3 常用项目路径

```bash
cd \python\CLL_Projects\Qwen      # 通义千问
cd \python\CLL_Projects\vllm      # 高性能推理
cd \python\CLL_Projects\trl       # 强化学习微调
cd \python\CLL_Projects\peft      # PEFT 库
cd \python\CLL_Projects\milvus    # 向量数据库
```

---

## 8. 保护规则与操作规范

### 8.1 必须遵守的规则

#### 必须 (MUST)

1. **必须**优先使用 GSTACK 工作流
2. **必须**将新 MCP 文件按 JM/BC/Tools 分类存放
3. **必须**在修改受保护文件前备份到 CC/2_Old
4. **必须**更新 CC 索引文件当移动文件时
5. **必须**使用环境变量存储敏感信息
6. **必须**在代码中包含错误处理

#### 禁止 (MUST NOT)

1. **禁止**修改 `.gstack_protected` 文件
2. **禁止**直接删除 CC 目录中的文件
3. **禁止**在 JM 目录存放代码类文件
4. **禁止**在 BC 目录存放建模类文件
5. **禁止**硬编码密码和 API 密钥
6. **禁止**执行未知来源的脚本

### 8.2 修改受保护文件流程

```
1. 确认修改必要性
   └─ 如果不必要，不要修改

2. 备份旧版本
   └─ 复制到 \python\CC\2_Old\[文件名]_[日期]

3. 更新 2_Old\INDEX.md
   └─ 记录备份信息

4. 执行修改
   └─ 小心操作

5. 验证修改
   └─ 确保系统正常

6. 更新相关索引
   └─ index.json, ai_architecture.json 等
```

### 8.3 新建文件流程

```python
# 1. 判断分类
# 建模 -> JM, 代码 -> BC, 其他 -> Tools

# 2. 选择正确目录
target_dir = "/python/MCP/BC"

# 3. 创建文件
file_path = Path(target_dir) / "my_new_tool.py"

# 4. 更新索引
# 编辑 /python/MCP/BC/README.md
# 编辑 /python/index.json
```

---

## 9. 故障排除

### 9.1 GSTACK 不可用

```python
# 检查
try:
    from gstack_core import GStackCore
    print("[OK] GSTACK 可用")
except ImportError:
    print("[FAIL] GSTACK 不可用")

# 处理
# 1. 检查文件是否存在
import os
os.path.exists("/python/gstack_core/gstack_core.py")

# 2. 进入降级模式 (strict)
# 仅提供只读服务
```

### 9.2 文件分类错误

```python
# 识别正确分类
if "blender" in filename or "3d" in filename:
    target = "/python/MCP/JM"
elif "code" in filename or "github" in filename:
    target = "/python/MCP/BC"
else:
    target = "/python/MCP/Tools"

# 移动文件
import shutil
shutil.move(wrong_path, os.path.join(target, filename))
```

### 9.3 技能注册失败

```python
# 检查技能基类
from skills.base import Skill

class MySkill(Skill):
    name = "my_skill"  # 必须设置
    description = "描述"

    def execute(self, action, params):
        pass

# 检查注册表
import json
with open("/python/.mcp/skills/registry.json") as f:
    registry = json.load(f)
```

### 9.4 备份失败

```bash
# 1. 检查磁盘空间
dir %BACKUP_DIR%

# 2. 检查权限
# 确保有写入 %BACKUP_DIR% 的权限

# 3. 手动运行测试
python \python\scripts\daily_backup.py --dry-run

# 4. 检查日志
type \python\logs\backup_log.md
```

---

## 10. 快速参考

### 10.1 目录速查

| 目录 | 用途 |
|------|------|
| `MCP/JM` | 3D 建模工具 |
| `MCP/BC` | 代码工具 |
| `MCP/Tools` | 系统工具 |
| `MCP_Core` | 核心系统 |
| `gstack_core` | GSTACK 引擎 |
| `CC/1_Raw` | 原始文件 |
| `CC/2_Old` | 旧版本 |
| `CC/3_Unused` | 未使用 |
| `CLL_Projects` | 44 个开源项目 |
| `scripts` | 自动化脚本 |

### 10.2 命令速查

| 命令 | 功能 |
|------|------|
| `gstack review file.py` | 代码审查 |
| `gstack ship` | 自动部署 |
| `gstack skill_doctor` | 技能自检 |
| `gstack cc_cleanup` | 缓存清理 |
| `gstack git:status` | Git 状态 |

### 10.3 系统检查

```bash
# 完整系统检查
python scripts/deep_check.py

# GSTACK 状态
python gstack_core.py status

# MCP 服务器状态
python MCP_Core/server.py status

# 备份
python scripts/daily_backup.py
```

---

> **文档结束**
>
> 完整架构文档: [AGENTS.md](AGENTS.md)
> 快速入门: [QUICK_START_TRAE.md](QUICK_START_TRAE.md)
