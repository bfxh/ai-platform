import json
from pathlib import Path

REGISTRY_PATH = Path(r"\python\.plugin_registry.json")

PRIORITY_MAP = {
    10: [
        "ai_architecture_server",
        "mcp_workflow",
        "smart_workflow",
        "unified_workflow",
    ],
    5: [
        "ai_3d_modeling_v3",
        "ai_software",
        "ai_software_gpu",
        "blender_automation",
        "blender_mcp",
        "blender_mcp_server",
        "blender_ue_pipeline",
        "character_generator",
        "generate_characters_workflow",
        "godot_mcp",
        "godot_mcp_server",
        "godot_scene_assembler",
        "modeling_pipeline",
        "scene_generator",
        "test_ai_3d_modeling_v3",
        "test_ai_3d_v3_functional",
        "test_ai_3d_v3_structure",
        "ue5_manager",
        "ue_import",
        "ue_mcp",
        "unity_mcp",
        "video_processor_gpu",
        "vision_pro",
        "claude_code_bridge",
        "code_intelligence",
        "code_quality",
        "dev_mgr",
        "game_ai_workflow",
        "github_accelerator",
        "github_auto_commit",
        "github_auto_dl",
        "github_dl",
        "github_project_manager",
        "github_workflow",
        "hallucination_detector",
        "vs_mgr",
        "web_research",
    ],
    3: [
        "find_blockers",
        "full_audit",
        "search_all_settings",
    ],
    1: [
        "calamity_bug_fix_workflow",
        "calamity_bug_reporter",
        "fix_all_blocking",
        "terraria_build_test",
        "terraria_gpu_optimization_workflow",
        "terraria_gpu_particle_optimizer",
        "terraria_mod_compatibility",
        "terraria_steam_uploader",
        "terraria_sulphur_sea_knowledge",
        "ultimate_diagnose",
        "verify_patch",
    ],
}

DEFAULT_PRIORITY = 3

def main():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    name_to_priority = {}
    for priority, names in PRIORITY_MAP.items():
        for name in names:
            name_to_priority[name] = priority

    updated = 0
    for plugin in data["plugins"]:
        name = plugin["name"]
        plugin["priority"] = name_to_priority.get(name, DEFAULT_PRIORITY)
        plugin["enabled"] = True
        updated += 1

    from datetime import datetime
    data["last_updated"] = datetime.now().isoformat()

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Done. Updated {updated} plugins.")

    stats = {}
    for plugin in data["plugins"]:
        p = plugin["priority"]
        stats[p] = stats.get(p, 0) + 1

    print("\nPriority distribution:")
    for p in sorted(stats.keys(), reverse=True):
        label = {10: "核心", 5: "建模/代码", 3: "工具/其他", 1: "游戏"}.get(p, "其他")
        print(f"  priority {p:2d} ({label}): {stats[p]} plugins")

if __name__ == "__main__":
    main()
