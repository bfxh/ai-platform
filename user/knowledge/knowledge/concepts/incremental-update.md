---
id: concept-incremental-update
title: 增量更新
type: concept
created_at: 2026-04-29
updated_at: 2026-04-29
aliases:
  - incremental processing
  - 增量处理
related:
  - compound-engineering
  - traceability
sources:
  - 2026-04-29-compound-engineering-knowledge-system-001
---

## Definition

只处理新增内容，不要每次重建全库。消化步骤只处理新增或指定的 raw 文件，先复用已有概念和主题页，必要时再新建。

## Why It Matters

全量重建成本高且不可持续。增量更新让系统可以持续运行而不会越来越慢，也保证了历史数据的稳定性。

## Where It Appears

- 消化阶段：只处理新增 raw 文件
- 概念抽取：先映射到已有概念库
- 主题页：先判断应更新哪些已有主题页

## Notes

增量更新的前提是文件命名和结构保持一致，这样才能准确判断什么是"新增"的。
