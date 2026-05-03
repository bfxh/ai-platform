# 自动化测试系统

## 功能
- **软件启动测试**: 验证 .exe 能否正常启动并保持运行
- **项目测试**: 自动运行 pytest/cargo test 等项目测试
- **历史记录**: 每次测试结果保存到 `test_history.json`
- **知识库记录**: 测试结果自动写入 SQLite 知识库

## 使用

### 测试所有软件启动
```bash
python /python/MCP_Core/skills/auto_tester/skill.py --mode software
```

### 测试指定项目
```bash
python /python/MCP_Core/skills/auto_tester/skill.py --mode project --project browser-use-main
```

### 完整测试（软件+项目）
```bash
python /python/MCP_Core/skills/auto_tester/skill.py --mode all
```

## 覆盖软件
QClaw, StepFun, WorkBuddy, TraeCN, VSCode, Blender, Godot

## 覆盖项目
browser-use-main, browser-main, MCP_Core
