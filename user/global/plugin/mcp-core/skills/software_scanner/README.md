# 软件库扫描器

## 功能
- 递归扫描 `D:\rj` 和 `F:\rj` 所有目录
- 识别 .exe 可执行文件和项目目录
- 按类型分类（AI工具/IDE/游戏引擎/3D工具/浏览器/系统工具）
- 写入 SQLite 知识库 + MEMORY.md
- 生成清单报告

## 使用
```bash
python /python/MCP_Core/skills/software_scanner/skill.py
```

## 输出
- `\python\MCP_Core\data\software_inventory.json` - 完整清单
- `\python\MCP_Core\data\software_inventory_report.md` - 分类报告
- 知识库 `software_inventory` 表
