# 代码规范

## Python
- Black: `--line-length=120`
- isort: `--profile=black`
- 命名: snake_case (变量/函数), PascalCase (类), UPPER_SNAKE_CASE (常量)
- docstring: 中文, Google 风格
- 禁止裸 `except:` 或 `except: pass`

## Git
- Conventional Commits: `feat:`, `fix:`, `refactor:`
- 禁止 `git push --force` 到 main/master

## 安全
- 禁止硬编码凭证、API Key
- 用户输入必须参数化
- 文件路径用绝对路径
- 不在日志中打印敏感信息

### SQL 强制规则
- 禁止字符串拼接构造 SQL（+、f-string、format() 均禁止）
- 必须使用参数化查询（? 占位符 + 参数元组）
- 示例正确写法:
  ```python
  cursor.execute("SELECT * FROM orders WHERE id=?", (user_id,))
  ```
- 动态表名/列名必须用白名单校验，不允许直接拼接
- 金额/小数必须使用 Decimal，禁止 float

## 输出
- 语言: 中文
- 风格: 简洁直接
- 禁止: emoji（除非用户明确要求）、过度赞美、猜测 URL/路径
