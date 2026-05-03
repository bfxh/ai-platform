#!/usr/bin/env python3
"""
\python 目录清理迁移脚本
把非AI文件从 \python 移到正确位置
"""
import os
import shutil
import glob

SOURCE = r"/python"
MOVES = {
    r"%SOFTWARE_DIR%\GJ": [
        "clone_*.bat", "clone_*.ps1",
        "一键*.bat", "一键*.ps1", "一键*.py",
        "auto_*.ps1", "auto_*.py", "auto_decompile*.py",
        "download_*.py", "download_*.bat", "download_*.ps1",
        "batch_*.py", "batch_*.bat", "batch_*.ps1",
        "comprehensive_*.bat", "comprehensive_*.ps1",
        "complete_*.bat", "complete_*.ps1",
        "diagnose*.ps1", "diagnose*.py",
        "修复*.ps1", "check_*.bat", "check_*.py",
        "clean_*.py", "clean_*.bat",
        "搜索并测试.bat", "Everything搜索*.bat",
        "快速连接*.bat", "快速启动*.bat",
        "发送到_*.bat",
        "disable_*.bat",
        "快速*.bat", "启动*.bat",
        "设置*.bat", "创建*.bat",
        "admin_*.bat", "admin_*.ps1",
        "auto_plugin_manager*.gd", "auto_plugin_manager*.gd.uid",
        "ai_behavior_system.gd", "ai_behavior_system.gd.uid",
        "animation_sync_manager.gd", "animation_sync_manager.gd.uid",
        "data_analytics_system.gd", "data_analytics_system.gd.uid",
        "beyond_ue5*.gd", "beyond_ue5*.gd.uid",
        "apply_schematic_fix.py",
        "batch_download_github*.ps1", "batch_download_github*.bat",
        "batch_download_github.py",
        "download_browser_projects.ps1",
        "download_single_project.ps1",
        "download_decompilers.py",
        "download_godot_jolt.py",
        "download_github*.py",
        "download_plugins*.py", "download_plugins*.ps1",
        "automate_plugins.py",
        "clone_browser*.bat",
        "clone_lightpanda*.bat",
        "clone_remaining*.bat",
        "clone_correct*.bat",
        "batch_github_download.ps1",
        "diagnose_schematic.py",
        "debug_export.py", "debug_ue5_pipeline.py",
        "blender_ue5_to_godot.py",
        "clone_godot_jolt.py",
        "check_fbx_params.py",
        "check_pytorch.py",
        "analyze_dependencies.py",
        "batch_decompile_mods.py",
        "calamity_bug_reporter.py",
        "copy_resources.ps1", "copy_resources.py",
        "create_model_dirs.bat",
        "delete_junk.py",
        "clean_download.py",
        "clean_memory.py",
        "cleanup_mcp_skills.py",
        "cleanup_stepfun.py",
        "debug_objects.txt", "debug_result.txt",
        "disable_idm_extensions.bat",
        "complete_explorer_fix.bat",
        "browser-use-main.zip",
        "cmake-3.31.0-windows-x86_64.msi",
        "cmake-3.31.0-windows-x86_64.zip",
        "admin_opt_done.flag",
        "移动文件夹.ps1",
        "整理下载文件夹.bat",
        "执行状态.md",
        "complete-mcp-servers-guide.md",
        "download-automation-workflow.md",
        "EXo_Cluster_Setup_Guide.md",
    ],
    r"%USERPROFILE%\WorkBuddy\20260410084126\docs": [
        "泰拉瑞亚*.md",
        "泰拉瑞亚*.ps1",
        "泰拉瑞亚*.bat",
        "泰拉瑞亚*.py",
        "泰拉瑞亚MCP*.md",
        "CalamityBugReporterGuide.md",
        "EncryptedSchematic*.md",
        "CalamityGlobalNPC_edited.cs",
        "CalamityGlobalNPC_fixed.cs",
        "CalamityNetcode_fixed.cs",
        "AquaticScourgeHead_fixed.cs",
        "EncryptedSchematicBugFix.md",
    ],
    r"F:\储存\备份\AI移出文件": [
        "*.gd", "*.gd.uid",
        "*.cs",
        "新建游戏项目",
        "godot",
    ],
    r"%SOFTWARE_DIR%\GJ\docs": [
        "开发软件下载链接.html",
        "浏览器插件安装说明.md",
        "浏览器项目克隆和配置指南.md",
        "浏览器项目配置说明.md",
        "浏览器项目下载说明.md",
        "通知系统使用说明.md",
        "使用指南.md",
        "替代插件推荐.md",
        "完整方案使用指南.md",
        "完整文档.md",
        "自动化方案总结.md",
        "CONTINUOUS_IMPROVEMENT_GUIDE.md",
        "COMMUNITY_FEEDBACK.md",
        "BEYOND_UNREAL5.md",
        "BETA_RELEASE_GUIDE.md",
        "CHANGELOG.md",
        "DEEP_ANALYSIS_REPORT.md",
        "DEEP_ANALYSIS_REPORT_v3.md",
        "ANALYSIS_REPORT.md",
    ],
}

def move_files():
    total_moved = 0
    for dest, patterns in MOVES.items():
        os.makedirs(dest, exist_ok=True)
        for pattern in patterns:
            # 处理目录
            if "*" not in pattern and not pattern.endswith(".md") and not pattern.endswith(".py") and not pattern.endswith(".bat") and not pattern.endswith(".ps1") and not pattern.endswith(".gd") and not pattern.endswith(".cs") and not pattern.endswith(".gd.uid"):
                dir_path = os.path.join(SOURCE, pattern)
                if os.path.isdir(dir_path):
                    dest_sub = os.path.join(dest, pattern)
                    if not os.path.exists(dest_sub):
                        shutil.copytree(dir_path, dest_sub)
                        print(f"[目录] {dir_path} -> {dest_sub}")
                        total_moved += 1
                continue

            # 通配符文件匹配
            pattern_path = os.path.join(SOURCE, pattern)
            try:
                matches = glob.glob(pattern_path)
            except Exception:
                continue
            for src in matches:
                if os.path.isfile(src):
                    fname = os.path.basename(src)
                    dest_file = os.path.join(dest, fname)
                    try:
                        shutil.move(src, dest_file)
                        print(f"[文件] {src} -> {dest_file}")
                        total_moved += 1
                    except Exception as e:
                        print(f"[跳过] {src}: {e}")
    print(f"\n共迁移 {total_moved} 项")
    return total_moved

if __name__ == "__main__":
    n = move_files()
    print("清理完成")
