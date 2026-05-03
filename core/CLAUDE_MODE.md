# Claude Code 运作模式

> 在 \python 中复刻 Claude Code 的核心机制

---

## 🎯 核心特性

### 复刻的Claude Code机制

| 特性 | 实现 | 说明 |
|------|------|------|
| **nO主循环引擎** | `claude_mode.py` | 消息处理主循环 |
| **h2A消息队列** | `Queue` + `asyncio` | 异步消息处理 |
| **wU2上下文压缩** | `ContextManager` | 92%阈值自动压缩 |
| **工具系统** | `ToolRegistry` | 可扩展工具注册 |
| **SubAgent** | `SubAgent` 类 | 子任务并发执行 |
| **状态管理** | `AgentState` | 状态跟踪 |

---

## 🚀 使用方式

### 命令行

```bash
# 交互模式（复刻Claude Code）
claude

# 直接提问
claude "写快速排序"

# 代码模式
claude --code "Python爬虫"

# 审查代码
claude --review test.py

# 修复代码
claude --fix bug.py

# 生成文档
claude --doc func.py

# 生成测试
claude --test code.py

# 压缩上下文
claude --compact
```

### Python API

```python
from claude_mode import ClaudeAgent, ask, chat

# 创建Agent
agent = ClaudeAgent()

# 提问
response = ask("写快速排序")

# 对话模式
chat()

# 高级使用
agent.send("任务")
# 自动处理工具调用、上下文管理
```

---

## 🏗️ 架构

```
ClaudeAgent (nO主循环)
├── ContextManager (wU2压缩器)
│   ├── 消息存储
│   ├── Token估算
│   └── 自动压缩 (92%阈值)
├── ToolRegistry (工具系统)
│   ├── read_file
│   ├── write_file
│   ├── search_code
│   └── use_mcp
├── MessageQueue (h2A队列)
│   └── 异步处理
└── SubAgent (子Agent)
    └── 并发执行
```

---

## 💡 工作流程

### 1. 消息处理循环

```python
while running:
    message = queue.get()      # 从h2A队列获取
    intent = analyze(message)   # 分析意图
    if intent == "tool":
        result = execute_tool() # 执行工具
    response = call_ai()        # 调用AI
    context.add(response)       # 更新上下文
```

### 2. 上下文压缩

```python
if token_count / max_tokens > 0.92:
    # 保留系统消息 + 最近5条 + 摘要
    compress_context()
```

### 3. 工具调用

```python
# 自动识别工具需求
if "读文件" in prompt:
    result = tools.call("read_file", params)
```

---

## 📁 文件

```
\python\core\
├── claude_mode.py      # 核心实现
└── ai.py               # 统一入口（已集成）

\python\tools\
├── claude.py           # 命令行入口
└── claude.bat          # Windows快捷
```

---

## 🔧 扩展

### 添加自定义工具

```python
from claude_mode import get_agent

agent = get_agent()
agent.tools.register("my_tool", my_function)
```

### 创建SubAgent

```python
sub = agent.create_subagent("代码审查")
result = await sub.run("审查这段代码")
```

---

## 🎮 示例

```bash
# 进入项目目录
cd D:\myproject

# 启动Claude模式
claude

# 对话示例
> 分析项目结构
> 读文件 main.py
> 修复第10行的bug
> 生成测试
> /compact  # 压缩上下文
> exit
```

---

*复刻Claude Code核心机制，一句话完成编程任务*
