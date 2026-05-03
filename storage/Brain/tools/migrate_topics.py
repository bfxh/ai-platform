import json
import os
import shutil
from datetime import datetime
from pathlib import Path

TOPICS_DIR = Path(r"\python\storage\Brain\topics")
INDEX_FILE = TOPICS_DIR / "_index.json"
MIGRATION_LOG = Path(r"\python\storage\Brain\tools\migration_log.json")

CATEGORY_RULES = [
    ("ai_models", ["AI", "模型", "qwen", "ollama", "deepseek", "stepfun", "LLM", "GPT", "claude"]),
    ("mcp_servers", ["MCP", "服务器", "server", "协调器", "TCP", "通信"]),
    ("game_dev", ["游戏", "Minecraft", "Unity", "Unreal", "Blender", "建模"]),
    ("system_ops", ["系统", "运维", "部署", "Docker", "配置", "安装", "环境"]),
    ("project_mgmt", ["项目", "管理", "架构", "规划", "任务", "GSTACK"]),
    ("troubleshooting", ["错误", "修复", "bug", "调试", "故障", "问题", "debug"]),
    ("coding_patterns", ["代码", "编程", "Python", "开发", "模式", "设计", "框架"]),
]

CATEGORY_DESCRIPTIONS = {
    "ai_models": "AI模型相关话题",
    "mcp_servers": "MCP服务器开发话题",
    "game_dev": "游戏开发相关话题",
    "system_ops": "系统运维与部署话题",
    "project_mgmt": "项目管理与架构话题",
    "coding_patterns": "代码开发与编程模式话题",
    "troubleshooting": "错误修复与调试话题",
    "uncategorized": "未分类话题",
}

EXCLUDE_FILES = {"_index.json"}
EXCLUDE_DIRS = {"ai_models", "mcp_servers", "game_dev", "system_ops", "project_mgmt", "coding_patterns", "troubleshooting", "uncategorized"}


def determine_category(tags):
    for category, keywords in CATEGORY_RULES:
        for tag in tags:
            tag_lower = tag.lower()
            for keyword in keywords:
                if keyword.lower() == tag_lower:
                    return category
    return "uncategorized"


def migrate():
    print("=" * 60)
    print("Brain Topics 分类迁移脚本 v1.0")
    print("=" * 60)

    if not INDEX_FILE.exists():
        print(f"错误: 找不到 _index.json: {INDEX_FILE}")
        return

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index_data = json.load(f)

    print(f"\n_index.json 中共有 {len(index_data)} 条记录")

    json_files = [
        f for f in TOPICS_DIR.iterdir()
        if f.is_file() and f.suffix == ".json" and f.name not in EXCLUDE_FILES
    ]
    print(f"topics/ 目录中共有 {len(json_files)} 个 JSON 文件（排除 _index.json）")

    category_counts = {cat: 0 for cat in CATEGORY_DESCRIPTIONS}
    migration_records = []
    tag_cloud = {}
    errors = []
    new_entries = []

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            tags = data.get("tags", [])
            if not isinstance(tags, list):
                tags = []

            for tag in tags:
                tag_cloud[tag] = tag_cloud.get(tag, 0) + 1

            category = determine_category(tags)
            category_counts[category] += 1

            dest_dir = TOPICS_DIR / category
            dest_dir.mkdir(exist_ok=True)
            dest_file = dest_dir / json_file.name

            shutil.move(str(json_file), str(dest_file))

            new_file_path = f"{category}/{json_file.name}"

            entry = {
                "id": data.get("id", json_file.stem),
                "title": data.get("title", ""),
                "tags": tags,
                "category": category,
                "file": new_file_path,
                "score": data.get("score", 5),
            }
            new_entries.append(entry)

            migration_records.append({
                "file": json_file.name,
                "from": "topics/",
                "to": new_file_path,
                "category": category,
                "tags": tags,
                "timestamp": datetime.now().isoformat(),
            })

        except Exception as e:
            errors.append({
                "file": json_file.name,
                "error": str(e),
            })
            print(f"  错误处理 {json_file.name}: {e}")

    new_index = {
        "version": "2.0",
        "updated_at": datetime.now().isoformat(),
        "categories": {},
        "tag_cloud": dict(sorted(tag_cloud.items(), key=lambda x: -x[1])),
        "total_entries": len(new_entries),
        "entries": sorted(new_entries, key=lambda x: x.get("score", 0), reverse=True),
    }

    for cat, desc in CATEGORY_DESCRIPTIONS.items():
        new_index["categories"][cat] = {
            "count": category_counts[cat],
            "description": desc,
        }

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(new_index, f, ensure_ascii=False, indent=2)

    log_data = {
        "migration_time": datetime.now().isoformat(),
        "total_migrated": len(migration_records),
        "total_errors": len(errors),
        "category_counts": category_counts,
        "records": migration_records,
        "errors": errors,
    }

    with open(MIGRATION_LOG, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print("迁移结果统计")
    print(f"{'=' * 60}")
    print(f"总迁移文件数: {len(migration_records)}")
    print(f"错误数: {len(errors)}")
    print()
    print("各分类文件数:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        desc = CATEGORY_DESCRIPTIONS[cat]
        print(f"  {cat:20s} ({desc}): {count}")
    print()
    print(f"新 _index.json 已生成: {INDEX_FILE}")
    print(f"迁移日志已保存: {MIGRATION_LOG}")

    remaining = [
        f for f in TOPICS_DIR.iterdir()
        if f.is_file() and f.suffix == ".json" and f.name not in EXCLUDE_FILES
    ]
    print(f"\n迁移后 topics/ 根目录剩余 JSON 文件: {len(remaining)}")
    if remaining:
        for f in remaining:
            print(f"  - {f.name}")

    total_in_subdirs = 0
    for cat in CATEGORY_DESCRIPTIONS:
        cat_dir = TOPICS_DIR / cat
        if cat_dir.exists():
            count = len(list(cat_dir.glob("*.json")))
            total_in_subdirs += count

    print(f"子目录中 JSON 文件总数: {total_in_subdirs}")
    print(f"\n迁移前总数: {len(json_files)}")
    print(f"迁移后总数: {total_in_subdirs}")
    if len(json_files) == total_in_subdirs:
        print("✓ 文件数量一致，迁移成功！")
    else:
        print("✗ 文件数量不一致，请检查！")


if __name__ == "__main__":
    migrate()
