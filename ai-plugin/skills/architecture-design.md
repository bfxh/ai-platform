---
name: architecture-design
description: 架构设计 — 设计系统架构、组件关系、数据流和技术选型
version: "1.0"
category: design
tags: [architecture, design, system, planning]
---

# 架构设计 Architecture Design

## 执行步骤

1. **需求分析**: 理解业务需求和技术约束
2. **现状评估**: 检查现有架构 (`/python/ai_architecture.json`)
3. **方案设计**:
   - 组件划分: 哪些是独立模块？
   - 数据流: 数据如何在组件间流动？
   - 接口定义: 组件间如何通信？
   - 技术选型: 使用什么技术栈？为什么？
4. **风险评估**: 识别技术风险点和缓解措施
5. **文档输出**: 更新架构文档或生成设计说明

## 设计原则

- **优先使用现有能力单元** — 不重复造轮子
- **简单优于复杂** — 最小可行架构，渐进增强
- **分离关注点** — 每个模块只做一件事
- **优先使用弱耦合** — 通过接口/消息通信，而非直接依赖
- **可观测性** — 日志、监控、调试基础设施先行

## \python 平台架构参考

现有架构分层:
```
用户层 (user/)        — 用户配置、技能、插件
核心层 (core/)        — dispatch、pipeline、shared_context
存储层 (storage/)     — Brain、MCP、CLL、CC
适配层 (adapter/)     — 外部工具集成
规格层 (specifications/) — 输出标准、架构规范
```

## 架构修改规则

- 修改 `ai_architecture.json` 前必须备份 (时间戳)
- 新增组件需要注册到 `core/dispatcher.py`
- 新增 MCP 需按分类添加 (JM/BC/Tools)
- 确保向下兼容现有 Agent 配置
