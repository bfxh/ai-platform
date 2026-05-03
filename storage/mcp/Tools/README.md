# Tools - 工具类 MCP

工具类 MCP 文件索引

## 目录路径
`\python\MCP\Tools`

## 文件清单 (共 32 个文件)

### 桌面自动化
| 文件名 | 描述 |
|--------|------|
| da.py | 桌面自动化工具 |
| screen_eye.py | 后台截屏工具 |

### 下载工具
| 文件名 | 描述 |
|--------|------|
| download_manager.py | 智能下载管理器 |
| download_accelerator.py | 下载加速器 |
| aria2_mcp.py | Aria2 下载管理器 |
| browser_download_interceptor.py | 浏览器下载拦截器 |

### 网络工具
| 文件名 | 描述 |
|--------|------|
| net_pro.py | 网络工具 |
| network_optimizer.py | 网络优化工具 |

### 软件管理
| 文件名 | 描述 |
|--------|------|
| local_software.py | 本地软件管理 |
| software_monitor.py | 软件监控 |
| software_upgrade_manager.py | 软件升级管理 |
| dev_mgr.py | 开发软件管理 |

### 系统工具
| 文件名 | 描述 |
|--------|------|
| system_monitor.py | 系统监控 |
| memory_monitor.py | 内存监控 |
| gpu_config.py | GPU 配置 |
| lazy_service_manager.py | 懒加载服务管理 |
| hybrid_cache.py | 混合缓存 |
| logging_config.py | 日志配置 |

### AI 工具
| 文件名 | 描述 |
|--------|------|
| ai_memory.py | AI 记忆系统 |
| auto_translate.py | 智能自动翻译 |

### 安全工具
| 文件名 | 描述 |
|--------|------|
| aes_scan.py | AES 密钥扫描 |
| aes_memory.py | AES 内存扫描 |
| pua_supervisor.py | PUA 监控 |

### 配置和文件系统
| 文件名 | 描述 |
|--------|------|
| config_center.py | 配置中心 |
| filesystem_server.py | 文件系统服务器 |
| check_ext.py | 扩展检查 |
| kill_trae_and_clear_cache.py | TRAE 缓存清理 |

### 其他
| 文件名 | 描述 |
|--------|------|
| extract.py | 模型提取工具 |
| mcp_best_practices.py | MCP 最佳实践 |
| mcp_vision_tools.py | MCP 视觉工具 |
| tencent_mcp.py | 腾讯 MCP |
| tencent_docs.py | 腾讯文档 |
| test_upgrade_manager.py | 升级管理器测试 |

### 磁盘索引工具
| 文件名 | 描述 |
|--------|------|
| disk_scanner.py | D盘全盘索引扫描工具 |
| disk_query.py | TRAE快速项目查询工具 |
| disk_index.db | 索引数据库 (SQLite) |
| disk_indexer_config.json | 索引配置 |

## 磁盘索引工具使用说明

### 功能
- 扫描D盘所有重要项目并建立索引
- 支持按类型/关键词/路径查询
- 生成结构化的索引数据库
- 输出适合TRAE直接使用的查询结果

### 快速查询示例
```bash
# 扫描并生成索引
python disk_scanner.py scan

# 搜索项目
python disk_query.py godot       # 搜索godot
python disk_query.py rust       # 搜索rust
python disk_query.py 泰拉        # 搜索中文

# 按分类筛选
python disk_query.py -c ai      # AI系统分类
python disk_query.py -c godot  # Godot分类

# 按技术栈筛选
python disk_query.py -t rust    # Rust技术
python disk_query.py -t python  # Python技术

# 显示所有项目
python disk_query.py --list

# 显示统计信息
python disk_query.py --stats

# 详细模式
python disk_query.py godot -v
```

### 数据库位置
- 索引数据库: `\python\MCP\Tools\disk_index.db`
- 配置: `\python\MCP\Tools\disk_indexer_config.json`

## 分类规则
- 桌面自动化
- 下载管理
- 网络工具
- 软件管理
- 系统监控
- AI 工具
- 安全工具
- 配置管理

## 创建时间
2026-04-24
