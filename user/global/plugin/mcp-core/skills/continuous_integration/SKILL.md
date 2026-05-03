# 持续集成技能

## 功能介绍

持续集成技能是一个专门用于自动化构建、测试和部署流程的工具，能够帮助开发者快速集成代码变更，确保代码质量和稳定性。

## 核心功能

- **自动化构建**：自动执行构建过程，生成可部署的产物
- **自动化测试**：运行测试套件，确保代码质量
- **自动化部署**：将构建产物部署到目标环境
- **多环境支持**：支持不同的构建和测试环境
- **CI配置生成**：生成常见CI平台的配置文件
- **报告生成**：生成详细的CI流程报告

## 安装方法

1. 确保 MCP Core 已安装并运行
2. 将技能目录复制到 `MCP_Core/skills/` 目录下
3. 重启 MCP Core 服务

## 使用方法

### 命令行使用

```bash
# 运行完整的CI流程
python -m MCP_Core.cli skill continuous_integration run

# 只运行构建步骤
python -m MCP_Core.cli skill continuous_integration build

# 只运行测试步骤
python -m MCP_Core.cli skill continuous_integration test

# 只运行部署步骤
python -m MCP_Core.cli skill continuous_integration deploy

# 生成CI配置文件
python -m MCP_Core.cli skill continuous_integration generate-config --template github-actions
```

### 编程接口

```python
from MCP_Core.skills.continuous_integration import ContinuousIntegrationSkill

# 初始化技能
skill = ContinuousIntegrationSkill()

# 运行完整的CI流程
result = skill.execute("run")
print(result)

# 只运行构建步骤
result = skill.execute("build")
print(result)

# 只运行测试步骤
result = skill.execute("test")
print(result)

# 只运行部署步骤
result = skill.execute("deploy")
print(result)

# 生成CI配置文件
result = skill.execute("generate-config", template="github-actions")
print(result)
```

## 配置说明

### 配置文件

技能会在首次运行时生成 `ci_config.json` 配置文件，包含以下内容：

- **build_dir**：构建产物保存目录
- **artifacts_dir**：CI产物保存目录
- **steps**：CI流程步骤
- **commands**：各步骤的执行命令
- **environments**：构建环境配置

### 默认配置

```json
{
  "ci_config": "ci_config.json",
  "build_dir": "build",
  "artifacts_dir": "artifacts",
  "steps": [
    "install",
    "build",
    "test",
    "deploy"
  ],
  "commands": {
    "install": ["pip", "install", "-r", "requirements.txt"],
    "build": ["python", "-m", "build"],
    "test": ["python", "-m", "pytest"],
    "deploy": ["twine", "upload", "dist/*"]
  },
  "environments": {
    "default": {
      "python_version": "3.10",
      "requirements": "requirements.txt"
    }
  }
}
```

## CI流程步骤

### 1. 安装依赖 (install)

执行 `pip install -r requirements.txt` 命令，安装项目依赖。

### 2. 构建项目 (build)

执行 `python -m build` 命令，构建项目并生成分发包。

### 3. 测试项目 (test)

执行 `python -m pytest` 命令，运行测试套件。

### 4. 部署项目 (deploy)

执行 `twine upload dist/*` 命令，将构建产物上传到PyPI。

## 支持的CI配置模板

### GitHub Actions

生成 `.github/workflows/ci.yml` 配置文件，支持：
- 多Python版本测试
- 自动安装依赖
- 自动构建项目
- 自动运行测试
- 上传构建产物

## 注意事项

1. **依赖安装**：使用构建和部署功能需要先安装相应的包
   ```bash
   pip install build twine pytest
   ```

2. **配置文件**：确保项目根目录有 `requirements.txt` 文件

3. **权限要求**：部署到PyPI需要配置 `~/.pypirc` 文件

4. **目录结构**：确保项目有标准的Python包结构

5. **环境变量**：某些部署步骤可能需要设置环境变量

## 示例场景

### 场景 1：完整CI流程

运行完整的CI流程，包括安装依赖、构建、测试和部署：

```bash
python -m MCP_Core.cli skill continuous_integration run
```

### 场景 2：只运行构建和测试

只运行构建和测试步骤，不进行部署：

```bash
python -m MCP_Core.cli skill continuous_integration run --steps '["install", "build", "test"]'
```

### 场景 3：生成GitHub Actions配置

为项目生成GitHub Actions配置文件：

```bash
python -m MCP_Core.cli skill continuous_integration generate-config --template github-actions
```

## 故障排除

### 依赖安装失败
- 错误信息：`ERROR: Could not open requirements file`
- 解决方法：确保项目根目录有 `requirements.txt` 文件

### 构建失败
- 错误信息：`error: invalid command 'build'`
- 解决方法：安装 build 包 `pip install build`

### 测试失败
- 错误信息：测试结果显示失败
- 解决方法：查看测试输出和错误信息，修复代码中的问题

### 部署失败
- 错误信息：`Upload failed (403): Invalid or non-existent authentication information`
- 解决方法：配置 `~/.pypirc` 文件，添加正确的PyPI credentials

## 扩展建议

1. **多平台支持**：添加对其他CI平台的支持，如GitLab CI、Jenkins等
2. **环境管理**：集成虚拟环境管理，如venv或conda
3. **缓存优化**：添加依赖缓存，提高构建速度
4. **通知系统**：集成邮件、Slack等通知系统
5. **部署目标**：支持部署到更多目标环境，如Docker、云服务等

## 版本历史

- **v1.0.0**：初始版本，支持基本的CI流程和GitHub Actions配置生成

## 贡献指南

欢迎提交 Issue 和 Pull Request，帮助改进这个技能。

## 许可证

MIT License