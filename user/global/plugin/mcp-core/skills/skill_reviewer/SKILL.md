# Skill Reviewer & Mindmap Generator

## 描述
小龙虾行为审查系统——审查所有已安装Skill的质量、安全、依赖，并生成工作流思维导图。

## 功能

### 1. Skill审查
- 安全扫描：检测shell注入、eval/exec、危险库调用
- 文档完整性：SKILL.md / README.md / skill.json
- 代码质量：行数统计、依赖提取
- 评分：0-100分，pass/warn/fail三档

### 2. 思维导图生成
- 全局视图：所有Skill与Workflow的依赖关系
- 单Skill视图：审查维度的树状分解
- 输出格式：JSON（D3.js）/ Mermaid语法

### 3. 完整审计
- 一次性审查所有Skill
- 生成综合报告
- 统计通过率、平均分

## 用法

```bash
# 审查指定Skill
python /python/MCP_Core/skills/skill_reviewer/skill.py review ai_toolkit_ecosystem

# 生成全局思维导图
python /python/MCP_Core/skills/skill_reviewer/skill.py mindmap

# 生成单Skill思维导图
python /python/MCP_Core/skills/skill_reviewer/skill.py mindmap -s github_opensource

# 输出Mermaid格式
python /python/MCP_Core/skills/skill_reviewer/skill.py mindmap --format mermaid -o diagram.mmd

# 运行完整审计
python /python/MCP_Core/skills/skill_reviewer/skill.py audit
```

## MCP调用
```json
{
  "skill": "skill_reviewer",
  "action": "review",
  "params": {"skill_name": "ai_toolkit_ecosystem"}
}
```
