# Core 核心模块

> 19816L → 知识压缩 | 来源: \python\core\

## shared_context.py — 跨Agent共享上下文 (1123L)

### 设计原则
- 每个Agent只写自己数据→消灭写冲突
- JSONL追加式日志→无需锁(NTFS <4KB原子)
- filelock保护读-改-写
- Marker机制: 每Agent独立追踪读取位置
- 优雅降级: 模块缺失退回单Agent模式

### 六大子系统

| 子系统 | 职责 | 核心方法 |
|--------|------|----------|
| AgentRegistry | 注册/心跳/发现/清理 | register_agent(id,type,pid,session,capabilities), update_heartbeat, discover_agents, cleanup_dead_agents(timeout=60s) |
| TaskBoard | 任务/冲突检测 | create_task, check_file_conflicts(支持**递归), get_active_tasks |
| ContextBroadcaster | 上下文广播 | broadcast(agent_id,summary,key_files,key_decisions), get_all_contexts |
| FileOperationLog | 文件操作日志 | log_operation(追加无锁), poll_new_operations(基于marker) |
| KnowledgeSyncQueue | 知识同步 | push_knowledge(title,content,category,tags,importance), pull_knowledge(agent_id,limit) |
| ResolvedContext | 全局快照 | resolve(registry,task_board,broadcaster,file_log)→合并+冲突检测 |

### 配置
```python
polling_interval: 3s, lock_timeout: 5s, heartbeat_interval: 15s, dead_agent_timeout: 60s
max_file_ops_log: 10000, max_knowledge_queue: 5000
```

### 存储: /python/storage/shared_context/
agents_registry.json, task_board.json, context_broadcasts.json, file_operations.log, knowledge_sync_queue.log, markers/{agent_id}.json

依赖: filelock

## ai_adapter.py — 统一AI适配层 (869L)

### 提供商枚举
STEPFUN/OPENAI/ANTHROPIC/GEMINI/OLLAMA/DEEPSEEK/QWEN/DOUBAO/XIAOLONGXIA/LOCAL_CLAUDE

### 数据类
Message(role,content,metadata), ChatRequest(messages,model,temperature,max_tokens,stream,tools), ChatResponse(content,model,usage,finish_reason)

### 类层次: BaseAIClient(ABC) → 10个Provider实现
工厂: AIClientFactory.create(provider) / get_instance(单例)
统一接口: UnifiedAI.chat(message,keep_history,temperature,max_tokens) / switch_provider / __call__

### 各Provider默认
| Provider | Base URL | Model |
|----------|----------|-------|
| StepFun | api.stepfun.com/v1 | step-1-8k |
| OpenAI | api.openai.com/v1 | gpt-4o-mini |
| Anthropic | api.anthropic.com/v1 | claude-3-5-sonnet |
| Gemini | generativelanguage.googleapis.com/v1beta | gemini-2.0-flash |
| Ollama | localhost:11434 | llama3.2 |
| DeepSeek | api.deepseek.com/v1 | deepseek-chat |
| Qwen | dashscope.aliyuncs.com | qwen-max |
| Doubao | ark.cn-beijing.volces.com | doubao-pro-32k |
| LocalClaude | D:\Claude_Extracted | subprocess |

依赖: urllib.request(无第三方HTTP库)

## ai_collaboration.py — 多AI协作 (852L)

### 协作模式
SINGLE/PARALLEL/SEQUENTIAL/DEBATE/VOTE/CASCADE/SPECIALIST

### 算法
- PARALLEL: ThreadPoolExecutor并行, 综合结果用第一个模型
- SEQUENTIAL: 链式, 输出作下一步输入
- DEBATE: 多轮: 各自观点→互相评论→最终结论
- VOTE: 各自生成→互相评估→得票最高胜出
- CASCADE: 默认3阶段: 生成→优化→审查
- SPECIALIST: 并行专家+组合, 关键词自动匹配分工

