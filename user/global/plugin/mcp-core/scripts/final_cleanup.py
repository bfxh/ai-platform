import os, shutil, traceback

SRC = r"/python"
DEST_BACKUP = r"F:\储存\备份\AI移出文件"
DEST_GJ = r"D:\\rj\GJ"
DEST_GJ_DOCS = r"D:\\rj\GJ\docs"
DEST_WORKSPACE = r"%USERPROFILE%\WorkBuddy\20260410084126\docs"

os.makedirs(DEST_BACKUP, exist_ok=True)
os.makedirs(DEST_GJ, exist_ok=True)
os.makedirs(DEST_GJ_DOCS, exist_ok=True)
os.makedirs(DEST_WORKSPACE, exist_ok=True)

def safe_copytree(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

def safe_move(src, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)
    fname = os.path.basename(src)
    dst = os.path.join(dst_dir, fname)
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"  -> {dst}")

def safe_rmtree(path):
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f"  [DEL] {path}")

moved = 0
errors = 0

# 游戏项目目录 -> F:\储存\备份\AI移出文件
game_dirs = [
    ".godot", "BeyondUE5", "GodotBlenderBridge_Improved",
    "CppGameProject", "FixedProject", "RTXNTC", "UE_Automation",
    "AutoFixScripts", "Plugins", "Projects", "scenes",
    "addons", "backups", "ironclaw", "ironclaw_source",
    "warframe-progress-tool",
    "CalamityModArchitecture", "CalamityMod_GPU_Optimization",
    "CalamityMod_Optimization", "GodotMCP",
]
# 这些目录有Unicode编码问题，稍后处理
unicode_dirs = ["我即是虫群v2.0", "鎴戝嵆鏄嶨缇歩2.0"]
non_ai_dirs = game_dirs + unicode_dirs + [
    "Outputs", "blender", "browser_prefs_20260313_130337",
    "cmake-3.31.0", "docs", "eIsland", "exo-cluster",
    "github_projects", "github_search_logs", "lightpanda-browser",
    "logs", "mcp_profiles", "models", "pua", "pua-main",
    "qiushi-skill", "reports", "scripts", "shared_core",
    "skills-collection", "skills-collection-2", "test_github",
    "Memory",
    ".stepclaw", ".trae", ".vscode", ".pytest_cache",
]

print("=== 移动非AI目录 ===")
for d in non_ai_dirs:
    src_path = os.path.join(SRC, d)
    if os.path.exists(src_path) and os.path.isdir(src_path):
        try:
            safe_copytree(src_path, os.path.join(DEST_BACKUP, d))
            safe_rmtree(src_path)
            moved += 1
        except Exception as e:
            print(f"  [跳过] {d}: {e}")
            errors += 1

# 非AI文件
print("\n=== 移动非AI文件 ===")
to_gj = [
    "MCP管理器.bat", "install-cherry-studio-mcp.bat",
    "create_shortcut.bat", "create_shortcut.ps1",
    "start_all_skills.bat", "start_all_skills.py",
    "optimize_resources.ps1",
    "search_everything.ps1", "search_github_desktop_lang.ps1",
    "search_godot.ps1",
    "test_github_search.py", "test_network.py",
    "temp_enable_plugin.py", "temp_get_info.py", "temp_verify_status.py",
    "create_dirs.py", "index.py",
    "token_optimizer.py", "workflow_automation.py", "workflow_runner.py",
    "task_executor.py", "smart_skill_caller.py", "smart_skill_manager.py",
    "advanced_skill_caller.py", "mcp_manager.py", "mcp_server.py",
    "chinese_config.py", "enhanced_import_system.py",
    "context.json", "memo.json", "quick.json", "registry.json",
    "version.json", "user_config.md",
    "pytest.ini", "background_process_config.json",
    "aria2_plugin_config.json", "claude-mcp-config.json",
    "langfuse-mcp-config.json", "langfuse-mcp-workflow.md",
    "mcp-config.json", "mcp-servers-collection.json",
    "mcp_workflow_config.json", "all-mcp-servers-list.md",
    "backup_stepfun_chats.py",
]
to_workdocs = [
    "Blender导出目录结构.md",
    "插件管理系统使用说明.md", "插件自动化部署完成报告.md",
    "插件适配报告.md",
    "测试报告.md", "测试报告_最终版.md",
    "深度分析报告_v3.0.md",
    "记录本.md",
]
to_gj_docs = [
    "开发软件下载链接.html",
    "快速连接华为电脑.md",
    "全自动无人值守方案.md", "安装完成说明.md",
    "高速双网传输方案.md",
]
to_backup = [
    "terraria_workflows.py", "terraria_workflows_updated.py",
    "backup_terraria_configs.py",
    "全自动传输_方案A_共享文件夹.bat",
    "全自动传输_方案B_Python.bat",
    "搜索并启动Godot.bat", "自动安装并启动.bat",
]

for fname in to_gj:
    safe_move(os.path.join(SRC, fname), DEST_GJ)
for fname in to_workdocs:
    safe_move(os.path.join(SRC, fname), DEST_WORKSPACE)
for fname in to_gj_docs:
    safe_move(os.path.join(SRC, fname), DEST_GJ_DOCS)
for fname in to_backup:
    safe_move(os.path.join(SRC, fname), DEST_BACKUP)

# 清理 .git（保留，因为有些AI项目可能需要）
# .git 保留

# 最终状态
remaining_files = [f for f in os.listdir(SRC) if os.path.isfile(os.path.join(SRC, f))]
remaining_dirs = [d for d in os.listdir(SRC) if os.path.isdir(os.path.join(SRC, d))]
remaining_dirs_ai = [d for d in remaining_dirs]

result = []
result.append(f"Files: {len(remaining_files)}")
result.append(f"Dirs: {len(remaining_dirs)}")
result.append("Dirs:")
for d in sorted(remaining_dirs):
    result.append(d)
result.append("Files:")
for f in sorted(remaining_files):
    result.append(f)
with open(r"/python\MCP_Core\scripts\cleanup_result.txt", "w", encoding="utf-8") as fw:
    fw.write("\n".join(result))
print("Done")
