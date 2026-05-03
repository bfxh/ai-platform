# Ingest Skill - 摄取技能

## 功能
将外部输入（网页、推文、笔记、播客、对话）统一转换为标准化 Markdown 文件。

## 使用方法
```
请摄取以下内容到知识系统：
[粘贴内容或提供URL]
```

## AI 行为规范

### 只做四件事
1. **抽取正文** - 提取核心内容
2. **清理噪音** - 去除广告、导航等无关内容
3. **保留元数据** - 来源、时间、作者、链接
4. **输出标准化文件** - 保存到 raw/ 目录

### 不做这些
- 不写观点
- 不写结论
- 不做概念抽取
- 不做深度总结

## 输出格式

保存到 `/python/user/knowledge/raw/{日期}-{源slug}.md`

```markdown
---
source: 来源名称
url: https://原始链接
date: 2026-04-26
author: 作者名
type: article|tweet|video|podcast|doc
---

# 标题

## 正文内容

原始正文内容...

## 注释

（如有额外元数据或处理说明）
```

## 文件命名规范

- 日期放前面：`YYYY-MM-DD-`
- 后面跟稳定 slug
- 不要依赖平台随机标题

示例：
- `2026-04-26-karpathy-ai-knowledge-management.md`
- `2026-04-26-twitter-ai-future-discussion.md`
- `2026-04-26-podcast-llm-deep-dive.md`
