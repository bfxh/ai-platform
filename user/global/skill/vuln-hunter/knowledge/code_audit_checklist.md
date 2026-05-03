# 代码审计检查清单

## Python 审计要点

### 1. 注入类
- [ ] SQL: 是否使用 f-string / % / + 拼接 SQL 语句
- [ ] 命令: 是否使用 `os.system()` / `subprocess(shell=True)` 且参数可控
- [ ] 模板: `render_template_string()` 用户输入
- [ ] 反序列化: `pickle.loads()` / `yaml.load()` 不安全加载

### 2. 认证授权
- [ ] 硬编码密码/Token/Key: `password = "xxx"` / `API_KEY = "sk-..."`
- [ ] 缺失权限检查: 路由无 `@login_required` 装饰器
- [ ] JWT: 是否验证签名、exp、aud
- [ ] Session: `secret_key` 是否弱密码

### 3. 文件操作
- [ ] 路径遍历: `open(user_path)` 无路径净化
- [ ] 文件上传: 未检查文件类型/大小
- [ ] 任意文件读取: `send_file(user_path)`

### 4. 信息泄露
- [ ] DEBUG=True 在生产环境
- [ ] 异常堆栈直接返回给客户端
- [ ] 日志包含敏感数据 (密码/Token)
- [ ] `.env` / `.git` 可访问

### 5. 依赖安全
- [ ] `requirements.txt` 中是否有已知 CVE 的包
- [ ] 是否使用已弃用的版本

---

## Java 审计要点

### 1. Web 层 (Spring/Struts)
- [ ] Controller 参数是否校验 @Valid
- [ ] MyBatis `${}` 拼接 SQL (应用 #{} )
- [ ] `@ResponseBody` 返回值是否包含敏感字段
- [ ] Spring Security 配置是否遗漏路径

### 2. 反序列化
- [ ] `ObjectInputStream.readObject()` 输入可控
- [ ] Fastjson `JSON.parse(text)` 未关闭 autoType
- [ ] XStream `fromXML()` 无安全框架

### 3. 表达式注入
- [ ] SpEL: `@Value("#{userInput}")` 或 `ExpressionParser`
- [ ] OGNL: Struts2 参数绑定
- [ ] EL: `${userInput}` 在 JSP 中

### 4. 权限
- [ ] Shiro RememberMe 密钥硬编码
- [ ] 垂直越权: 普通用户直接访问管理接口
- [ ] 水平越权: 修改 user_id 参数访问他人数据

---

## JavaScript/Node.js 审计要点

### 1. 注入
- [ ] SQL: 字符串拼接而非参数化
- [ ] NoSQL: `collection.find({ $where: userInput })`
- [ ] 命令: `child_process.exec(userInput)`
- [ ] 模板: EJS/Pug 未转义用户输入

### 2. 原型链污染
- [ ] `Object.assign()` / `_.merge()` / `_.defaultsDeep()` 合并用户数据
- [ ] `JSON.parse()` 后直接使用 `__proto__` 属性

### 3. 依赖
- [ ] `node_modules` 中是否有已知漏洞包
- [ ] `package.json` 版本范围是否过宽

---

## PHP 审计要点

### 1. 注入
- [ ] SQL: `mysql_query("SELECT ... ".$_GET['id'])`
- [ ] 命令: `exec()`/`system()`/`shell_exec()`/`passthru()` + 用户输入
- [ ] 文件包含: `include($_GET['page'])` (LFI/RFI)
- [ ] 反序列化: `unserialize($_GET['data'])`

### 2. 会话
- [ ] `session fixation`: 登录后不重新生成 session_id
- [ ] `session.auto_start=On` + 用户可控 session_id

---

## C# / .NET 审计要点

### 1. 注入
- [ ] SQL: 字符串拼接而非 `SqlParameter`
- [ ] LINQ: `Dynamic Linq` 用户构造表达式
- [ ] 命令: `Process.Start(userInput)`
- [ ] XPath: `XPathExpression.Compile(userInput)`

### 2. 反序列化
- [ ] `BinaryFormatter.Deserialize()` / `NetDataContractSerializer`
- [ ] `JavaScriptSerializer` 与 `SimpleTypeResolver`
- [ ] ViewState 未加密/MAC

### 3. 认证
- [ ] FormsAuthentication 弱密钥
- [ ] JWT `None` 算法绕过

---

## Go 审计要点

### 1. 注入
- [ ] SQL: `fmt.Sprintf()` 拼接 SQL
- [ ] 模板: `template.HTML(userInput)` (XSS)
- [ ] 命令: `exec.Command("sh", "-c", userInput)`

### 2. 并发
- [ ] 竞态条件: 无锁共享变量
- [ ] goroutine 泄漏: 无 context 取消

### 3. 密码学
- [ ] `math/rand` 而非 `crypto/rand`
- [ ] 弱 hash: MD5/SHA1 用于密码

---

## 通用高风险模式 (跨语言)

### P0 — 立即修复
- [ ] 硬编码凭证 (密码/Token/Key/证书)
- [ ] 无认证的敏感操作
- [ ] 命令注入且参数可控
- [ ] SQL 注入且无 WAF
- [ ] 任意文件读取/写入

### P1 — 尽快修复
- [ ] 反序列化输入可控
- [ ] 权限绕过漏洞
- [ ] 敏感信息泄露
- [ ] XSS 存储型

### P2 — 计划修复
- [ ] 弱密码算法
- [ ] DEBUG 模式
- [ ] 不安全的默认配置
- [ ] 依赖版本过旧
