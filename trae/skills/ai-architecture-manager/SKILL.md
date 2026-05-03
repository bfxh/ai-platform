---
name: "ai-architecture-manager"
description: "Automatically manages \python architecture on startup. Checks GSTACK, MCP categories, CC cache, Skills system, and runs daily automation tasks. Invoked automatically when workspace loads or user mentions \python architecture."
---

# AI Architecture Manager

## Auto-Trigger Conditions

This skill auto-triggers when:
- Workspace loads (startup)
- User mentions "\python", "architecture", "GSTACK", "MCP", "CC cache"
- Before any file operation in \python directory

## Startup Sequence (Auto-Execute)

### Step 1: GSTACK Check
```
IF GSTACK unavailable:
  - Report to user
  - Switch to fallback_mode
  - Continue with limited functionality
```

### Step 2: Configuration Validation
Check these files exist:
- `\python\ai_architecture.json` (v4.2)
- `\python\index.json`
- `\python\MCP\mcp-config.json` (v2.0)
- `\python\.gstack_protected`

### Step 3: MCP Directory Scan
```
JM:  target=30, actual=?, status=OK/WARNING
BC:  target=46, actual=?, status=OK/WARNING  
Tools: target=32, actual=?, status=OK/WARNING
```

### Step 4: CC Cache Check
Verify directories:
- `\python\CC\1_Raw\`
- `\python\CC\2_Old\`
- `\python\CC\3_Unused\`
- All INDEX.md files present

### Step 5: Skills System Check
- `\python\MCP_Core\skills\` exists
- `skill_doctor` available
- `cc_cleanup_advisor` available

## Auto-Actions

### When User Says "Check" or "检查"
Auto-run full architecture check and report results.

### When User Says "Cleanup" or "整理"
Auto-scan \python root for scattered files and move to CC/3_Unused/.

### When User Says "Backup" or "备份"
Auto-run `\python\scripts\daily_backup.py`.

### When User Says "Update" or "更新"
Auto-run `\python\scripts\daily_github_update.py`.

## Architecture Status Report Format

```
✅ GSTACK v3.1 Ready
✅ MCP: JM(30) BC(46) Tools(32)
✅ Skills: 29 available
✅ CC Cache: 3 categories
✅ CLL Projects: 44 projects
✅ Automation: 2 scheduled tasks
⚠️  Issues: [list if any]
```

## Protection Rules (Auto-Enforced)

1. Before modifying any architecture file:
   - Auto-backup to `CC/2_Old/`
   - Log the change
   
2. Before moving MCP files:
   - Verify category (JM/BC/Tools)
   - Update mcp-config.json
   - Update INDEX.md

3. Before deleting anything:
   - Move to CC/3_Unused/ first
   - Wait 30 days before actual delete
