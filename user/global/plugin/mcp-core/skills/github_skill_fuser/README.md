# GitHub Skill 融合安装器 (github_skill_fuser)

安装 GitHub 项目为 Skill，先搜索类似项目理解生态，再融合最佳实践。

## 工作流程

```
用户请求安装 Skill
    ↓
搜索 GitHub 类似项目（理解生态，不只盯一个）
    ↓
分析目标仓库原理（结构、语言、入口点、SKILL.md）
    ↓
对比同类工具优缺点
    ↓
融合最佳设计，生成 Skill 文件
    ↓
安装到 \python\MCP_Core\skills\
    ↓
写知识库记录
```

## 融合原则

安装时对比多个类似项目：
- 触发词（triggers）取并集
- 命令结构参考最佳实践
- 保留原始 SKILL.md（如果有）
- 生成 Python 入口文件

## 命令

```bash
# 先找类似项目（理解生态）
python skill.py search-similar "browser automation agent"

# 分析仓库原理
python skill.py analyze-repo <repo_url>

# 安装为 Skill（下载 + 分析 + 融合）
python skill.py install <repo_url> [--skill-name <name>]

# 融合两个项目对比
python skill.py fuse <repo_url1> <repo_url2>
```

## 知识库记录

安装后自动写入：
- 技能名称
- 来源仓库
- 主语言
- 安装时间
