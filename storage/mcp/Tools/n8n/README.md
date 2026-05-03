# n8n 工作流集成

集成到 GSTACK 架构的 n8n 工作流自动化平台。

## 目录结构

```
\python\MCP\Tools\n8n\
├── workflows\               # n8n 工作流 JSON 文件
├── docker-compose.yml       # Docker 配置
└── README.md               # 本文件
```

## 快速启动

### 启动 n8n

```powershell
gstack workflow start
```

### 停止 n8n

```powershell
gstack workflow stop
```

### 查看状态

```powershell
gstack workflow status
```

### 打开 Web UI

```powershell
gstack workflow ui
```

## 手动启动

如果 Docker 可用：

```bash
cd \python\MCP\Tools\n8n
docker-compose up -d
```

n8n Web UI 将在 http://localhost:5678 访问。

## 内置工作流模板

### 1. CC 定时清理

扫描 `CC/3_Unused` 目录，自动归档超过 7 天的文件。

**触发方式**: 每周日凌晨 2:00 自动执行

### 2. 渲染队列

监听 `\python\Inbox\` 目录，有新的 `.blend` 文件时自动调用 Blender MCP 渲染。

**触发方式**: 文件系统监视

### 3. 健康报告推送

每天 9:00 生成 GSTACK 健康报告，发送到指定邮箱/飞书。

**触发方式**: 定时执行

## 与 GSTACK 集成

在 `commands.ps1` 中添加了以下命令：

- `gstack workflow start` - 启动 n8n
- `gstack workflow stop` - 停止 n8n
- `gstack workflow status` - 检查状态
- `gstack workflow ui` - 打开 Web UI
- `gstack workflow trigger <name>` - 触发指定工作流

## 注意事项

- 确保已安装 Docker
- 端口 5678 不能被占用
- 首次启动可能需要几分钟初始化
