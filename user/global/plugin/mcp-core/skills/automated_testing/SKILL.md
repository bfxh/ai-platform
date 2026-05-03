# 自动化测试技能

## 功能介绍

自动化测试技能是一个专门用于自动运行测试并生成测试报告的工具，支持多种测试框架，能够帮助开发者快速发现和解决代码中的问题。

## 核心功能

- **多框架支持**：支持 pytest、unittest 和 nose 测试框架
- **自动发现**：自动查找项目中的测试文件
- **批量测试**：一次运行多个测试文件
- **报告生成**：生成详细的测试报告，包括 JSON 和 HTML 格式
- **结果分析**：分析测试结果，统计通过和失败的测试数量
- **配置管理**：支持自定义测试配置

## 安装方法

1. 确保 MCP Core 已安装并运行
2. 将技能目录复制到 `MCP_Core/skills/` 目录下
3. 重启 MCP Core 服务

## 使用方法

### 命令行使用

```bash
# 运行指定路径的测试
python -m MCP_Core.cli skill automated_testing run --test_path tests --framework pytest

# 运行所有测试
python -m MCP_Core.cli skill automated_testing run-all

# 生成测试报告
python -m MCP_Core.cli skill automated_testing generate-report --report_file test_reports/test_summary_20260409_120000.json

# 列出测试文件
python -m MCP_Core.cli skill automated_testing list-tests --test_path tests
```

### 编程接口

```python
from MCP_Core.skills.automated_testing import AutomatedTestingSkill

# 初始化技能
skill = AutomatedTestingSkill()

# 运行测试
result = skill.execute("run", test_path="tests", framework="pytest")
print(result)

# 运行所有测试
result = skill.execute("run-all")
print(result)

# 生成测试报告
result = skill.execute("generate-report", report_file="test_reports/test_summary.json")
print(result)

# 列出测试文件
result = skill.execute("list-tests", test_path="tests")
print(result)
```

## 配置说明

### 配置文件

技能会在首次运行时生成 `test_config.json` 配置文件，包含以下内容：

- **test_reports_dir**：测试报告保存目录
- **test_frameworks**：测试框架列表
- **test_paths**：测试文件搜索路径
- **test_patterns**：测试文件匹配模式

### 默认配置

```json
{
  "test_config": "test_config.json",
  "test_reports_dir": "test_reports",
  "test_frameworks": ["pytest", "unittest", "nose"],
  "test_paths": ["tests", "test"],
  "test_patterns": ["test_*.py", "*_test.py"]
}
```

## 测试报告

### JSON 报告

测试完成后，会生成 JSON 格式的测试报告，包含以下信息：

- **timestamp**：测试时间
- **total_tests**：总测试数
- **frameworks**：各测试框架的测试结果
- **results**：详细的测试结果

### HTML 报告

使用 `generate-report` 命令可以生成 HTML 格式的测试报告，包含以下信息：

- **测试摘要**：测试时间、总测试数、各框架测试结果
- **详细结果**：每个测试文件的测试结果，包括输出和错误信息

## 支持的测试框架

1. **pytest**：功能强大的测试框架，支持参数化测试、 fixtures 等高级特性
2. **unittest**：Python 标准库中的测试框架
3. **nose**：unittest 的扩展，提供更多功能

## 注意事项

1. **依赖安装**：使用 pytest 和 nose 框架需要先安装相应的包
   ```bash
   pip install pytest pytest-json-report nose nose-json
   ```

2. **测试文件命名**：测试文件应按照 `test_*.py` 或 `*_test.py` 的命名模式

3. **测试方法命名**：测试方法应以 `test_` 开头

4. **报告目录**：测试报告默认保存在 `test_reports` 目录中

5. **权限要求**：需要对测试目录和报告目录有读写权限

## 示例场景

### 场景 1：项目构建前测试

在项目构建前，运行所有测试确保代码质量：

```bash
python -m MCP_Core.cli skill automated_testing run-all
```

### 场景 2：特定模块测试

只测试特定模块的代码：

```bash
python -m MCP_Core.cli skill automated_testing run --test_path tests/test_module.py --framework pytest
```

### 场景 3：生成测试报告

测试完成后，生成 HTML 格式的测试报告：

```bash
python -m MCP_Core.cli skill automated_testing generate-report --report_file test_reports/test_summary.json
```

## 故障排除

### 测试框架未安装
- 错误信息：`ModuleNotFoundError: No module named 'pytest'`
- 解决方法：安装相应的测试框架

### 测试文件未找到
- 错误信息：`没有找到测试文件`
- 解决方法：检查测试文件路径和命名模式

### 测试失败
- 错误信息：测试结果显示失败
- 解决方法：查看测试输出和错误信息，修复代码中的问题

## 扩展建议

1. **集成 CI/CD**：将自动化测试集成到 CI/CD 流程中
2. **自定义报告**：根据项目需求自定义测试报告格式
3. **测试覆盖**：集成测试覆盖率工具，如 coverage.py
4. **并行测试**：支持并行运行测试，提高测试速度
5. **测试数据管理**：添加测试数据管理功能

## 版本历史

- **v1.0.0**：初始版本，支持基本的测试运行和报告生成

## 贡献指南

欢迎提交 Issue 和 Pull Request，帮助改进这个技能。

## 许可证

MIT License