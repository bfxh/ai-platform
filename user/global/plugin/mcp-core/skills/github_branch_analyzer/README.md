# GitHub 分支分析器 (github_branch_analyzer)

分析仓库分支结构，理解分支工作流原理。

## 分支原理

### Git 分支本质
- 分支 = 指向 commit SHA 的可变指针
- `HEAD` = 当前分支的指针
- 合并 = 将两个 commit 历史合并

### 分支类型识别

| 类型 | 命名模式 | 生命周期 | 合并方向 |
|------|---------|---------|---------|
| main | main, master | 永久 | 接受所有合并 |
| dev | dev, develop | 永久 | main ← dev ← feature |
| release | release/v1.2 | 临时 | main + dev |
| hotfix | hotfix/bug-123 | 临时 | main |
| feature | feature/login | 临时 | dev |
| fix | fix/memory-leak | 临时 | dev/main |

### 工作流类型

**GitFlow** — 大型项目
```
main ────────────●────────────────●─────
                  ↖ hotfix       ↑ merge
dev ────●──●──●──●────────────────●───
         ↑ feature   ↑ release   ↑
feature ─●         release/v1 ──●
```

**GitHub Flow** — 敏捷团队
```
main ────●──●──●──●──●──●──●──●──●
          ↑ feature合并
feature ─●──●──●
```

**Trunk-Based** — 持续集成
```
main ────●──●──●──●──●──●──●──●──●
         ↑short-lived feature
feature ─●
```

## 命令

```bash
# 完整分析（分支结构 + 工作流 + 默认分支提交）
python skill.py analyze <repo_url>

# 只看分支列表
python skill.py branches <repo_url>

# 比较两个分支差异
python skill.py compare <repo_url> <branch1> <branch2>

# 生成分支树
python skill.py tree <repo_url>
```

## 输出示例

```
仓库: user/repo (默认分支: main)
==================================================

★ 主分支:
  🔒 main → a1b2c3d

◆ 开发分支:
  🔒 dev → f4e5d6

◇ feature (3个):
    feature/user-auth → g7h8i9
    feature/payment → j1k2l3
  ... 还有 1 个分支
```
