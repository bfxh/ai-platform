# RemoteLink 远程控制系统

> 38402L → 知识压缩 | 来源: \python\remote-control\

## 端口总表

| 端口 | 服务 | 协议 |
|------|------|------|
| 50050 | WebSocket控制 | WS |
| 50052 | UDP设备发现 | UDP |
| 52415 | EXO集群 | HTTP |
| 52416 | 任务队列 | HTTP |
| 52417 | 手机服务 | HTTP |
| 8080 | 文件上传 | HTTP |
| 8081 | 远程控制 | HTTP+WS |
| 8082 | 通知推送 | HTTP+WS |

## 消息协议 (protocol.py)

22种MessageType: HELLO/AUTH/AUTH_RESULT, SCREEN_FRAME/SCREEN_CONFIG, INPUT_MOUSE/INPUT_KEYBOARD/INPUT_CLIPBOARD, FILE_LIST/FILE_DOWNLOAD/FILE_UPLOAD/FILE_DATA, PROCESS_LIST/PROCESS_CONTROL/SERVICE_LIST/SERVICE_CONTROL, SYSTEM_COMMAND/SYSTEM_INFO/HARDWARE_MONITOR/POWER_CONTROL, EXO_STATUS/EXO_INFER, PING/PONG/ERROR

格式: `{"type":"<MessageType.value>","ts":<unix>,"data":{...}}`

认证: HELLO→AUTH(hmac.compare_digest)→AUTH_RESULT→screen_stream

### 核心类

- `ScreenCapture`: ImageGrab→缩放→JPEG→base64, MD5帧去重, 默认quality=80/scale=0.5/fps=15
- `InputController`: pyautogui优先→pynput降级, 文本用剪贴板注入(Set-Clipboard+SendKeys "^v")
- `FileTransfer`: CHUNK_SIZE=64KB, WS_MAX=10MB
- `RemoteControlServer/Client`: WS双向, start(host,port)/connect(host,port)

## 任务队列 (task_queue.py + queue_server.py + http_queue.py)

### 数据模型

```
TaskMessage: task_id(UUID[:12]), task_type, params, rules, priority(1-10), parent_id, children_ids(DAG), status(pending→running→reviewing→completed/rejected), retry_count/max_retries(3)
TaskType: AI_INFERENCE|CODE_REVIEW|VULN_SCAN|CODE_GENERATE|FILE_PROCESS|SHELL_COMMAND|CUSTOM
```

### 三级降级队列

| 实现 | 后端 | 特点 |
|------|------|------|
| TaskQueue | Redis ZSet+Hash+PubSub | 优先级排序, Key: remotelink:tasks:{pending/running/results} |
| MemoryTaskQueue | 内存List+Dict | 降级方案 |
| HTTPTaskQueue | HTTP远程 | 跨机器 |

### HTTP队列API (:52416)

POST /submit, /fetch(Header:X-Node-ID), /complete, /fail | GET /result/{task_id}, /stats, /nodes

## 执行引擎 (worker.py + orchestrator.py)

### TaskExecutor handler映射

| task_type | 执行逻辑 |
|-----------|----------|
| AI_INFERENCE | Ollama /api/chat, rules注入prompt末尾 |
| CODE_REVIEW | review prompt→Ollama JSON输出 |
| VULN_SCAN | port_scan(Test-NetConnection) / code_scan(5类模式:SQL注入/XSS/硬编码密钥/不安全反序列化/路径遍历) |
| CODE_GENERATE | Ollama生成 |
| FILE_PROCESS | read/write/list |
| SHELL_COMMAND | cmd /c, 白名单过滤 |

### RuleEnforcer默认规则: 金额Decimal/禁止硬编码密钥/必须异常处理

### orchestrator启动: --mode full|worker|scheduler, --queue URL, --redis URL, -i交互

交互命令: status, hw, ai <msg>, shell <cmd>, vuln <code>, quit

## 硬件控制 (hardware.py)

- ProcessManager: list/kill/start/find_by_name
- ServiceManager: list/start/stop/restart Windows服务
- SystemCommandExecutor: ALLOWED_COMMANDS白名单+BLOCKED_PATTERNS黑名单
- HardwareMonitor: CPU/内存(ctypes Win32API)/磁盘/GPU/网络
- PowerControl: shutdown/restart/lock/sleep/cancel(全@staticmethod)

## 设备发现 (discovery.py)

UDP广播 :50052, Magic=b'REMOTELINK'+JSON(DeviceInfo), 间隔3s, 离线超时30s
连接类型: 169.254.x.x→USB, 同/24→WIFI
USB ICS: COM对象HNetCfg.HNetShare

## HTTP服务层

### 远程控制 (:8081)
GET / (手机HTML), /ws (WS控制), token认证(URL参数或Bearer)

### 通知推送 (:8082)
GET / (通知中心HTML), /ws (WS推送), POST /notify {"title":"","body":""}
特性: WS广播+浏览器Notification+Windows BurntToast+历史100条

### 文件上传 (:8080)
GET / (上传HTML), POST /upload (multipart), GET /list
存储: D:\Shared, 限制100MB, 文件名sanitize+路径遍历防护

### 共享服务 (share_server.py)
SecureFileShare: 白名单+黑名单+路径遍历防护+操作日志
操作: list/upload/download/allow/block/stats

## EXO集群 (exo_bridge.py)

ExoClusterBridge: is_exo_installed/running, install(本地源F:\要搞的东西\exo_extract\exo-1.0.69→PyPI降级), start_node(python -m exo), cluster_status, available_models, infer(model,messages)→POST /v1/chat/completions
ExoRemoteProxy: 注册远程节点→转发推理请求

## 手机连接 (phone_connector.py)

HuaweiPhoneConnector: ADB connect/getprop/ls/pull/push, 端口52417
ADB路径: adb→%USERPROFILE%/adb/platform-tools/adb.exe→C:\adb\platform-tools\adb.exe

## 模块依赖

```
full_system ← discovery + notification + remote_control + share
orchestrator ← task_queue + http_queue + hardware + exo_bridge
worker ← task_queue + hardware
protocol ← hardware(延迟导入)
queue_server (独立)
http_queue (独立, aiohttp)
phone_connector ← http_queue
share_server ← http_queue
notification/remote_control/file_upload (独立, aiohttp)
```

外部依赖: websockets, PIL/Pillow, pyautogui, pynput, redis, aiohttp, requests, pyperclip
