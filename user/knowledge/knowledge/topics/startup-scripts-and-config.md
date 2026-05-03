---
title: 启动脚本与配置参考
date: 2026-04-29
source: 实践部署
tags: [scripts, startup, config, bun, ollama, environment]
---

# 启动脚本与配置参考

## 一、环境依赖

| 工具 | 版本 | 安装方式 | 路径 |
|------|------|----------|------|
| Bun | 1.3.13 | npm install -g bun | C:\Users\888\AppData\Roaming\npm\bun.cmd |
| Node.js | 22.22.2 | 系统安装 | node |
| Ollama | 0.21 | 系统安装 | D:\rj\Ollama\ollama.exe |
| Python | 3.12 | 系统安装 | C:\Users\888\AppData\Local\Programs\Python\Python312 |

## 二、启动脚本清单

| 脚本 | 路径 | 功能 |
|------|------|------|
| start_clause.bat | \python\scripts\launch\start_clause.bat | 一键启动全部（Ollama+VCPToolBox+面板+Claude Code） |
| start_vcp_bridge.bat | \python\scripts\launch\start_vcp_bridge.bat | 仅启动后台桥接服务（不影响 TRAE） |
| auto_start_vcp.vbs | \python\scripts\launch\auto_start_vcp.vbs | VBS 静默启动（用于开机自启） |
| clause_env | \python\scripts\launch\clause_env | Claude Code .env 模板 |

## 三、start_clause.bat 流程

```
[1/4] 检查 Ollama (11434) → 不在则启动
[2/4] 检查 VCPToolBox API (6005) → 不在则启动 server.js
[3/4] 检查 VCPToolBox Admin (6006) → 不在则启动 adminServer.js
[4/4] 打开管理面板浏览器
      → 按任意键启动 Claude Code TUI
```

## 四、开机自启

已注册到 Windows 启动项：
- 快捷方式：C:\Users\888\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\VCPToolBox Bridge.lnk
- 目标：wscript.exe "\python\scripts\launch\auto_start_vcp.vbs"
- 启动：Ollama + VCPToolBox API (6005) + Admin (6006)

## 五、端口映射

| 端口 | 服务 | 说明 |
|------|------|------|
| 11434 | Ollama | 本地模型推理 |
| 6005 | VCPToolBox API | OpenAI 兼容 API 桥接 |
| 6006 | VCPToolBox Admin | 管理面板 Web UI |
| 11436 | WS Bridge (可选) | Ollama WebSocket 桥接 |

## 六、删除保护规则

已写入 \python\.trae\user_rules.md：
- 禁止自动删除任何文件或目录
- 禁止使用 rm/del/rmdir/shutil.rmtree/os.remove
- 需要删除时先列出内容，等用户确认
- 不影响 TRAE 正常的代码编辑、创建、读取、搜索操作

## 七、踩坑记录

### 7.1 Bun 不在系统 PATH
- 症状：bun 命令找不到
- 原因：npm install -g bun 安装到 C:\Users\888\AppData\Roaming\npm\，但不在 PATH
- 解决：启动脚本中 `set PATH=C:\Users\888\AppData\Roaming\npm;%PATH%`

### 7.2 VCPToolBox 管理面板打不开
- 症状：访问 /AdminPanel/ 返回 302 重定向到 6006，但 6006 无服务
- 原因：VCPToolBox 双进程架构，adminServer.js 需要单独启动
- 解决：同时启动 server.js (6005) 和 adminServer.js (6006)

### 7.3 VCPToolBox IP 封禁
- 症状：访问面板返回 429 Too Many Requests
- 原因：多次未带 Authorization 头请求触发安全机制
- 解决：重启 VCPToolBox 进程解除封禁

### 7.4 hnswlib-node 编译失败
- 症状：npm install 报错 hnswlib-node build fail
- 原因：缺少 C++ 编译环境
- 解决：npm install --ignore-scripts，然后 npm rebuild better-sqlite3

### 7.5 .env 文件写入失败
- 症状：.env 文件为空
- 原因：\python CLAUDE\ 路径不在 TRAE 允许列表中
- 解决：通过启动脚本 copy /Y clause_env .env 方式创建
