---
name: coding-style
description: 代码编写规范 — 格式化、命名、注释、Git 提交
priority: high
version: "1.0"
---

# 代码编写规范 Coding Style

## Python 代码格式

| 工具 | 配置 |
|------|------|
| **Black** | `--line-length=120` |
| **isort** | `--profile=black` |
| **flake8** | max-line-length=120 |

执行命令:
```bash
black --line-length=120 .
isort --profile=black .
```

## 命名约定

- **变量/函数**: `snake_case` (如 `get_user_data`)
- **类**: `PascalCase` (如 `BugMemoryEngine`)
- **常量**: `UPPER_SNAKE_CASE` (如 `MAX_RETRY_COUNT`)
- **私有成员**: 前缀 `_` (如 `_internal_method`)
- **模块**: `snake_case` (如 `bug_memory.py`)
- **包**: 简短小写单词 (如 `memory/`, `core/`)

## 文档注释

- **docstring 语言**: 中文
- **docstring 风格**: Google 风格
- **必须包含**: 函数用途、参数说明、返回值说明
- **复杂逻辑**: 行内注释说明为什么这样做（而非做了什么）

```python
def record_bug(self, error_message: str, task_description: str = "") -> str:
    """记录一个 Bug 到记忆引擎。

    Args:
        error_message: 错误信息文本
        task_description: 触发该 bug 的任务描述

    Returns:
        bug_id: 新记录的 bug ID 字符串
    """
```

## 错误处理

- **禁止** 裸 `except:` 或 `except: pass`
- 明确捕获预期的异常类型
- 不处理"不可能发生"的错误场景
- 只在系统边界（用户输入、外部 API）做校验

## Git 提交

- 格式: [Conventional Commits](https://www.conventionalcommits.org/)
- 示例:
  ```
  feat: 添加 BugMemoryEngine 自动学习系统
  fix: 修复 hook_post_task 签名不匹配问题
  refactor: 抽取 `_classify_error()` 辅助方法
  ```
- 提交信息结尾添加: `🤖 Generated with [Qoder][https://qoder.com]`（仅 Qoder 生成时）

## 安全编码

- 禁止在代码或日志中硬编码凭证、API Key
- 用户输入必须做参数化处理（防注入）
- 文件路径使用绝对路径，避免相对路径混淆
- 不创建或改进可能被恶意使用的代码
