# Web 漏洞检测模式

## 1. SQL 注入 (SQL Injection)

### 检测模式
- Python: `cursor.execute(f"SELECT * FROM users WHERE id={user_input}")`
- Python: `cursor.execute("SELECT * FROM users WHERE id=" + user_input)`
- Java: `stmt.executeQuery("SELECT * FROM users WHERE id=" + request.getParameter("id"))`
- PHP: `mysql_query("SELECT * FROM users WHERE id=" . $_GET['id'])`
- C#: `new SqlCommand("SELECT * FROM users WHERE id=" + Request["id"])`

### 检测策略
1. 找到所有数据库查询点
2. 检查是否使用参数化查询 (PreparedStatement, ? placeholder)
3. 检查是否有字符串拼接或 f-string 构造 SQL
4. 对每个注入点, 尝试注入 `' OR '1'='1` 验证

### 修复建议
- Python: `cursor.execute("SELECT * FROM users WHERE id=?", (user_input,))`
- Java: `PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id=?")`

## 2. 跨站脚本 (XSS)

### 检测模式
- `innerHTML = user_input`
- `document.write(user_input)`
- `eval(user_input)`
- `<%= user_input %>` (JSP 未转义)
- `{{ user_input|safe }}` (Django 未转义)
- `dangerouslySetInnerHTML` (React)

### 检测策略
1. 搜索所有将用户输入插入 DOM 的位置
2. 检查是否使用了 HTML 编码/转义
3. 检查 CSP (Content-Security-Policy) 头

## 3. 命令注入 (Command Injection)

### 检测模式
- `os.system(user_input)`
- `os.popen(user_input)`
- `subprocess.call(user_input, shell=True)`
- `Runtime.getRuntime().exec(user_input)` (Java)
- `exec(user_input)` (PHP)
- `Process.Start(user_input)` (C#)

### 检测策略
1. 搜索所有系统命令执行点
2. 检查命令参数是否来自用户输入
3. 尝试注入 `; ls` 或 `| whoami` 验证

### 修复建议
- 使用 `subprocess.run([cmd, arg1, arg2])` 而非 `shell=True`
- 使用白名单限制可执行命令

## 4. 路径遍历 (Path Traversal)

### 检测模式
- `open(user_input)`
- `os.path.join(base, user_input)` — 无法防止 `../../../`
- `File(user_input)` (Java)

### 检测策略
1. 找到所有文件读写操作
2. 检查路径是否来自用户输入
3. 尝试 `../../../etc/passwd` 验证

### 修复建议
- 使用 `os.path.basename()` 剥离目录
- 使用 `os.path.realpath()` 验证路径在允许范围内

## 5. SSRF (服务端请求伪造)

### 检测模式
- `requests.get(user_input)`
- `urllib.request.urlopen(user_input)`
- `HttpClient.GetAsync(user_input)` (C#)

### 检测策略
1. 找到所有服务端发起 HTTP 请求的位置
2. 检查 URL 是否来自用户输入
3. 尝试访问 `http://169.254.169.254/` (AWS metadata) 或 `http://127.0.0.1/` 验证

## 6. 反序列化漏洞

### 检测模式
- `pickle.loads(user_input)` (Python)
- `ObjectInputStream.readObject()` (Java)
- `BinaryFormatter.Deserialize()` (C#)
- `unserialize(user_input)` (PHP)

### 检测策略
1. 找到所有反序列化点
2. 检查数据源是否可控
3. 检查是否使用了安全的序列化方案 (JSON)

## 风险等级标记
- P0 [!!]: 可确认利用, 无认证要求
- P1 [!]: 需特定条件但可稳定利用
- P2 [-]: 不良实践, 当前不可利用但应修复
