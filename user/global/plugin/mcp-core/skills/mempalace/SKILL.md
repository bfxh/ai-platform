# MemPalace AI记忆系统 (mempalace)

## 描述

基于古希腊记忆术的AI记忆宫殿系统，提供长期记忆管理、知识图谱和智能检索功能。

## 功能

### 1. 记忆宫殿管理
- 创建和管理记忆宫殿的侧厅（Wings）
- 在侧厅中创建房间（Rooms）
- 建立房间之间的连接（Tunnels）

### 2. 长期记忆存储
- 使用衣柜（Closets）和抽屉（Drawers）结构存储记忆
- AAAK压缩格式支持，高效存储
- 元数据标记和分类
- ChromaDB向量搜索（可选）

### 3. 知识图谱
- 支持知识三元组（Subject-Predicate-Object）
- 时间有效性管理
- 置信度评分
- 冲突检测和解决

### 4. 智能检索
- 基于语义的向量搜索
- 文本匹配搜索
- 多维度过滤
- 相关性排序

## 记忆宫殿结构

```
记忆宫殿
├── 侧厅 (Wings)
│   ├── 项目侧厅
│   ├── 人物侧厅
│   └── 主题侧厅
├── 房间 (Rooms)
│   ├── 房间1
│   ├── 房间2
│   └── 房间3
├── 衣柜 (Closets)
│   ├── 衣柜1 (摘要 + AAAK压缩数据)
│   └── 衣柜2
└── 抽屉 (Drawers)
    ├── 抽屉1 (原始文本 + 元数据)
    └── 抽屉2
```

## 用法

### 命令行

```bash
# 创建侧厅
python /python/MCP_Core/skills/mempalace/skill.py create_wing "我的项目" project

# 创建房间
python /python/MCP_Core/skills/mempalace/skill.py create_room "我的项目" "会议记录"

# 存储记忆
python /python/MCP_Core/skills/mempalace/skill.py store_memory "我的项目" "会议记录" "今天讨论了AI记忆系统的集成方案"

# 检索记忆
python /python/MCP_Core/skills/mempalace/skill.py retrieve_memory "我的项目" "会议记录"

# 搜索记忆
python /python/MCP_Core/skills/mempalace/skill.py search "AI集成方案"

# 添加知识
python /python/MCP_Core/skills/mempalace/skill.py add_knowledge "MemPalace" "是" "AI记忆系统"

# 查询知识
python /python/MCP_Core/skills/mempalace/skill.py query_knowledge --subject "MemPalace"

# 获取统计信息
python /python/MCP_Core/skills/mempalace/skill.py get_stats

# 导出数据
python /python/MCP_Core/skills/mempalace/skill.py export_data backup.json

# 导入数据
python /python/MCP_Core/skills/mempalace/skill.py import_data backup.json
```

### MCP 调用

```json
{
  "skill": "mempalace",
  "action": "create_wing",
  "params": {
    "wing_name": "我的项目",
    "wing_type": "project"
  }
}
```

```json
{
  "skill": "mempalace",
  "action": "store_memory",
  "params": {
    "wing_name": "我的项目",
    "room_name": "会议记录",
    "memory_text": "今天讨论了AI记忆系统的集成方案",
    "metadata": {
      "date": "2026-04-09",
      "importance": "high"
    }
  }
}
```

```json
{
  "skill": "mempalace",
  "action": "search",
  "params": {
    "query": "AI集成方案",
    "limit": 5
  }
}
```

## 动作列表

| 动作 | 描述 | 必需参数 |
|------|------|----------|
| create_wing | 创建侧厅 | wing_name, wing_type |
| create_room | 创建房间 | wing_name, room_name |
| store_memory | 存储记忆 | wing_name, room_name, memory_text |
| retrieve_memory | 检索记忆 | wing_name, room_name (可选) |
| search | 搜索记忆 | query |
| add_knowledge | 添加知识三元组 | subject, predicate, object |
| query_knowledge | 查询知识图谱 | subject, predicate, object (可选) |
| detect_conflicts | 检测知识冲突 | 无 |
| get_stats | 获取统计信息 | 无 |
| export_data | 导出数据 | file_path |
| import_data | 导入数据 | file_path |

## 侧厅类型

- **project**: 项目相关记忆
- **person**: 人物相关记忆
- **topic**: 主题相关记忆

## AAAK压缩格式

AAAK (Abstract Association and Abstraction Kit) 是一种高效的记忆压缩格式：
- 提取关键信息
- 建立关联索引
- 抽象化表示
- 保持可读性

## 知识图谱

知识图谱使用三元组表示：
- **Subject**: 主体
- **Predicate**: 谓词/关系
- **Object**: 客体
- **Confidence**: 置信度 (0.0-1.0)
- **Valid Until**: 有效期

## 配置选项

| 参数 | 默认值 | 描述 |
|------|--------|------|
| db_path | mempalace.db | SQLite数据库路径 |
| chroma_path | chroma_data | ChromaDB数据路径 |

## 依赖

- Python 3.8+
- SQLite3 (内置)
- ChromaDB (可选，用于向量搜索)

## 输出

- 操作成功/失败状态
- 详细的消息和错误信息
- 统计数据
- 检索结果列表

## 使用场景

1. **项目管理**: 存储项目会议记录、决策、里程碑
2. **学习笔记**: 整理学习内容、知识点、关联关系
3. **个人日记**: 记录重要事件、想法、反思
4. **知识管理**: 构建个人知识库、概念图谱
5. **研究笔记**: 整理研究资料、文献、发现

## 注意事项

- ChromaDB未安装时，将使用文本搜索作为降级方案
- 数据库文件会自动创建在当前目录
- 建议定期导出数据作为备份
- 知识冲突检测可以帮助发现不一致的信息
