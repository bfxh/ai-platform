---
question: 我该怎么吸取这篇文档的知识系统方法论？
date: 2026-04-29
sources:
  - summaries/2026-04-29-compound-engineering-knowledge-system.md
  - concepts/compound-engineering.md
  - concepts/file-over-app.md
  - concepts/incremental-update.md
  - topics/compound-engineering-knowledge-system.md
---

# 问题

我该怎么吸取这篇文档的知识系统方法论？

# 回答

吸取这篇文档的方法论，不是"读完记住"，而是**用它的方法来处理它本身**。具体分三步：

## 1. 先跑通最小闭环（已完成）

你已经做到了：
- ✅ **摄取**：把文档内容存入 `raw/2026-04-29-compound-engineering-knowledge-system.md`
- ✅ **消化**：生成了 1 个摘要、5 个概念卡、1 个主题页、1 个索引
- 🔄 **输出**：就是你现在读到的这个 QA 文件
- ⏳ **巡检**：下一步执行

这一轮跑通，系统雏形就有了。

## 2. 日常使用中持续喂养系统

从现在开始，每次你遇到有价值的内容，就执行一次四步流程：

| 你做什么 | 对应步骤 | AI 做什么 |
|----------|----------|-----------|
| 发一个 URL 或粘贴一段内容 | 摄取 | 清洗、标准化、存入 raw/ |
| 说"消化一下" | 消化 | 生成摘要、抽取概念、更新主题页和索引 |
| 提一个问题 | 输出 | 从知识系统取材回答，存入 outputs/qa/ |
| 说"巡检一下" | 巡检 | 扫描系统问题，生成报告 |

**关键习惯**：不要只聊天，要让每次高价值产出落文件。

## 3. 遇到新来源时扩展摄取能力

文档里提到的核心思路是：**每当你遇到摄取不了的文件格式，就让 AI 研究如何成功获取，成功后把经验写回 skills**。

比如：
- 想摄取小红书文章 → 让 AI 研究方案 → 成功后更新 ingest.md
- 想摄取播客 transcript → 让 AI 写脚本 → 成功后更新 ingest.md
- 想摄取 YouTube 视频 → 安装 youtube-transcript skill → 更新 ingest.md

这样 skills 会随着使用越来越强大，成为你的个人资产。

## 已知结论 vs 推断

- **已知结论**：四步工作流（摄取→消化→输出→巡检）是文档明确提出的
- **已知结论**：三个基本原则（文件优先、增量更新、可追溯）是系统设计基础
- **推断**：日常使用中，摄取和输出会最频繁，消化和巡检可以批量进行
- **待确认**：你的具体使用场景（主要摄取什么类型的内容）会影响 skills 的优先扩展方向

## 参考来源

- [摘要](summaries/2026-04-29-compound-engineering-knowledge-system.md)
- [概念：Compound Engineering](concepts/compound-engineering.md)
- [概念：文件优先](concepts/file-over-app.md)
- [概念：增量更新](concepts/incremental-update.md)
- [主题页](topics/compound-engineering-knowledge-system.md)
