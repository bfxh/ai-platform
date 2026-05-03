# \python\storage\ — 存储层说明

## 目录结构

```
storage/
├── mcp/                    # MCP服务器存储
│   ├── JM/                # 建模类 (Blender, UE, Unity, Godot, 3D)
│   ├── BC/                # 代码类 (GitHub, Code, Search, Fix)
│   └── Tools/             # 工具类 (Download, Monitor, Config, System)
├── cll/                   # CLL 开源LLM项目集合 (44个项目)
├── Brain/                 # AI记忆系统
│   ├── memory/            # 记忆引擎 (engine.py + recall.py)
│   ├── growth/            # 成长追踪 (tracker.py)
│   ├── supervisor/        # 合规审计 (audit.py)
│   ├── thinking/          # 思维框架 (frameworks.json)
│   ├── topics/            # 话题索引 (392条)
│   └── integration/       # 事件桥接 (event_bridge.py)
├── data/                  # 运行时数据
│   ├── test_results.db    # 统一测试数据库
│   └── pipeline_reports/  # Pipeline报告存档
├── skills/                # Skill 描述文件
├── mcps/                  # MCP 服务配置
├── workflows/             # Workflow 定义
├── agents/                # Agent 配置
├── plugins/               # 第三方插件配置
├── daily/                 # 每日摘要 JSON
├── CC/                    # 分类缓存 (1_Raw/2_Old/3_Unused)
├── models/                # 模型信息与AI工具对比数据
└── trash/                 # 沙盒垃圾堆
```

## 能力单元优先级

当需要解决问题时，按以下顺序检查本地能力：

1. **Skill** → `/python/user/global/skill/`
2. **MCP** → `/python/storage/mcp/` (JM → BC → Tools)
3. **CLL** → `/python/storage/cll/`
4. **Workflow** → workflow.yaml 定义
5. **Agent** → agent.yaml 定义
6. **Plugin** → `/python/user/global/plugin/`

## 维护规则
- 所有能力单元必须注册到 `core/dispatcher.py`
- 新文件必须按分类存放 (JM/BC/Tools)
- CC目录每30天审查清理
- Brain系统自动管理记忆持久化
- Pipeline报告保留90天
