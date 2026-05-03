# gstack_core - GSTACK 工作流引擎

GSTACK 是 \python 的核心工作流引擎，优先级最高。

**状态**: 模块已配置但尚未独立部署。功能分散在:
- `\python\core\dispatcher.py` — 命令调度
- `\python\core\workflow_engine.py` — 工作流执行
- `\python\ai_architecture.json` — GSTACK 配置 (commands 列表)

**待实现**: 独立的 `gstack_core.py` 主入口文件
