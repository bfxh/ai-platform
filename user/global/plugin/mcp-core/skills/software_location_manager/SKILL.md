# 软件位置管理器 (software_location_manager)

## 描述

软件位置管理技能，用于管理软件安装位置和自动扫描。

## 功能

### 1. 位置管理
- 添加自定义软件位置
- 删除软件位置
- 列出所有位置
- 自动扫描默认位置 (D:\rj, F:\rj)

### 2. 软件管理
- 扫描位置中的软件
- 搜索软件
- 列出所有软件
- 获取软件详情
- 更新软件列表

### 3. 自动扫描
- 自动扫描D:\rj和F:\rj目录
- 支持自定义位置的扫描
- 自动发现新软件

## 默认位置

- **D:\rj** - 软件安装目录1
- **F:\rj** - 软件安装目录2

## 用法

### MCP 调用

```json
{
  "skill": "software_location_manager",
  "action": "list_locations"
}
```

```json
{
  "skill": "software_location_manager",
  "action": "scan_locations"
}
```

```json
{
  "skill": "software_location_manager",
  "action": "add_location",
  "params": {
    "location": "E:\Software"
  }
}
```

```json
{
  "skill": "software_location_manager",
  "action": "search_software",
  "params": {
    "query": "chrome"
  }
}
```

## 动作列表

| 动作 | 描述 | 必需参数 |
|------|------|----------|
| add_location | 添加软件位置 | location |
| remove_location | 删除软件位置 | location_id |
| list_locations | 列出所有位置 | 无 |
| scan_locations | 扫描所有位置 | 无 |
| search_software | 搜索软件 | query |
| list_software | 列出所有软件 | 无 |
| get_software_details | 获取软件详情 | software_id |
| update_software | 更新软件列表 | 无 |

## 配置选项

| 参数 | 默认值 | 描述 |
|------|--------|------|
| config_file | software_locations.json | 配置文件路径 |

## 依赖

- Python 3.8+

## 输出

- 操作成功/失败状态
- 位置列表
- 软件列表
- 搜索结果
- 软件详情

## 使用场景

1. **软件管理**: 集中管理所有软件安装位置
2. **快速访问**: 快速查找和启动软件
3. **自动发现**: 自动发现新安装的软件
4. **系统维护**: 清理和管理软件安装

## 注意事项

- 默认位置 (D:\rj, F:\rj) 不能删除
- 扫描可能需要一些时间，取决于目录大小
- 配置文件会自动创建在当前目录
- 支持的文件类型: .exe, .lnk, 安装程序

## 扫描逻辑

1. 自动扫描D:\rj和F:\rj目录
2. 查找常见的可执行文件和快捷方式
3. 提取文件信息（大小、修改时间等）
4. 去重和分类管理
5. 持久化存储到配置文件
