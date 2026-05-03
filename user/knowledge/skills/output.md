# Output Skill - 输出技能

## 功能
从知识系统中取材，生成各种格式的输出文件。

## 使用方法
```
请基于知识系统回答以下问题/生成以下内容：
[问题或任务描述]
```

## AI 行为规范

### 输出流程
1. **先检索** - 定位相关内容
2. **再读相关** - summary、concept、topic
3. **选择格式** - 根据任务目标选择输出形式
4. **生成文件** - 保存到 outputs/ 对应目录
5. **提出建议** - 如果发现系统缺口，提出补充建议

### 核心原则
- 先检索，再综合，再生成
- 输出结果尽量引用来源
- 高价值输出必须落文件
- 不把聊天记录当资产，文件才是资产

## 输出格式类型

### 问答输出 (qa/)

保存到 `/python/user/knowledge/outputs/qa/{日期}-{问题slug}.md`

```markdown
---
question: 问题描述
date: 2026-04-26
sources:
  - summaries/xxx.md
  - concepts/xxx.md
  - topics/xxx.md
---

# 问题

问题描述...

# 回答

回答内容...

## 参考来源

- [来源1](summaries/xxx.md)
- [来源2](concepts/xxx.md)
```

### 文章输出 (article/)

保存到 `/python/user/knowledge/outputs/article/{日期}-{主题slug}.md`

```markdown
---
title: 文章标题
date: 2026-04-26
author: AI Generated
tags:
  - 标签1
sources:
  - summaries/xxx.md
  - concepts/xxx.md
---

# 文章标题

## 摘要

...

## 正文

...

## 参考来源

- [来源1](summaries/xxx.md)
- [来源2](concepts/xxx.md)
```

### 研究备忘录 (memo/)

保存到 `/python/user/knowledge/outputs/memo/{日期}-{主题slug}.md`

```markdown
---
title: 研究备忘录标题
date: 2026-04-26
scope: 研究范围
sources:
  - summaries/xxx.md
  - concepts/xxx.md
---

# 研究备忘录

## 研究问题

...

## 关键发现

...

## 分析

...

## 结论

...

## 待研究问题

...
```

### 社交媒体输出 (social/)

保存到 `/python/user/knowledge/outputs/social/{日期}-{平台}-{主题slug}.md`

```markdown
---
platform: twitter|weibo|wechat
date: 2026-04-26
format: thread|short-post|poster
sources:
  - summaries/xxx.md
---

# 社交媒体内容

## Thread/Post 1

内容...

## Thread/Post 2

内容...

...
```

### PPT 输出 (ppt/)

保存到 `/python/user/knowledge/outputs/ppt/{日期}-{主题slug}.md`

```markdown
---
title: PPT 标题
date: 2026-04-26
slides: 10
sources:
  - summaries/xxx.md
---

# Slide 1: 标题页

标题
副标题

---

# Slide 2: 目录

1. 目录项1
2. 目录项2
...

---

# Slide 3: 内容页

标题

要点1
要点2
要点3
```

## 输出文件组织

```
outputs/
├── article/          # 长文
├── infographic/      # 信息图（图片说明稿、设计文案、生成脚本）
├── pdf/             # PDF 文档
├── ppt/             # PPT 演示
├── qa/              # 问答
├── memo/            # 研究备忘录
└── social/          # 社交媒体
```

> 输出天然是场景化的。最合理的做法是为不同输出类型创造不同 skill，让 skill 自己决定最合适的文件格式。
