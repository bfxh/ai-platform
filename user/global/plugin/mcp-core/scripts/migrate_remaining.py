#!/usr/bin/env python3
"""/python 残留文件深度清理"""
import os, shutil, glob

SOURCE = r"/python"

def move(src, dest):
    os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else dest, exist_ok=True)
    if os.path.exists(src) and src != dest:
        shutil.move(src, dest)
        print(f"  -> {dest}")

# === Godot 场景和项目文件 -> F:\储存\备份\Godot相关
for p in [
    "project.godot", "plugin.cfg", "plugin.py", "plugin_loader.cfg",
    "icon.svg", "test_asset.png",
    "fragment.tscn", "fragment_fixed.tscn", "fragment_fixed_simple.tscn",
    "test_basic.tscn", "test_physics.tscn", "test_physics_fixed.tscn",
    "test_simple.tscn", "test_minimal.tscn",
    "*.tscn",
]:
    for f in glob.glob(os.path.join(SOURCE, p)):
        move(f, os.path.join(r"F:\储存\备份\Godot相关", os.path.basename(f)))

# === 下载缓存 -> %SOFTWARE_DIR%\GJ\download_cache
for p in ["browser-use-main.zip", "cmake-3.31.0-windows-x86_64.msi",
          "cmake-3.31.0-windows-x86_64.zip", "pua.zip",
          "*.zip", "*.msi"]:
    for f in glob.glob(os.path.join(SOURCE, p)):
        dest = os.path.join(r"D:\\rj\GJ\download_cache", os.path.basename(f))
        move(f, dest)

# === 临时脚本 -> %SOFTWARE_DIR%\GJ\
scripts = [
    "diag2.ps1", "diag3.ps1", "final_explorer_fix.bat", "fix_explorer.bat",
    "fix_explorer_on_startup.bat", "open_explorer.bat", "quick_start.bat",
    "scan_network.bat", "find_and_transfer.bat",
    "test_launcher.bat", "test_github.log", "test_github_clone.ps1",
    "test_github_api.ps1", "test_github_api_to_file.ps1",
    "test_git_installation.ps1", "simple_github_download.ps1",
    "simple_github_download_en.ps1", "install-all-32-mcp-servers.bat",
    "install-all-80-mcp-servers.bat", "install-all-mcp-servers.bat",
    "install_cherry_studio_mcp.bat", "test_blender_mcp.bat",
    "test_blender_ue.bat", "test_ai_3d_modeling.bat",
    "test_ai_software.bat", "test_download_manager.bat",
    "test_ue5_manager.bat", "test_video_processor.bat",
    "test_vscode_ai.bat", "test_accel_network.bat",
    "test_network.ps1", "test_simple.ps1", "test_project.ps1",
    "test_basic.py", "test_cpp_project.ps1", "test_skills.py",
    "test_translate.py", "test_translate_zh.py",
    "simple_test.ps1", "test_physics_fixed.py",
    "install_vs_simple.ps1", "install_visual_studio.ps1",
    "install_rtx_ntc_english.ps1", "install_browser_plugins.ps1",
    "install_browser_plugins_english.ps1", "install_browser_plugins_final.ps1",
    "install_browser_plugins_fixed.ps1", "login_guard.ps1",
    "login_persist_runner.ps1", "login_persist_setup.ps1",
    "login_persist_v2.ps1", "optimize_startup.ps1",
    "run_admin.ps1", "fix_godot_project.ps1",
    "fix_godot_project_comprehensive.ps1",
    "fix_godot_project_v2.ps1", "fix_godot_project_v3.ps1",
    "fix_quark_prefs.ps1", "fix_all_godot_bugs.ps1",
    "fix_all_godot_bugs.py", "verify.ps1",
    "system_check.ps1", "system_diag.ps1",
    "fix_project_godot.bat", "fix_project_godot_simple.bat",
    "start_godot_project.bat", "start_godot_simple.bat",
    "start_project.bat", "test_launcher.bat",
    "init-workflow.bat", "init-workflow.sh",
    "migrate_to_d.py", "organizer.py",
    "extract_terraria_resources.py",
    "fix_terraria_mods.py", "fix_sulphur_sea_bug.py",
    "fix_sulphur_sea_bug_cmd.py", "fix_network_sync.py",
    "fix_godot_project.py", "fix_all_godot_bugs.py",
    "gen_godot_scene.py", "test_fragment_system.py",
    "verify_setup.py", "scan_project.ps1",
    "test_godot_project.py", "mcp_workflow.ps1",
    "mcp_workflow_simple.ps1", "mcp_workflow_test.ps1",
    "mcp_integration.ps1", "mcp_local_integration.ps1",
    "mcp-aria2-server.js", "mcp-browser-integration.ps1",
    "mcp-file-organizer.ps1", "run_blender_mcp.ps1",
    "run_blender_mcp_workflow.ps1", "run_ue5_pipeline.ps1",
    "run_all_tests.bat", "run_tests.bat", "run_tests.ps1",
    "run_optimization.bat", "setup_auto_import.ps1",
    "setup_auto_import.py", "setup_auto_sync.bat",
    "setup_registry.bat", "login_persist_runner.ps1",
    "start_trae_with_agent.ps1", "start_trae_with_agent.bat",
    "login_persist_setup.ps1",
    "create_project.bat", "start_project.bat",
    "start_godot.bat", "start_godot.ps1",
    "start_godot_english.ps1", "quick_config.ps1",
    "install_plugins.bat", "test_trae_agent.txt",
    "trae_agent_test.txt",
    "automation_test.ps1", "自动化测试.ps1", "完整自动化测试.ps1",
    "自动化测试.ps1",
    "fix_sulphur_sea_bug_cmd.py",
    "test_physics_fixed.py",
]
for s in scripts:
    for f in glob.glob(os.path.join(SOURCE, s)):
        move(f, os.path.join(r"D:\\rj\GJ", os.path.basename(f)))

