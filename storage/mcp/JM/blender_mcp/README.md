# Blender MCP

集成到 GSTACK 架构的 Blender MCP 模块，用于自然语言控制 Blender。

## 目录结构

```
\python\MCP\JM\blender_mcp\
├── src\
│   └── server.py          # Blender MCP 服务器
├── config.json            # 配置文件
└── README.md             # 本文件
```

## 配置

在 `config.json` 中配置以下参数:

- `port`: 服务端口，默认 8400
- `blender_path`: Blender 可执行文件路径
- `auto_restart`: 是否自动重启
- `heartbeat_interval`: 心跳检测间隔（秒）

## 使用方法

### 启动 Blender MCP

```powershell
gstack blender start
```

### 停止 Blender MCP

```powershell
gstack blender stop
```

### 检查状态

```powershell
gstack blender status
```

## 可用命令

- `scene.info`: 获取当前场景信息
- `objects.list`: 列出场景中的所有对象
- `object.add`: 添加新对象
- `object.delete <name>`: 删除指定对象

## 与 GSTACK 集成

Blender MCP 已集成到 GSTACK 的自检流程中，如果服务离线会自动拉起。

## 注意事项

- 服务器代码需要在 Blender 内部运行
- 确保配置正确的 Blender 路径
- 端口 8400 不能被其他程序占用
