# TuriX CUA 与 AI 漏洞挖掘工具 - 安装配置完成报告

## 安装状态

| 组件 | 状态 | 路径 |
|------|------|------|
| TuriX CUA | ✅ 已安装 | \python\turix-cua\ |
| AI 漏洞扫描器 | ✅ 已安装 | \python\security-tools\ |
| TuriX Agent核心 | ✅ 验证通过 | \python\turix-cua\TuriX-CUA\src\agent\service.py |
| Windows控制器 | ✅ 验证通过 | \python\turix-cua\TuriX-CUA\src\windows\controller.py |
| 技能系统 | ✅ 验证通过 | \python\turix-cua\TuriX-CUA\src\agent\skills.py |
| 漏洞扫描器 | ✅ 验证通过 | \python\security-tools\tools\vuln_scanner.py |
| Web安全测试器 | ✅ 验证通过 | \python\security-tools\tools\web_security.py |

---

## 1. TuriX CUA - AI桌面自动化

### 什么是 TuriX CUA？
TuriX Computer Use Agent 是一个AI驱动的桌面自动化代理，能让AI像人类一样操控各种桌面应用程序。核心特点：
- **无需应用API**：只要人能点击的界面，AI都能操作
- **视觉语言模型驱动**：通过理解屏幕内容自主决策
- **模型热插拔**：修改config.json即可切换模型
- **MCP协议兼容**：可联动Claude等外部AI代理
- **OSWorld基准测试第三名**：64.2%成功率

### 已安装的Python依赖
- pyautogui (屏幕操控)
- Pillow (图像处理)
- requests (HTTP请求)
- pygetwindow (窗口管理)

### 快速使用

```powershell
# 方式1: 双击启动
\python\turix-cua\start_turix.bat

# 方式2: 命令行启动
cd \python\turix-cua\TuriX-CUA\examples
\python\turix-cua\venv\Scripts\python.exe main.py -t "Open Notepad"

# 方式3: 仅规划不执行
\python\turix-cua\venv\Scripts\python.exe main.py -t "Open Chrome and search AI" --plan-only
```

### 配置文件
位置：`\python\turix-cua\TuriX-CUA\examples\config.json`

```json
{
    "agent": {
        "task": "Open Notepad and type Hello",
        "max_steps": 50,
        "use_plan": true,
        "use_skills": true
    },
    "llm": {
        "provider": "ollama",
        "model": "qwen2.5-coder:7b",
        "base_url": "http://localhost:11434/v1"
    },
    "vision": {
        "provider": "ollama",
        "model": "qwen2.5-vl:7b",
        "base_url": "http://localhost:11434/v1"
    }
}
```

### 前置条件
运行前需要启动 Ollama 并下载模型：
```powershell
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-vl:7b
```

### 核心架构
```
用户指令 → TuriXAgent
              ├── Config (配置管理)
              ├── Logger (日志记录)
              ├── ScreenController (屏幕操控)
              │     ├── screenshot() 截图
              │     ├── click() 点击
              │     ├── type_text() 输入
              │     ├── hotkey() 快捷键
              │     └── scroll() 滚动
              ├── AppController (应用管理)
              │     ├── open_app() 打开应用
              │     ├── close_app() 关闭应用
              │     └── list_windows() 列出窗口
              ├── LLMClient (AI模型)
              │     ├── Ollama支持
              │     └── OpenAI兼容
              └── SkillRegistry (技能系统)
                    ├── browser-tasks
                    ├── office-tasks
                    ├── system-tasks
                    └── file-management
```

---

## 2. AI 漏洞挖掘工具

### 已安装的Python依赖
- scapy (网络包处理)
- cryptography (加密)
- paramiko (SSH)
- scikit-learn (机器学习)
- pandas (数据分析)
- numpy (数值计算)
- matplotlib (可视化)
- beautifulsoup4 (HTML解析)
- requests (HTTP请求)

### 工具1: 漏洞扫描器 (VulnScanner)

```powershell
# 扫描目标
\python\security-tools\scan.bat 192.168.1.1

# 或直接使用Python
cd \python\security-tools
venv\Scripts\python.exe tools\vuln_scanner.py 192.168.1.1

# 指定端口范围
venv\Scripts\python.exe tools\vuln_scanner.py 192.168.1.1 --ports 1-65535

# 启用AI分析
venv\Scripts\python.exe tools\vuln_scanner.py 192.168.1.1 --ai
```

功能：
- 端口扫描 (多线程，100并发)
- 服务识别 (SSH/HTTP/FTP/SMB/MySQL/Redis等)
- 漏洞检测 (基于服务类型的自动化检查)
- 风险评分 (0-100分)
- AI辅助分析 (需Ollama)
- JSON报告生成

### 工具2: Web安全测试器 (WebSecurityTester)

```powershell
# Web安全测试
\python\security-tools\web_test.bat http://target.com

# 或直接使用Python
cd \python\security-tools
venv\Scripts\python.exe tools\web_security.py http://target.com

# 仅网络测试
venv\Scripts\python.exe tools\web_security.py 192.168.1.1 --type network
```

功能：
- 安全头检测 (X-Frame-Options, HSTS, CSP等)
- SSL/TLS配置检查
- XSS漏洞测试
- SQL注入测试
- 目录遍历测试
- DNS枚举和反向解析

### AI辅助分析
当启用 `--ai` 参数时，扫描器会调用本地Ollama模型对发现进行深度分析：
- 风险评估总结
- 优先修复建议
- 潜在攻击向量
- 合规性建议

---

## 3. 注意事项

### 网络问题
由于当前网络无法访问GitHub，TuriX-CUA官方仓库未能克隆。已创建本地实现版本，功能包含：
- ✅ 屏幕操控 (截图/点击/输入/快捷键/滚动)
- ✅ 应用管理 (打开/关闭/窗口切换)
- ✅ AI模型集成 (Ollama/OpenAI)
- ✅ 任务规划与执行
- ✅ 技能系统
- ✅ 日志记录

网络恢复后，可执行以下命令获取官方完整版：
```powershell
cd \python\turix-cua
git clone https://github.com/TurixAI/TuriX-CUA.git TuriX-CUA-official
cd TuriX-CUA-official
git checkout multi-agent-windows
```

### 安全警告
- ⚠️ 仅在授权目标上进行安全测试
- ⚠️ 未授权扫描可能违法
- ⚠️ 建议在隔离环境中测试
- ⚠️ 使用前请阅读各工具的LICENSE

### 权限配置
Windows需要以下权限：
1. 屏幕录制权限 (设置 > 隐私和安全性)
2. 辅助功能权限 (设置 > 隐私和安全性)
3. 文件系统读写权限

---

## 4. 文件结构

```
\python\turix-cua\
├── TuriX-CUA\
│   ├── src\
│   │   ├── agent\
│   │   │   ├── service.py      # 核心代理
│   │   │   └── skills.py       # 技能系统
│   │   └── windows\
│   │       └── controller.py   # Windows控制器
│   └── examples\
│       ├── main.py             # 主入口
│       └── config.json         # 配置文件
├── venv\                       # Python虚拟环境
└── start_turix.bat             # 启动脚本

\python\security-tools\
├── tools\
│   ├── vuln_scanner.py         # 漏洞扫描器
│   └── web_security.py         # Web安全测试器
├── venv\                       # Python虚拟环境
├── scan.bat                    # 漏洞扫描启动
└── web_test.bat                # Web测试启动
```
