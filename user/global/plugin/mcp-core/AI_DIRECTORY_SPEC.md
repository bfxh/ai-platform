# \python 目录规范 v2.0
> 最后更新：2026-04-11
> 用途：定义 \python 的收纳边界、AI内容放前审查规则、备份策略

---

## 目录边界（绝对规则）

**\python = AI专属目录**，只允许以下类型进入：

| 类型 | 示例 | 是否允许 |
|------|------|---------|
| MCP Core 系统 | MCP_Core/, skills/, nl_router.py, mcp_skill_server.py | ✅ |
| AI工具本体 | QClaw/, StepFun/, WorkBuddy/（放在 %SOFTWARE_DIR%\AI\） | ✅ |
| MCP 服务器实现 | mcp_*.py, plugin_*.py | ✅ |
| 知识库数据 | knowledge_base.db, software_inventory.json | ✅ |
| Skill 实现 | \python\MCP_Core\skills\ 下的所有技能目录 | ✅ |
| AI项目源码 | Blender AI插件/, browser-use/, GodotBlenderBridge/ | ✅ |
| AI项目文档 | .PROJECT.md, AI_UPGRADE_PLAN.md | ✅ |
| AI生态说明 | AI_TOOLKIT_ECOSYSTEM_COMPLETE.md | ✅ |
| **临时脚本（bat/ps1/py）** | clone_*.bat, 一键*.bat, auto_*.ps1 | ❌ → 移到 %SOFTWARE_DIR%\GJ\ |
| **模组/游戏开发文件** | Terraria模组文档, UE5插件脚本, Godot项目 | ❌ → 移到工作区或 F:\储存 |
| **下载缓存** | *.zip, *.msi, *.exe 下载缓存 | ❌ → 移到 %SOFTWARE_DIR%\GJ\ |
| **个人工作文件** | *.cs 源码（非AI项目）, 配置文件 | ❌ → 移到工作区 |

---

## AI内容审查流程（放前必查）

**规则解读：非AI文件不是绝对禁止进入，而是需要审查后决定。**

凡是要放进 \python 的内容，回答以下问题：

### 审查清单
1. **这个文件是 AI 相关的吗？**
   - MCP/Skill/Agent → ✅ 直接放
   - AI工具配置/模型/提示词 → ✅ 直接放
   - 非AI但具有AI扩展价值（如：开源引擎可被AI调用）→ ✅ 审查后放
   - 通用脚本/纯游戏开发/个人项目 → ❌ 移到其他目录
2. **这个文件在其他目录是否有更合适的位置？**
   - 下载脚本 → %SOFTWARE_DIR%\GJ\
   - 游戏模组 → F:\储存\ + 工作区
   - 个人项目 → %USERPROFILE%\WorkBuddy\
3. **如果多人协作，是否需要放进版本控制？**
   - MCP/Skill → 可以
   - 临时脚本 → 不需要
4. **这个文件是否有备份价值？**
   - AI核心系统 / 知识库 / 配置 → ✅ 必须进每日备份
   - 临时缓存 / 下载文件 → ❌ 不备份

---

## 当前目录清理记录（2026-04-11）

| 原路径 | 迁移到 | 原因 |
|--------|--------|------|
| \python\clone_*.bat | %SOFTWARE_DIR%\GJ\ | 通用下载脚本 |
| \python\一键*.bat | %SOFTWARE_DIR%\GJ\ | 通用启动脚本 |
| \python\auto_*.ps1 | %SOFTWARE_DIR%\GJ\ | 通用自动化脚本 |
| \python\泰拉瑞亚*.md | %USERPROFILE%\WorkBuddy\20260410084126\docs\ | 游戏开发文档 |
| \python\*.cs（非AI项目） | F:\储存\备份\ | 非AI源码 |
| \python\*.zip | %SOFTWARE_DIR%\GJ\download_cache\ | 下载缓存 |
| \python\*.msi | %SOFTWARE_DIR%\GJ\download_cache\ | 安装包缓存 |
| \python\download_*.py | %SOFTWARE_DIR%\GJ\ | 通用下载工具 |
| \python\auto_decompile*.py | F:\储存\备份\ | 游戏逆向工具 |
| \python\发送到_*.bat | %SOFTWARE_DIR%\GJ\ | 网络传输脚本 |
| \python\快速*.md | %SOFTWARE_DIR%\GJ\docs\ | 通用工具说明 |
| \python\*.gd | F:\储存\备份\ | Godot脚本（非AI项目） |
| \python\新建游戏项目/ | F:\储存\新建游戏项目\ | 游戏项目 |
| \python\beyond_ue5*.gd | F:\储存\UE5插件\ | UE5插件源码 |

---

## 备份策略

### 每日自动备份
- **来源**：`\python\`（整个目录）
- **目标**：`F:\储存\AI备份\YYYY-MM-DD\`
- **时间**：每天 13:00（午后，用户已开工，能覆盖全天变化）
- **保留**：最近 30 天（自动删除旧备份）

### 备份内容
- 整个 \python 目录（压缩为 .zip）
- 排除：download_cache, *.zip, *.msi 等临时文件

### 备份脚本
见：`\python\MCP_Core\scripts\daily_backup.py`

