# Qoder Agent — 项目规则路由

本文件不再包含具体规则。项目专属规则在 `{workspace}/.ai-rules/` 下。

## First: Load Project Rules

Before any task, read all `.md` files in `{workspace}/.ai-rules/`.
These are the highest-priority rules for the current project.

Current workspace: `/python`
Rules directory: `/python/.ai-rules/`

If `.ai-rules/` doesn't exist, fall back to `/python/ai-plugin/rules/`.

## Execution Protocol

1. Load `.ai-rules/*.md` (project rules)
2. Read `/python/AGENTS.md` and `/python/ai_architecture.json`
3. Check local capabilities: Skill → MCP → CLL → Workflow → Agent → Plugin
4. Execute task
5. Record results

## Hardcoded Paths (not env-var-dependent)

- Git: `D:/rj/KF/Git/cmd/git.exe`
- Ollama: `D:/rj/Ollama/ollama.exe`
- Python: `C:/Users/888/AppData/Local/Programs/Python/Python312/python.exe`

## Core Principles

1. Quality over Speed
2. Local First — use existing capabilities before writing new code
3. Read code before proposing changes
4. No guessing paths — use Glob/Grep to verify
