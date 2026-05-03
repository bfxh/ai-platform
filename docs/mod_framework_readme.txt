# Minecraft 模组代码修改框架

## 设计原则
所有修改与模组jar文件分离，模组更新不会覆盖修改。

## 1.12.2 (我即是虫群v2.0) - CraftTweaker

### 修改文件位置
- 脚本目录: `%GAME_DIR%\.minecraft\versions\我即是虫群v2.0\scripts\`
- 配置目录: `%GAME_DIR%\.minecraft\versions\我即是虫群v2.0\config\`

### 已有脚本
- `values.zs` - 全局变量定义（优先级100，最先加载）
- `events.zs` - 事件处理（货币系统、死亡回城、经验取消等）
- `recipes.zs` - 配方修改（移除物品、添加自定义配方）
- `reloca.zs` - 重定位脚本
- `firearm.zs` - 枪械相关

### 添加新修改
1. 创建新 `.zs` 文件在 scripts 目录
2. 使用 `#loader` 指令指定加载阶段
3. 使用 `#priority` 控制加载顺序（数字越大越先加载）

### 更新模组后
- 脚本文件不受影响（不在jar内）
- 如果模组API变化，需要检查脚本中的物品ID是否仍然有效
- 运行 `/ct syntax` 命令检查语法错误

## 1.20.4 (新起源) - KubeJS

### 修改文件位置
- 启动脚本: `%GAME_DIR%\.minecraft\versions\新起源\kubejs\startup_scripts\`
- 服务端脚本: `%GAME_DIR%\.minecraft\versions\新起源\kubejs\server_scripts\`
- 客户端脚本: `%GAME_DIR%\.minecraft\versions\新起源\kubejs\client_scripts\`
- 数据包: `%GAME_DIR%\.minecraft\versions\新起源\kubejs\data\`
- 资源包: `%GAME_DIR%\.minecraft\versions\新起源\kubejs\assets\`

### 添加新修改
1. `startup_scripts/` - 注册新物品、方块、流体等
2. `server_scripts/` - 修改配方、标签、战利品表等
3. `client_scripts/` - 修改提示信息、JEI信息等

### 更新模组后
- KubeJS脚本不受影响
- 运行 `/kubejs reload` 重新加载脚本
- 检查控制台是否有错误日志

## 通用修改方式（不修改jar）

### 1. 配方修改 (CraftTweaker / KubeJS)
修改合成配方、熔炼配方等

### 2. 标签修改 (KubeJS / 数据包)
修改物品/方块标签，影响合成和交互

### 3. 配置文件修改
修改 `config/` 目录下的 `.cfg` / `.json` / `.toml` 文件

### 4. 战利品表修改 (KubeJS / 数据包)
修改怪物掉落、宝箱内容等

### 5. 深度代码修改 (Mixin)
如需修改Java代码逻辑，创建独立的Mixin模组:
- 修改与模组jar分离
- 模组更新后Mixin自动适配（除非目标方法签名变化）
- 位置: `mods/` 目录下的独立jar文件
