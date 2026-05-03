# AI 集成平台 - 快速教程

> 从零开始，30 分钟掌握 AI 集成平台的核心用法

---

## 目录

1. [环境搭建](#1-环境搭建)
2. [第一次 AI 对话](#2-第一次-ai-对话)
3. [多提供商切换](#3-多提供商切换)
4. [使用 GSTACK 工作流](#4-使用-gstack-工作流)
5. [创建自定义 Skill](#5-创建自定义-skill)
6. [创建自定义 Plugin](#6-创建自定义-plugin)
7. [MCP 服务器开发](#7-mcp-服务器开发)
8. [游戏自动化测试](#8-游戏自动化测试)
9. [AI 记忆系统](#9-ai-记忆系统)
10. [常见问题](#10-常见问题)

---

## 1. 环境搭建

### 1.1 克隆与安装

```bash
git clone https://github.com/bfxh/ai-platform.git \python
cd \python
pip install -r requirements.txt
```

### 1.2 配置 API Key

至少配置一个 AI 提供商的 API Key：

```powershell
# 方式一：环境变量（临时）
$env:STEPFUN_API_KEY = "sk-xxx"

# 方式二：写入 PowerShell 配置文件（永久）
Add-Content $PROFILE '$env:STEPFUN_API_KEY = "sk-xxx"'
```

### 1.3 (可选) 安装 Ollama 本地模型

```bash
# 安装 Ollama: https://ollama.com/download
# 拉取模型
ollama pull qwen2.5-coder:7b
ollama pull deepseek-coder:6.7b
```

### 1.4 (可选) 安装 MCP 服务器

```bash
cd user/global/plugin/agents-md && npm install
cd user/global/plugin/ollama-bridge && npm install
```

### 1.5 验证安装

```python
python -c "from core.ai_new import AI; ai = AI(); print(ai('Hello!'))"
```

---

## 2. 第一次 AI 对话

### 2.1 Python 交互

```python
from core.ai_new import AI

# 创建实例（使用默认提供商 stepfun）
ai = AI()

# 简单提问
result = ai("什么是量子计算？")
print(result)

# 带历史记录的对话
response1 = ai.chat("你好，我叫小明")
response2 = ai.chat("我叫什么名字？")  # AI 会记住"小明"

# 代码生成
code = ai.write_code("用 Python 实现快速排序")
print(code)

# 代码审查
review = ai.review_code(code)
print(review)

# 代码修复
fixed = ai.fix(code)
print(fixed)
```

### 2.2 快捷函数

```python
from core.ai_new import ask, chat, write_code

# 单次提问（不保持历史）
result = ask("1+1等于几？", provider="stepfun")

# 代码生成
code = write_code("写一个 HTTP 服务器")
```

### 2.3 命令行使用

```bash
# 通过 GSTACK CLI
python gstack_core.py status
```

---

## 3. 多提供商切换

### 3.1 支持的提供商

| 提供商 | 标识符 | 环境变量 |
|--------|--------|----------|
| 阶跃AI | `stepfun` | `STEPFUN_API_KEY` |
| OpenAI | `openai` | `OPENAI_API_KEY` |
| Anthropic | `claude` | `ANTHROPIC_API_KEY` |
| Google Gemini | `gemini` | `GEMINI_API_KEY` |
| Ollama (本地) | `ollama` | 无需 |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` |
| 通义千问 | `qwen` | `QWEN_API_KEY` |
| 豆包 | `doubao` | `DOUBAO_API_KEY` |

### 3.2 运行时切换

```python
from core.ai_new import AI

ai = AI(provider="stepfun")           # 初始化用阶跃
ai.switch_provider("openai")          # 切换到 OpenAI
ai.switch_provider("ollama")          # 切换到本地模型

# 指定模型
ai = AI(provider="qwen", model="qwen-max")
ai = AI(provider="ollama", model="qwen2.5-coder:7b")
```

### 3.3 本地模型 (Ollama)

```python
# 使用本地模型，无需 API Key
ai = AI(provider="ollama", model="qwen2.5-coder:7b")
result = ai("帮我写一个 Python 脚本")
```

---

## 4. 使用 GSTACK 工作流

GSTACK 是平台的核心编排引擎，所有修改类操作必须通过它审计。

### 4.1 常用命令

```bash
# 查看系统状态
python gstack_core.py status

# 代码审查（带自动修复）
python gstack_core.py review my_script.py

# 测试 + 自动修复
python gstack_core.py qa

# 仅报告不修复
python gstack_core.py qa_only

# 自动化部署
python gstack_core.py ship

# 根因分析
python gstack_core.py investigate

# CEO 视角评审
python gstack_core.py plan_ceo_review

# 工程架构评审
python gstack_core.py plan_eng_review

# Skills 自检
python gstack_core.py skill_doctor

# CC 缓存清理
python gstack_core.py cc_cleanup
```

### 4.2 工作流优先原则

```
所有修改操作 → GSTACK 审计 → 执行 → 记录 → 可回滚
```

---

## 5. 创建自定义 Skill

### 5.1 目录结构

```
user/global/skill/my-skill/
├── skill.yaml      # 技能定义
├── skill.py        # 入口脚本
└── README.md       # 说明文档
```

### 5.2 编写 skill.yaml

```yaml
name: my-skill
entry: skill.py
description: 我的自定义技能
timeout: 600
permissions:
  network: true
  filesystem: ["./"]
tags: [custom, utility]
```

### 5.3 编写入口脚本

```python
# skill.py
import sys

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: skill.py <input>")
        return
    result = process(args[0])
    print(result)

def process(input_text):
    return f"Processed: {input_text}"

if __name__ == "__main__":
    main()
```

---

## 6. 创建自定义 Plugin

### 6.1 目录结构

```
user/global/plugin/my-plugin/
├── plugin.toml     # 插件定义
├── server.py       # MCP 服务器 (可选)
├── skills/         # 包含的技能
│   └── my-skill/
└── README.md
```

### 6.2 编写 plugin.toml

```toml
name = "my-plugin"
version = "1.0.0"
description = "我的自定义插件"

[includes]
skills = ["my-skill"]
mcps = ["my-mcp"]

[dependencies]
plugins = ["mcp-core"]
```

---

## 7. MCP 服务器开发

### 7.1 最简 MCP 服务器

```python
# server.py
import json
import sys

def handle_request(request):
    method = request.get("method", "")
    if method == "tools/list":
        return {
            "tools": [{
                "name": "hello",
                "description": "Say hello",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                }
            }]
        }
    elif method == "tools/call":
        name = request["params"]["arguments"]["name"]
        return {"content": [{"type": "text", "text": f"Hello, {name}!"}]}

for line in sys.stdin:
    request = json.loads(line)
    response = handle_request(request)
    print(json.dumps(response), flush=True)
```

### 7.2 注册到 mcp.json

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["path/to/server.py"],
      "description": "My custom MCP server"
    }
  }
}
```

---

## 8. 游戏自动化测试

### 8.1 测试流程

```
启动游戏 → 主菜单 → 进入游戏 → 基础操控 → 玩法测试 → 稳定性 → 退出
```

### 8.2 使用测试框架

```python
from core.game_test_framework import GameTestFramework

framework = GameTestFramework(game_name="Minecraft")
framework.launch_game()
framework.wait_for_main_menu(timeout=60)
framework.enter_world("TestWorld")
framework.test_movement(duration=30)
framework.take_screenshot("movement_test")
framework.exit_game()
```

### 8.3 测试规则

- 必须以玩家身份执行，不得仅凭文件存在判定通过
- 每个测试阶段必须截图留证
- 发现 Bug 记录到 `PROBLEMS.md`

---

## 9. AI 记忆系统

### 9.1 Compound Engineering 四步工作流

```
摄取 (Ingest) → 消化 (Digest) → 输出 (Output) → 巡检 (Patrol)
```

### 9.2 使用知识管理器

```python
from core.knowledge_manager import KnowledgeManager

km = KnowledgeManager()

# 摄取知识
km.ingest("Python 3.12 新增了 type alias 语法")

# 查询知识
result = km.query("Python 3.12 有什么新特性？")

# 巡检（定期整理）
km.patrol()
```

---

## 10. 常见问题

### Q: pip install 报错怎么办？

```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: Ollama 连接失败？

```bash
# 确保 Ollama 服务已启动
ollama serve

# 检查模型列表
ollama list
```

### Q: API Key 无效？

```powershell
# 检查环境变量
echo $env:STEPFUN_API_KEY
echo $env:OPENAI_API_KEY
```

### Q: GSTACK 命令找不到？

```bash
# 确保在 \python 目录下执行
cd \python
python gstack_core.py status
```

---

## 下一步

- 阅读 [AGENTS.md](AGENTS.md) 了解完整的 AI 操作规则
- 阅读 [specifications/README.md](specifications/README.md) 了解能力单元规范
- 查看 [ai_architecture.json](ai_architecture.json) 了解架构配置
- 探索 [storage/mcp/](storage/mcp/) 下的 MCP 工具
