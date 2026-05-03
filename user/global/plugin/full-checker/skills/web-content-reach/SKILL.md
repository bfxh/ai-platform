---
name: "web-content-reach"
description: "全网内容检索技能，合规读取B站/小红书/GitHub等公开内容。Invoke when user needs to search or read public web content from Bilibili/Xiaohongshu/GitHub."
---

# 全网内容检索技能

## 概述

基于 [Agent-Reach](https://github.com/Panniantong/Agent-Reach) 的理念，实现AI合规读取全网公开内容的能力，解决本地AI信息滞后问题。

## 核心功能

- **B站内容检索**：读取B站公开视频信息、评论、弹幕
- **小红书内容检索**：读取公开笔记和攻略
- **GitHub内容检索**：读取仓库文档和代码
- **Reddit/YouTube检索**：读取公开讨论和视频信息
- **零API费用**：无需付费API密钥
- **本地部署**：数据不出本机

## 与您系统的映射

| Agent-Reach概念 | 您的系统对应 |
|----------------|-------------|
| 内容检索脚手架 | adapter/层 |
| 平台适配器 | adapter/software/ |
| 本地数据处理 | storage/层 |
| AI Agent集成 | core/dispatcher.py |

## 使用方法

### 搜索B站内容
```python
# 搜索B站AI教程
results = reach.search_bilibili("AI Agent 教程")
# 返回: 视频标题、UP主、播放量、简介
```

### 搜索小红书内容
```python
# 搜索小红书攻略
results = reach.search_xiaohongshu("Obsidian 知识管理")
# 返回: 笔记标题、作者、内容摘要
```

### 搜索GitHub项目
```python
# 搜索GitHub项目
results = reach.search_github("AI agent framework")
# 返回: 项目名、Stars、描述、README摘要
```

## 合规原则

- ✅ 仅读取平台公开可浏览内容
- ✅ 不涉及任何违规抓取行为
- ✅ 全程本地设备运算
- ✅ Cookie和数据不上传第三方
- ❌ 不用于商业用途
- ❌ 不破解平台规则

## 适用场景

- AI信息实时补充
- 行业资讯追踪
- 竞品分析
- 学习资源发现
- 内容创作参考

## 参考项目

- Agent-Reach: https://github.com/Panniantong/Agent-Reach (⭐15,075)