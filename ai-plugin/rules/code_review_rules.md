# 代码审查规则库

## 通用规则（所有语言）

1. 禁止使用 eval() 或类似的动态代码执行函数
2. 敏感信息（密码、密钥、API密钥）禁止硬编码，必须使用环境变量或配置文件
3. 禁止在循环内进行昂贵的操作（如数据库查询、网络请求）
4. 必须处理异常情况，避免程序崩溃
5. 禁止无限循环

---

## Python 规则

1. **金额类型**：任何涉及"金额"、"余额"、"价格"、"工资"的变量和函数返回值，必须使用 `Decimal` 类型，禁止使用 `float/double`
2. **SQL安全**：禁止任何形式的 SQL 字符串拼接，必须使用参数化查询
3. **命名规范**：函数参数和变量使用 snake_case，类名使用 PascalCase，常量使用 UPPER_SNAKE_CASE
4. **API响应**：JSON 字段名使用 camelCase
5. **命令执行**：调用外部命令必须检查返回码
6. **导入规范**：导入语句必须按标准库、第三方库、本地模块的顺序排列

---

## JavaScript/TypeScript 规则

1. **金额类型**：使用 `BigNumber` 库处理金额，禁止使用 `number` 类型
2. **SQL安全**：禁止字符串拼接 SQL，使用 ORM 或参数化查询
3. **命名规范**：变量和函数使用 camelCase，类和接口使用 PascalCase，常量使用 UPPER_CASE
4. **空值检查**：必须对可能为 null/undefined 的值进行检查
5. **类型安全**：TypeScript 代码必须严格类型化，禁止使用 `any` 类型
6. **Promise处理**：异步操作必须正确处理 reject 情况

---

## Go 规则

1. **金额类型**：使用 `decimal.Decimal` 或 `big.Float` 处理金额
2. **SQL安全**：使用 `database/sql` 的参数化查询，禁止字符串拼接
3. **命名规范**：函数名和变量名使用 CamelCase，导出标识符首字母大写
4. **错误处理**：必须检查并正确处理所有错误返回值
5. **指针使用**：避免不必要的指针，合理使用值类型
6. **并发安全**：共享数据结构必须使用互斥锁保护

---

## Java 规则

1. **金额类型**：使用 `java.math.BigDecimal` 处理金额
2. **SQL安全**：使用 `PreparedStatement` 进行参数化查询
3. **命名规范**：类名使用 PascalCase，方法和变量使用 camelCase，常量使用 UPPER_SNAKE_CASE
4. **异常处理**：区分 checked 和 unchecked 异常，合理捕获和处理
5. **资源管理**：使用 try-with-resources 自动关闭资源
6. **空值检查**：使用 Optional 或显式空值检查避免 NullPointerException