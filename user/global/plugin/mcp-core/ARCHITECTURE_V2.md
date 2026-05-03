# MCP Core System v2 - 精简架构设计

## 设计原则
1. **单一职责**：每个组件只做一件事
2. **实际可用**：去除只有文档没有实现的组件
3. **统一入口**：所有功能通过统一MCP Server暴露
4. **最小依赖**：优先使用标准库

---

## 核心组件清单（精简后）

### 1. MCP Server (统一入口)
```
\python\MCP_Core\server.py
- 统一MCP协议处理
- 工具注册与路由
- 请求/响应标准化
```

### 2. 配置中心
```
\python\MCP_Core\config.py
- 统一配置管理
- 环境变量支持
- 配置热加载
```

### 3. 工作流引擎
```
\python\MCP_Core\workflow\engine.py
- 工作流执行
- 依赖解析
- 状态管理
```

### 4. 事件总线
```
\python\MCP_Core\event_bus.py
- 技能间通信
- 异步事件处理
```

### 5. 核心技能（实际实现）
```
\python\MCP_Core\skills\network_transfer\    # 网络传输
\python\MCP_Core\skills\exo_cluster\          # EXo集群
\python\MCP_Core\skills\notification\         # 通知服务
\python\MCP_Core\skills\system_config\        # 系统配置
```

### 6. 基础工具（保留现有可用工具）
```
\python\MCP_Core\tools\da.py                  # 桌面自动化（现有可用）
\python\MCP_Core\tools\ai_memory.py           # 记忆系统（现有可用）
\python\MCP_Core\tools\net_pro.py             # 网络工具（现有可用）
```

---

## 移除/合并的组件

| 原组件 | 处理方式 | 原因 |
|--------|----------|------|
| mcp_workflow.py | 合并到 workflow/engine.py | 功能重叠 |
| unified_workflow.py | 合并到 workflow/engine.py | 功能重叠 |
| smart_workflow.py | 作为插件集成 | 依赖其他工作流 |
| 所有skill目录的SKILL.md | 转为Python实现 | 只有文档无代码 |
| 分散的配置文件 | 统一到 config.yaml | 配置分散 |

---

## 目录结构

```
\python\MCP_Core\
├── server.py                    # MCP Server主入口
├── config.py                    # 配置中心
├── config.yaml                  # 配置文件
├── event_bus.py                 # 事件总线
├── ARCHITECTURE_V2.md           # 本文档
│
├── workflow\                    # 工作流引擎
│   ├── __init__.py
│   ├── engine.py               # 核心引擎
│   ├── executor.py             # 执行器
│   ├── plugins\                # 插件
│   │   ├── memory.py
│   │   └── notification.py
│   └── templates\              # 工作流模板
│       ├── dual_pc_setup.json
│       └── transfer.json
│
├── skills\                      # 技能实现
│   ├── __init__.py
│   ├── base.py                 # 技能基类
│   ├── registry.py             # 技能注册
│   ├── network_transfer\       # 网络传输技能
│   │   ├── __init__.py
│   │   ├── skill.py
│   │   ├── sender.py
│   │   └── receiver.py
│   ├── exo_cluster\            # EXo集群技能
│   │   ├── __init__.py
│   │   ├── skill.py
│   │   └── node.py
│   ├── notification\            # 通知技能
│   │   ├── __init__.py
│   │   └── skill.py
│   └── system_config\           # 系统配置技能
│       ├── __init__.py
│       └── skill.py
│
└── tools\                       # 基础工具
    ├── __init__.py
    ├── da.py                   # 桌面自动化
    ├── ai_memory.py            # 记忆系统
    └── net_pro.py              # 网络工具
```

---

## 快速开始

```bash
# 启动MCP Server
python \python\MCP_Core\server.py

# 调用技能
python \python\MCP_Core\server.py call network_transfer.send --target 192.168.1.10 --file test.txt

# 执行工作流
python \python\MCP_Core\server.py workflow dual_pc_setup
```
