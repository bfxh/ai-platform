# 反编译审计标准操作流程 (SOP)

## 流程概览

```
目标文件 → 识别类型 → 选择工具 → 反编译 → 代码分析 → 漏洞报告
```

---

## 场景 1: APK (Android 应用)

### 工具
- **jadx** (D:\rj\KF\FBY\jadx\bin\jadx-gui.bat)
- 备选: Ghidra (Dalvik 模块)

### 执行步骤
```bash
# 1. 反编译
D:\rj\KF\FBY\jadx\bin\jadx.bat -d output_dir target.apk

# 2. 关键文件检查
# - AndroidManifest.xml → 权限、组件、debuggable
# - resources/ → 硬编码密钥/URL
# - source/ → Java 源码审计
```

### APK 审计清单
- [ ] `android:debuggable="true"` — 允许调试
- [ ] `android:allowBackup="true"` — 允许备份
- [ ] 导出组件 (Service/Activity/BroadcastReceiver) 无权限保护
- [ ] WebView `setAllowUniversalAccessFromFileURLs(true)` — 跨域漏洞
- [ ] WebView `addJavascriptInterface` — JS 桥接洞
- [ ] 硬编码: API_KEY, AES_KEY, 签名密钥
- [ ] 使用 HTTP 明文传输
- [ ] SSL 证书固定缺失
- [ ] 文件提供者 (FileProvider) 路径遍历
- [ ] Intent 劫持: 隐式 Intent 未验证目标
- [ ] SQLite 数据库明文存储
- [ ] SharedPreferences 明文存储
- [ ] 日志泄漏: `Log.d(tag, password)`
- [ ] WebView `onReceivedSslError` 忽略 SSL 错误
- [ ] 不安全反序列化: `ObjectInputStream`

---

## 场景 2: .NET DLL/EXE

### 工具
- **dnSpy** (D:\rj\KF\FBY\dnSpy\dnSpy.exe)
- **ILSpy** (D:\rj\KF\FBY\ILSpy\ILSpy.exe)

### 执行步骤
```bash
# CLI 反编译
D:\rj\KF\FBY\dnSpy\dnSpy.Console.exe -o output_dir target.dll
```

### .NET 审计清单
- [ ] 硬编码连接字符串
- [ ] `BinaryFormatter.Deserialize()` 输入可控
- [ ] `Process.Start(userInput)`
- [ ] `SqlCommand` 字符串拼接
- [ ] ViewState MAC 验证关闭
- [ ] `validateRequest="false"` (WebForms)
- [ ] 加密密钥硬编码
- [ ] 弱随机数: `new Random()` 而非 `RNGCryptoServiceProvider`
- [ ] 路径遍历: `Path.Combine` 无法防止 `../`
- [ ] 反射加载: `Assembly.Load(userInput)`

---

## 场景 3: Java JAR

### 工具
- **JD-GUI** (D:\rj\KF\FBY\JD-GUI\jd-gui.jar)
- 备选: jadx (支持 class 文件)

### 执行步骤
```bash
java -jar D:\rj\KF\FBY\JD-GUI\jd-gui.jar target.jar
```

### Java JAR 审计清单
- [ ] 硬编码凭证 (数据库密码/API密钥)
- [ ] `ObjectInputStream.readObject()` — 反序列化
- [ ] Fastjson/XStream 配置不安全
- [ ] Shiro RememberMe 硬编码密钥
- [ ] Spring Boot Actuator 暴露
- [ ] MyBatis `${}` SQL 拼接
- [ ] JNDI 注入: `InitialContext.lookup(userInput)`

---

## 场景 4: Native Binary (EXE/SO/DLL)

### 工具
- **Ghidra** (D:\rj\KF\FBY\Ghidra\ghidra_11.3.1_PUBLIC\ghidraRun.bat)

### 执行步骤
```bash
# Headless 分析
D:\rj\KF\FBY\Ghidra\ghidra_11.3.1_PUBLIC\support\analyzeHeadless.bat ^
  <project_dir> <project_name> -import target.exe -postScript DecompileScript.java
```

### Native 二进制审计清单
- [ ] 硬编码字符串 (密码/IP/URL)
- [ ] 弱加密算法: DES, RC4, MD5 用于密码
- [ ] 缓冲区溢出: `strcpy`/`sprintf`/`gets` 无边界检查
- [ ] 格式化字符串: `printf(userInput)`
- [ ] 整数溢出/下溢
- [ ] UAF (Use After Free)
- [ ] 竞争条件: 无锁的多线程访问
- [ ] 导入函数: `CreateProcess` / `WinExec` / `system` 参数可控
- [ ] DLL 劫持: 加载 DLL 无完整路径
- [ ] 签名校验绕过: 直接 patch 二进制

---

## 通用审计流程 (适用所有场景)

### Step 1: 信息收集
- 识别文件类型 (file/magic bytes)
- 检测加壳/混淆 (PEiD, Detect It Easy)
- 提取字符串 (`strings` 命令)

### Step 2: 反编译/反汇编
- 选择匹配的工具 (见上方场景)
- 导出全部源码到本地目录

### Step 3: 静态分析
- 搜索危险函数调用
- 搜索硬编码密钥/凭证
- 分析认证/授权逻辑
- 分析加密实现
- 分析网络通信

### Step 4: 动态分析 (可选)
- 沙箱运行 (Windows Sandbox/VM)
- 网络抓包 (Wireshark/Fiddler)
- 调试器附加 (x64dbg/GDB)
- Hook 关键函数 (Frida)

### Step 5: 报告
- P0/P1/P2 分级
- PoC 代码 (无害验证)
- 修复建议
- CVE 关联

---

## 工具路径速查

| 工具 | 路径 |
|------|------|
| jadx | `D:\rj\KF\FBY\jadx\bin\jadx-gui.bat` |
| dnSpy | `D:\rj\KF\FBY\dnSpy\dnSpy.exe` |
| ILSpy | `D:\rj\KF\FBY\ILSpy\ILSpy.exe` |
| Ghidra | `D:\rj\KF\FBY\Ghidra\ghidra_11.3.1_PUBLIC\ghidraRun.bat` |
| JD-GUI | `D:\rj\KF\FBY\JD-GUI\jd-gui.jar` |
| ResourceHacker | `D:\rj\KF\FBY\ResourceHacker\ResourceHacker.exe` |
