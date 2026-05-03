# CI/CD 配置指南

## 概述

本项目使用 GitHub Actions 实现持续集成和持续部署（CI/CD）流程。CI/CD 流程主要包括以下几个方面：

- **代码质量检查**：使用 Black、isort、Flake8 等工具检查代码风格
- **类型检查**：使用 mypy 进行静态类型检查
- **单元测试**：使用 pytest 运行单元测试并生成覆盖率报告
- **安全检查**：使用 safety 和 bandit 检查依赖和代码的安全问题
- **文档生成**：使用 pdoc 生成 API 文档
- **预提交钩子**：使用 pre-commit 确保提交的代码符合质量要求

## GitHub Actions 配置

### 工作流程文件

工作流程配置文件位于 `.github/workflows/ci.yml`，包含三个主要任务：

1. **test**：运行单元测试和代码质量检查
2. **build**：生成 API 文档
3. **security**：进行安全检查

### 测试矩阵

测试在多个 Python 版本上运行，确保代码的兼容性：
- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12

### 代码质量检查

- **Black**：代码格式化检查
- **isort**：导入排序检查
- **mypy**：静态类型检查
- **pytest**：运行单元测试并生成覆盖率报告

### 安全检查

- **safety**：检查依赖中的安全漏洞
- **bandit**：检查代码中的安全问题

## 预提交钩子

### 安装

```bash
# 安装 pre-commit
pip install pre-commit

# 安装钩子
pre-commit install
```

### 运行

```bash
# 运行所有钩子
pre-commit run --all-files

# 运行特定钩子
pre-commit run black
```

### 钩子配置

预提交钩子配置文件位于 `.pre-commit-config.yaml`，包含以下钩子：

- **black**：代码格式化
- **isort**：导入排序
- **flake8**：代码风格检查
- **mypy**：类型检查
- **bandit**：安全检查
- **docformatter**：文档字符串格式化
- **radon**：代码复杂度检查
- **pre-commit-hooks**：各种通用检查（大文件、冲突、私钥等）

## 本地开发流程

### 1. 安装依赖

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 或者安装所有依赖
pip install -e .[dev]
```

### 2. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_skills/test_github_opensource.py

# 运行测试并生成覆盖率报告
pytest --cov=skills --cov-report=html
```

### 3. 代码质量检查

```bash
# 运行 Black 格式化
black skills/ tests/

# 运行 isort 排序导入
isort skills/ tests/

# 运行 Flake8 检查
flake8 skills/

# 运行 mypy 类型检查
mypy skills/
```

### 4. 安全检查

```bash
# 检查依赖漏洞
safety check --file requirements.txt

# 检查代码安全问题
bandit -r skills/ -ll
```

## 依赖管理

### 核心依赖

- **pytest**：测试框架
- **pytest-cov**：测试覆盖率
- **black**：代码格式化
- **isort**：导入排序
- **mypy**：类型检查
- **pdoc**：文档生成
- **safety**：依赖安全检查
- **bandit**：代码安全检查

### 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

## 环境变量

CI/CD 流程使用以下环境变量：

| 环境变量 | 描述 | 必需 |
|---------|------|------|
| `CODECOV_TOKEN` | Codecov 覆盖率报告上传令牌 | 否 |
| `GITHUB_TOKEN` | GitHub API 访问令牌 | 否 |

## 问题排查

### 常见问题

1. **测试失败**：检查测试代码和被测试代码，确保测试逻辑正确
2. **代码质量检查失败**：运行 `black` 和 `isort` 自动修复代码格式
3. **类型检查失败**：添加类型注解或修改类型定义
4. **安全检查失败**：修复安全漏洞或添加安全注释
5. **依赖安装失败**：检查网络连接和依赖版本

### 排查步骤

1. **查看 CI 日志**：在 GitHub Actions 页面查看详细的构建日志
2. **本地重现**：在本地运行相同的命令，查看具体错误
3. **检查依赖**：确保所有依赖都已正确安装
4. **更新依赖**：尝试更新到最新版本的依赖
5. **提交修复**：修复问题后提交代码，触发新的 CI 构建

## 最佳实践

1. **提交前检查**：在提交代码前运行 `pre-commit run --all-files`
2. **分支管理**：使用 feature 分支开发新功能，使用 main 分支发布
3. **测试覆盖**：为新功能添加单元测试，确保测试覆盖率
4. **代码风格**：遵循项目的代码风格指南，使用 Black 和 isort 自动格式化
5. **安全意识**：定期运行安全检查，修复发现的安全问题
6. **文档更新**：更新代码时同步更新文档

## 示例工作流程

### 开发新功能

1. 创建 feature 分支：`git checkout -b feature/my-feature`
2. 开发新功能
3. 运行测试：`pytest`
4. 运行代码质量检查：`pre-commit run --all-files`
5. 提交代码：`git commit -m "Add my feature"`
6. 推送分支：`git push origin feature/my-feature`
7. 创建 Pull Request
8. 等待 CI 构建完成
9. 合并到 main 分支

### 修复 bug

1. 创建 fix 分支：`git checkout -b fix/my-bug`
2. 修复 bug
3. 运行测试：`pytest`
4. 运行代码质量检查：`pre-commit run --all-files`
5. 提交代码：`git commit -m "Fix my bug"`
6. 推送分支：`git push origin fix/my-bug`
7. 创建 Pull Request
8. 等待 CI 构建完成
9. 合并到 main 分支

## 总结

本项目的 CI/CD 流程旨在确保代码质量、安全性和可靠性。通过自动化的测试、代码质量检查和安全检查，可以早期发现和解决问题，提高代码质量和开发效率。

遵循本指南的最佳实践，可以确保项目的持续集成流程顺利运行，为项目的长期发展奠定良好的基础。
