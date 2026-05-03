---
id: concept-traceability
title: 可追溯
type: concept
created_at: 2026-04-29
updated_at: 2026-04-29
aliases:
  - traceability
  - 来源可追溯
related:
  - file-over-app
  - incremental-update
sources:
  - 2026-04-29-compound-engineering-knowledge-system-001
---

## Definition

任何结论都能追溯到原始来源。所有结论尽量引用来源，发现冲突时显式标记而不是静默覆盖。

## Why It Matters

没有审计和可追溯性，系统会越来越不可信。这是"让 AI 静默修改知识库"被列为误区的原因。

## Where It Appears

- 摄取阶段：保留来源、时间、作者、链接元信息
- 消化阶段：每条结论带来源，概念卡和主题页都有 sources 字段
- 输出阶段：尽量引用具体来源文件
- 巡检阶段：检查缺少来源支持的结论

## Notes

可追溯性是系统可信度的基石。如果一条结论找不到来源，它的价值就要打折扣。
