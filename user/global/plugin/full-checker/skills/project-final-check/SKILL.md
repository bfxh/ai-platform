---
name: "project-final-check"
description: "项目最终全面检查skill，集成代码质量、测试覆盖、文档完整性、安全检查、依赖管理五大检查项。项目结束前必须执行。"
---

# Project Final Check Skill

## 概述

项目最终全面检查工具，在项目结束前执行全面的质量检查，确保项目符合发布标准。

## 检查项目

### 1. 代码质量检查 (code_quality)

- 检查是否存在超大文件（>10000行无函数）
- 检查代码结构合理性
- 检查命名规范
- 检查注释完整性

### 2. 测试覆盖检查 (testing)

- 检查是否存在测试文件
- 统计测试文件数量
- 检查测试命名规范
- 验证测试可运行性

### 3. 文档完整性检查 (documentation)

- 检查 README.md 是否存在
- 检查 docs/ 目录
- 检查 CHANGELOG
- 检查许可证文件

### 4. 安全检查 (security)

- 检查敏感文件(.env)是否被gitignore保护
- 检查是否存在硬编码密码/密钥
- 检查依赖安全漏洞

### 5. 依赖管理检查 (dependencies)

- 检查是否存在锁文件(package-lock.json, requirements.lock)
- 检查依赖版本是否过时
- 检查是否有未使用的依赖

## 使用方法

### 通过Full Checker Plugin调用

```python
from full_checker import get_checker

checker = get_checker()
result = checker.run_check(
    project_path="D:\\project\\my-app",
    project_name="my-app",
    check_types=["code_quality", "testing", "documentation", "security", "dependencies"]
)
```

### 指定项目类型

```python
# 自动检测项目类型
project_type = checker.get_project_type("D:\\project\\my-app")
# 返回: nodejs, python, rust, java, go, generic

# 根据项目类型进行定制检查
result = checker.run_check(
    project_path="D:\\project\\my-app",
    check_types=["testing"]  # 对NodeJS项目特别检查package.json中的test脚本
)
```

### 项目级配置

```python
# 为特定项目设置自定义检查配置
checker.set_project_config("my-app", {
    "required_checks": ["code_quality", "testing", "documentation"],
    "skip_checks": ["security"],
    "thresholds": {
        "min_test_files": 5,
        "min_coverage": 80
    }
})

# 获取项目配置
config = checker.get_project_config("my-app")
```

## 返回结果格式

```json
{
  "success": true,
  "project_path": "D:\\project\\my-app",
  "project_name": "my-app",
  "project_type": "nodejs",
  "checks": {
    "code_quality": {
      "status": "passed",
      "message": "Code quality check completed. Found 0 issues.",
      "issues": []
    },
    "testing": {
      "status": "passed",
      "message": "Testing check completed. Found 10 test files.",
      "test_files": ["test/test_api.py", "..."]
    },
    "documentation": {
      "status": "warning",
      "message": "Documentation check completed. Found 1 documentation items.",
      "docs": ["README.md"]
    },
    "security": {
      "status": "passed",
      "message": "Security check completed. Found 0 potential issues.",
      "issues": []
    },
    "dependencies": {
      "status": "warning",
      "message": "Dependency check completed. Missing lock file: True",
      "outdated": []
    }
  },
  "summary": {
    "total": 5,
    "passed": 3,
    "failed": 0,
    "warnings": 2
  }
}
```

## 状态说明

- **passed**：检查通过
- **failed**：检查失败（严重问题）
- **warning**：警告（建议改进）
- **skipped**：跳过（未执行）

## 适用场景

- 项目结束前的最终验证
- 发布前的质量检查
- CI/CD流程中的最终检查点
- 团队代码审查的前置检查

## 注意事项

1. 本skill会自动保存检查历史到 `config.json`
2. 建议为每个项目配置特定的检查阈值
3. 对于大型项目，可以选择性跳过部分耗时的检查

## 集成说明

本skill是 `full-checker` plugin的核心组成部分，会在以下情况被自动调用：
- 项目即将结束时
- CI/CD流程的最后阶段
- 手动触发总检查时