# === Terraria/游戏相关文档 -> 工作区 docs
for p in [
    "CalamityMod_BugReport_EncryptedSchematics.md",
    "SulphurSeaKnowledgeBugAnalysis.md",
    "SulphurSeaKnowledgeBugFix.md",
    "SulphurSeaKnowledgeSolution.md",
    "TerrariaNetworkOptimization.md",
    "GodotBlenderBridge_Architecture.md",
    "GodotBlenderBridge_Improvement_Report.md",
    "GodotBlenderBridge_Integration_Examples.md",
    "STEAM_PLUGIN_SYSTEM.md",
    "GPU_UPGRADE_COMPLETE.md",
    "GPU_MEMORY_STRATEGY.md",
    "PYTORCH_GPU_GUIDE.md",
]:
    f = os.path.join(SOURCE, p)
    if os.path.exists(f):
        move(f, os.path.join(r"%USERPROFILE%\WorkBuddy\20260410084126\docs", p))

# === UE5 相关文档 -> F:\储存\UE5
for p in [
    "UE_检查和修复指南.md",
    "UE_项目检查报告.md",
    "GPU_MEMORY_STRATEGYGY.md",
]:
    f = os.path.join(SOURCE, p)
    if os.path.exists(f):
        move(f, os.path.join(r"F:\储存\备份\AI移出文件", p))

# === 日志和临时文件 -> 删除
for p in ["*.log", "*.txt", "*.bak", "*.flag"]:
    for f in glob.glob(os.path.join(SOURCE, p)):
        try:
            os.remove(f)
            print(f"  [删除] {f}")
        except Exception as e:
            print(f"  [跳过删除] {f}: {e}")

# === 通用工具 py -> %SOFTWARE_DIR%\GJ
tools = [
    "high_speed_receive.py", "high_speed_receive_v2.py",
    "high_speed_transfer.py", "high_speed_transfer_v2.py",
    "one_click_automation.py", "publish_to_github.py",
    "generate_github_issue.py", "generate_issue_simple.py",
    "github_issue_content.md", "github_issue_sulphur_sea.md",
    "install_all_plugins.py", "install_rtx_ntc_plugin_fixed.py",
    "restore_terraria_config.py", "register_startup.py",
    "register_task.py", "send_notification.py",
    "notify_complete.py", "notification_service.py",
    "optimize_resources.py", "start_high_speed_receive.bat",
    "start_high_speed_send.bat", "start_receive_now.bat",
    "test_translate.py",
    "batch_download_github*.ps1", "batch_download_github*.bat",
    "test_github_download.log", "test_github_download_simple.log",
    "github_download.log", "github_download_helper.ps1",
    "github_single_download.log", "github_batch_download.log",
    "download_github_simple.ps1",
    "batch_decompile_mods.py",
    "blender_batch_test.log",
    "godot_log.txt",
    "github_download.log",
    "ue5_pipeline_result.txt",
    "blender_ue5_pipeline.log",
    "test_translate_zh.py",
    "test_physics_fixed.py",
    "download_github.py",
    "download_github_api.py",
    "fix_network_sync.py",
    "gen_godot_scene.py",
]
for t in tools:
    for f in glob.glob(os.path.join(SOURCE, t)):
        fname = os.path.basename(f)
        dest = os.path.join(r"D:\\rj\GJ", fname)
        move(f, dest)

# === AI项目下载脚本 -> %SOFTWARE_DIR%\GJ
for f in glob.glob(os.path.join(SOURCE, "AI-Projects-Download.ps1")):
    move(f, os.path.join(r"D:\\rj\GJ", "AI-Projects-Download.ps1"))

# === 清理 admin_opt_done.flag
f = os.path.join(SOURCE, "admin_opt_done.flag")
if os.path.exists(f):
    os.remove(f)

print("\n深度清理完成")
