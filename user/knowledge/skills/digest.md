# Digest Skill - 消化技能

## 功能
将原始材料编译成可以复用的知识结构。

## 使用方法
```
请消化以下文件，更新知识系统：
[文件路径或内容]
```

## AI 行为规范

### 做四件事
1. **生成结构化摘要** - 保存在 summaries/
2. **抽取概念** - 更新 concepts/
3. **更新主题页** - 更新 topics/
4. **更新总索引** - 更新 index/

### 核心原则
- 增量方式处理新增内容
- 每条结论尽量带来源
- 先抽象出概念，再组织主题
- 人负责判断，AI 负责整理和联结
- 不追求一次性完美分类，持续迭代就够

## 摘要输出

保存到 `/python/user/knowledge/knowledge/summaries/{日期}-{slug}.md`

```markdown
---
source: 来源
url: https://原始链接
date: 2026-04-26
digest_date: 2026-04-26
summary: |
  结构化摘要（3-5个要点）
key_findings:
  - 要点1
  - 要点2
  - 要点3
related_concepts:
  - 概念1
  - 概念2
tags:
  - 标签1
  - 标签2
---
```

## 概念卡输出

保存到 `/python/user/knowledge/knowledge/concepts/{概念slug}.md`

```markdown
---
concept: 概念名称
aliases:
  - 别名1
  - 别名2
definition: 一句话定义
source: 来源
date_created: 2026-04-26
last_updated: 2026-04-26
related_concepts:
  - 相关概念1
  - 相关概念2
tags:
  - 标签
---

## 详细笔记

详细笔记内容...

## 来源

- [来源1](url1)
- [来源2](url2)
```

## 主题页更新

保存到 `/python/user/knowledge/knowledge/topics/{主题slug}.md`

```markdown
---
topic: 主题名称
description: 主题描述
related_concepts:
  - 概念1
  - 概念2
key_summaries:
  - summaries/2026-04-26-summary1.md
  - summaries/2026-04-26-summary2.md
last_updated: 2026-04-26
---

## 概述

主题概述...

## 核心概念

### 概念1
- 定义
- 来源

### 概念2
- 定义
- 来源

## 相关主题

- [主题A](topics/a.md)
- [主题B](topics/b.md)
```

## 索引更新

更新 `/python/user/knowledge/knowledge/index/index.md`

```markdown
# 知识索引

## 最近更新
- {日期} {主题/概念名} [link](path)

## 概念
- {概念名} [link](concepts/xxx.md)

## 主题
- {主题名} [link](topics/xxx.md)

## 来源
- {来源名} [link](summaries/xxx.md)
```
