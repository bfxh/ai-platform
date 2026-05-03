# Workflow Engine Skill

工作流引擎与自动化编排技能

## 功能

- 工作流定义与执行
- 步骤依赖管理
- 条件分支
- 并行执行
- 错误处理与重试
- 状态持久化

## 工作流定义格式

```json
{
  "name": "工作流名称",
  "version": "1.0",
  "steps": [
    {
      "id": 1,
      "name": "步骤名称",
      "command": "执行的命令",
      "depends_on": [依赖步骤ID],
      "target": "local/remote/both",
      "retry": 3,
      "timeout": 300
    }
  ]
}
```

## 工作流类型

### 顺序工作流
步骤按顺序执行，前一个完成后执行下一个

### 并行工作流
多个步骤同时执行，等待全部完成

### 条件工作流
根据条件选择执行路径

### 循环工作流
重复执行某一步骤直到条件满足

## 核心命令

### 执行工作流
```bash
python workflow_runner.py --workflow workflow_name.json
```

### 查看工作流状态
```bash
python workflow_runner.py --status
```

### 暂停/恢复工作流
```bash
python workflow_runner.py --pause
python workflow_runner.py --resume
```

## 内置工作流

### dual-pc-setup
完整双电脑集群搭建

### file-transfer-only
仅文件传输

### exo-cluster-setup
仅 EXo 集群配置

### system-optimization
系统优化配置

## 回调与通知

工作流支持以下事件回调:
- step_start: 步骤开始
- step_complete: 步骤完成
- step_error: 步骤错误
- workflow_complete: 工作流完成

## 状态文件

工作流状态保存在:
```
\python\.workflow\state.json
```
