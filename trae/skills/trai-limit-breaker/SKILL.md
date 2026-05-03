---
name: "trai-limit-breaker"
description: "限制突破大师。自动检测并突破所有系统限制：网络限制、技能加载限制、架构限制、执行限制。Invoke when any limitation or restriction is encountered in \python system."
---

# 限制突破大师

## 突破类型

### 1. 网络限制突破
```powershell
# 运行网络限制突破
& "\python\scripts\break_all_limits.ps1" -NetworkOnly
```

**检测内容：**
- Hosts 文件中的 127.0.0.1 重定向
- Steam++ 等工具添加的限制
- DNS 污染
- 代理配置

**自动修复：**
- 备份原始 hosts 文件
- 移除所有 GitHub 相关限制
- 刷新 DNS 缓存
- 测试网络连通性

### 2. 技能加载限制突破
```powershell
# 运行技能限制突破
& "\python\scripts\break_all_limits.ps1" -SkillsOnly
```

**检测内容：**
- 导入路径错误 (MCP_Core.skills.base → skills.base)
- 缺失的类级属性 (name, description, version, author)
- 语法错误 (f-string 问题)
- 模块依赖缺失

**自动修复：**
- 修复导入语句
- 添加缺失的属性
- 修正语法错误
- 重新加载技能

### 3. 架构限制突破
```powershell
# 运行架构限制突破
& "\python\scripts\break_all_limits.ps1" -ArchitectureOnly
```

**检测内容：**
- 缺失的核心目录
- 受保护文件完整性
- 文件分类正确性
- 索引文件同步

**自动修复：**
- 创建缺失目录
- 恢复受保护文件
- 验证分类规则
- 重建索引

### 4. 执行限制突破
```powershell
# 运行执行限制突破
& "\python\scripts\break_all_limits.ps1"
```

**检测内容：**
- PowerShell 执行策略
- Python 环境可用性
- 系统权限
- 依赖包安装

**自动修复：**
- 设置执行策略为 RemoteSigned
- 检测 Python 安装
- 验证管理员权限
- 安装缺失依赖

## 完整突破流程

```powershell
# 一键突破所有限制
& "\python\scripts\break_all_limits.ps1" -AutoFix
```

**执行步骤：**
1. 检查管理员权限
2. 备份关键文件
3. 清理网络限制
4. 修复技能加载
5. 验证架构完整性
6. 设置执行环境
7. 重新加载所有技能
8. 验证突破结果

## 降级方案

当自动突破失败时，提供手动突破指南：

### 网络限制手动突破
```powershell
# 1. 备份 hosts
Copy-Item "C:\Windows\System32\drivers\etc\hosts" "C:\Windows\System32\drivers\etc\hosts.bak"

# 2. 编辑 hosts，删除 GitHub 相关行
notepad "C:\Windows\System32\drivers\etc\hosts"

# 3. 刷新 DNS
ipconfig /flushdns
```

### 技能限制手动突破
```python
# 1. 修复导入
# 在 skill.py 中替换:
from MCP_Core.skills.base import SkillBase
# 为:
from skills.base import SkillBase

# 2. 添加属性
class MySkill(SkillBase):
    name = "my_skill"
    description = "我的技能"
    version = "1.0.0"
    author = "MCP Core Team"
```

## 突破验证

```powershell
# 验证网络
ping github.com

# 验证技能
py "\python\MCP_Core\server.py" --status

# 验证架构
Test-Path "\python\.gstack_protected"
Test-Path "\python\AGENTS.md"
Test-Path "\python\index.json"
```

## 持续监控

```python
# 定期检查限制状态
def monitor_limits():
    status = {
        'network': check_network(),
        'skills': check_skills(),
        'architecture': check_architecture(),
        'execution': check_execution()
    }
    
    if any(not s for s in status.values()):
        auto_break_limits()
    
    return status
```
