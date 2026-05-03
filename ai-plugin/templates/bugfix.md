---
name: bugfix
description: Bug 修复任务模板
version: "1.0"
---

# Bug 修复: [Bug 简述]

## 现象
[用户看到什么？什么不工作？]

## 复现步骤
1. [第一步]
2. [第二步]
3. [观察到的错误]

## 根因分析
[代码中哪里出了问题？为什么？]

## 修复方案
[打算怎么修？为什么这样修？]

## 涉及文件
- [ ] `path/to/file1.py` — [改动说明]

## Bug 记忆
- **首次出现**: [是/否]
- **复发次数**: [N]
- **错误分类**: [import / syntax / logic / permission / network / encoding]
- **反模式标记**: [是/否，>=3 次复发自动标记]

## 验收标准
- [ ] 复现步骤不再触发错误
- [ ] 无回归 (现有功能不受影响)
- [ ] Brain post_task 记录 (含 fix_description)
- [ ] 遵循 coding-style.md 代码规范

## 执行记录
- Brain pre_task: [结果]
- Bug 召回: [历史相关 bug]
- 修复: [做了什么]
- Brain post_task: [成功 + bug_id]