### SmartRouter任务映射
coding→SPECIALIST(openai/claude/deepseek), writing→PARALLEL(claude/openai), analysis→DEBATE(openai/claude), translation→VOTE(qwen/stepfun/doubao), creative→PARALLEL(claude/gemini), math→VOTE(openai/deepseek), general→SINGLE(stepfun/openai)

## dispatcher.py — TRAE能力调度器 (595L)

能力签名: skill.yaml/mcp.json/cli.yaml/workflow.yaml/agent.yaml/plugin.toml/model.yaml
SandboxManager: 隔离执行(.py/.ps1), 超时控制, 快照到trash
Dispatcher: scan→register→dispatch(按类型分发: mcp→HTTP→subprocess, workflow→engine, cli→sandbox)

## pipeline_engine.py — 五阶段强制管道 (436L)

| 阶段 | 内容 |
|------|------|
| ANALYSIS(1) | 架构扫描/依赖映射/特性识别 |
| SECURITY(2) | 漏洞/密钥/依赖漏洞/配置审计 |
| REVERSE(3) | 许可证/开源验证/二进制/反编译 |
| DEEP(4) | 交叉分析前三阶段/风险重评 |
| DEV(5) | 编码/建模/测试/部署 |

Gate机制: GateStatus(PASSED/BLOCKED/WARNING/SKIPPED/FAILED), can_proceed()=PASSED/WARNING/SKIPPED
CRITICAL安全发现自动阻塞Phase5
CLI: python pipeline_engine.py -p <path> [-n name] [--phase 1-5] [--force]

## knowledge_manager.py — 复利知识系统 (397L)

四步: ingest(标准化→raw/)→digest(摘要+概念+主题→knowledge/)→output(问答→outputs/)→inspect(审计→inspection/)
CLI: python knowledge_manager.py ingest|digest|output|inspect|search|stats

## context_manager.py — 上下文管理 (252L)

核心: add_message→get_context(max_tokens)→compress(保留代码块+关键词行,最多10行)→clean(keep_recent)
count_tokens: tiktoken(cl100k_base)→len/4估算
switch_project: 压缩→清理→广播SharedContext
文件: /python/user/context.json, compressed_context.json

## model_info_manager.py — 模型信息 (187L)

预设12模型: gpt-4o(128K), claude-3-opus(200K), gemini-1.5-pro(1M), qwen2.5-72b(128K), deepseek-coder-v2(160K)等
存储: /python/storage/models/model_info.json

## mcp_lite.py — 轻量MCP (247L)

MCPCapability: FILE/CODE/SEARCH/BROWSER/DB/DESIGN/MEDIA
内置处理器: file(read/write/list), code(analyze/review/fix/explain→router.do), search(→router.do), browser(fetch), db(SQLite,拦截DROP/DELETE/TRUNCATE/ALTER), design(→router.do)
全局实例: mcp("file:read:test.py")

## sandbox.py — 沙盒执行 (354L)

进程隔离+删除拦截(monkey-patch os.remove/shutil.rmtree)+超时监控+快照保存
SandboxManager.execute(command,args,env,cwd,timeout,permissions)→SandboxResult
默认: trash=/python/storage/trash, timeout=600s, 删除需显式permissions={"delete":True}

## router.py — 智能路由 (240L)

算法: 缓存(SHA256)→复杂度(SIMPLE<100字→本地ollama-7b, NORMAL<1000字→云端step-1-8k, COMPLEX≥1000字→step-1-32k)
便捷: do(prompt) / code(prompt) / review(prompt) / design(prompt) / analyze(prompt)

## workflow_engine.py — 工作流引擎 (224L)

load_workflow(YAML)→拓扑排序→逐节点执行(cli/skill/mcp)→context传递→报告
CLI: python workflow_engine.py <workflow.yaml> <project_name>

## 跨模块依赖

```
shared_context ← (核心, 被所有模块依赖)
  ↑ context_manager, pipeline_engine, dispatcher
ai_adapter ← ai_collaboration
router ← mcp_lite
sandbox ← dispatcher
workflow_engine ← dispatcher
knowledge_manager (独立)
model_info_manager (独立)
```

外部依赖: filelock(必须), yaml(必须), toml(必须), tiktoken(可选)
