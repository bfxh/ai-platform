# TRAE IDE — 项目规则路由

本文件不再包含具体规则。所有项目专属规则已迁移到 `.ai-rules/` 目录。

## [!!] 执行前必读

请读取当前项目根目录下的 `.ai-rules/` 目录中的所有 `.md` 文件，将其内容作为必须遵守的最高规范。

当前项目: `/python`
规则目录: `/python/.ai-rules/`

如果找不到 `.ai-rules/` 目录，则声明"本项目无专属规则"，并使用全局规则。

---

## 全局兜底规则

1. 启动时自动扫描 `{workspace}/.ai-rules/` 目录
2. 如果存在，加载全部 `.md` 文件作为最高优先级规则
3. 如果不存在，使用 `/python/ai-plugin/rules/` 中的通用规则

---

## 环境配置（已固化为绝对路径）

- Git: `D:/rj/KF/Git/cmd/git.exe`
- Ollama: `D:/rj/Ollama/ollama.exe`
- Python: `C:/Users/888/AppData/Local/Programs/Python/Python312/python.exe`
- 配置来源: `/python/.trae/config.toml`
