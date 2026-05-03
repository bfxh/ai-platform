# Narsil MCP

集成到 GSTACK 架构的 Narsil MCP 模块，用于深度代码分析。

## 目录结构

```
\python\MCP\BC\narsil_mcp\
├── narsil-server.exe       # Narsil 服务器（Rust 编译）
├── narsil-client.py        # Python 客户端
├── config.toml            # 配置文件
└── README.md             # 本文件
```

## 配置

在 `config.toml` 中配置以下参数:

- `port`: 服务端口，默认 8401
- `server_path`: narsil-server.exe 路径
- `analysis_targets`: 要分析的代码库路径列表

## 使用方法

### 启动 Narsil MCP

```powershell
gstack narsil start
```

### 停止 Narsil MCP

```powershell
gstack narsil stop
```

### 检查状态

```powershell
gstack narsil status
```

### 深度代码分析

```powershell
gstack lint --deep <file_path>
```

## 可用命令

- `analyze <path>`: 深度分析文件
- `symbols <path>`: 获取文件中的符号（函数、类等）
- `strings <path>`: 查找字符串字面量
- `deps <path>`: 获取文件依赖

## 与 GSTACK 集成

Narsil MCP 已集成到 `gstack lint --deep` 命令中，提供：

- 函数、类定义的符号查找
- 未使用导入的识别
- 循环依赖检测
- 复杂度超标函数识别
- 硬编码绝对路径检测

## 架构守护增强

在 `architect_enforce/skill.py` 中，Narsil MCP 用于验证代码是否访问了禁止的目录：

```python
bad_refs = narsil_client.find_string_literals(file, pattern=r"[A-Z]:\\")
```

## 注意事项

- 需要 Rust 编译环境来构建 narsil-server.exe
- 端口 8401 不能被占用
- 确保 analysis_targets 路径配置正确
