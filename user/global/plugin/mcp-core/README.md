# MCP Core 完整文档

## 快速开始

```bash
# 启动服务器
python server.py

# 或使用 CLI
python cli.py server start

# 列出技能
python cli.py skill list

# 调用技能
python cli.py skill call network_transfer -p '{"action":"discover"}'

# 运行工作流
python cli.py workflow run dual_pc_setup
```

## 目录结构

```
\python\MCP_Core\
├── server.py                   # MCP Server
├── cli.py                      # 命令行工具
├── config.py                   # 配置中心
├── config_validator.py         # 配置验证
├── logger.py                   # 日志系统
├── event_bus.py                # 事件总线
├── cache.py                    # 缓存系统
├── skill_installer.py          # 技能安装器
├── SKILL_INTEGRATION_GUIDE.md  # 集成指南
├── ARCHITECTURE_V2.md          # 架构文档
│
├── skills/                     # 技能目录
│   ├── base.py                 # 技能基类
│   ├── network_transfer/       # 网络传输
│   ├── exo_cluster/            # EXo集群
│   ├── notification/           # 通知
│   ├── system_config/          # 系统配置
│   └── file_backup/            # 文件备份
│
├── workflow/                   # 工作流目录
│   ├── engine.py               # 工作流引擎
│   └── templates/              # 工作流模板
│
├── tests/                      # 测试目录
│   ├── test_skills/            # 技能测试
│   └── test_workflow/          # 工作流测试
│
└── logs/                       # 日志目录
```

## 核心组件

### 1. 技能系统
- 基于 `Skill` 基类
- 自动注册和发现
- 参数验证
- 事件驱动

### 2. 工作流引擎
- JSON 定义
- 依赖管理
- 并行执行
- 状态持久化

### 3. 事件总线
- 发布订阅模式
- 异步处理
- 事件持久化

### 4. 配置系统
- 统一配置管理
- 环境变量支持
- 配置验证
- 热重载

## 添加新技能

```bash
# 使用安装器
python skill_installer.py create my_skill --description "我的技能"
python skill_installer.py register my_skill

# 手动创建
# 1. 在 skills/ 下创建目录
# 2. 创建 skill.py 实现 Skill 基类
# 3. 在 server.py 中注册
```

## 测试

```bash
# 运行所有测试
cd tests
python run_tests.py

# 详细输出
python run_tests.py -v

# 只运行特定测试
python run_tests.py -k network_transfer
```

## CLI 命令

```bash
# 技能管理
mcp skill list              # 列出技能
mcp skill call <name>       # 调用技能
mcp skill info <name>       # 查看详情

# 工作流管理
mcp workflow list           # 列出工作流
mcp workflow run <name>     # 运行工作流
mcp workflow show <name>    # 查看详情

# 系统管理
mcp server start            # 启动服务
mcp status                  # 查看状态
mcp config show             # 显示配置
```

## 配置示例

```json
{
  "version": "2.0.0",
  "server": {
    "host": "localhost",
    "port": 8766,
    "protocol": "websocket"
  },
  "skills": {
    "network_transfer": {
      "enabled": true,
      "transfer_port": 50000
    }
  }
}
```

## 日志

日志文件位于 `\python\MCP_Core\logs\`

- `{date}.log` - 普通日志
- `{skill}_error.log` - 错误日志

## 更多信息

- [技能集成指南](SKILL_INTEGRATION_GUIDE.md)
- [架构文档](ARCHITECTURE_V2.md)
