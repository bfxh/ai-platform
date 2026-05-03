#!/usr/bin/env python
"""\python 系统优化修复脚本 v1.0

执行以下 5 项优化:
  1. 创建缺失的 context.json (从 ai_architecture.json 提取摘要)
  2. 更新 ai_architecture.json 中的 last_check 时间戳
  3. 在 pipeline_engine.py 中注入 last_check 自动更新逻辑
  4. 拆分 requirements.txt 为生产核心 + 开发依赖
  5. 验证 Brain Topics 索引与文件一致性

用法:
  python scripts/fix/system_optimize.py          # 全部执行
  python scripts/fix/system_optimize.py --dry-run # 仅预览不修改
  python scripts/fix/system_optimize.py --only 1  # 仅执行第1项
  python scripts/fix/system_optimize.py --only 3 5 # 仅执行第3和5项
"""

import json
import sys
import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent.parent  # \python

DRY_RUN = False
ONLY_ITEMS = []


def log(msg: str, level: str = "INFO"):
    prefix = {"INFO": "  ", "OK": "✅", "WARN": "⚠️", "ERR": "❌", "DRY": "🔍"}
    tag = prefix.get(level, "  ")
    print(f"{tag} {msg}")


def backup_file(filepath: Path) -> Optional[Path]:
    if not filepath.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = filepath.parent / f"{filepath.stem}_backup_{ts}{filepath.suffix}"
    shutil.copy2(filepath, backup)
    log(f"备份: {filepath.name} -> {backup.name}", "OK")
    return backup


def safe_write(filepath: Path, content: str):
    if DRY_RUN:
        log(f"[DRY] 将写入: {filepath}", "DRY")
        log(f"[DRY] 内容预览 (前200字): {content[:200]}...", "DRY")
        return
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    log(f"已写入: {filepath}", "OK")


def safe_write_json(filepath: Path, data: dict):
    content = json.dumps(data, ensure_ascii=False, indent=2)
    safe_write(filepath, content)


# ──────────────────────────────────────────────────────────
# Fix 1: 创建 context.json
# ──────────────────────────────────────────────────────────
def fix1_create_context_json():
    log("=" * 50)
    log("Fix 1: 创建缺失的 context.json")
    log("=" * 50)

    ctx_path = ROOT / "user" / "context.json"
    if ctx_path.exists():
        log(f"context.json 已存在: {ctx_path}", "WARN")
        return

    arch_path = ROOT / "ai_architecture.json"
    if not arch_path.exists():
        log("ai_architecture.json 不存在，无法提取摘要", "ERR")
        return

    arch = json.loads(arch_path.read_text(encoding="utf-8"))

    mcp_summary = {}
    for cat_key, cat_val in arch.get("mcp", {}).get("categories", {}).items():
        mcp_summary[cat_key] = {
            "name": cat_val.get("name", ""),
            "file_count": cat_val.get("file_count", 0),
            "keywords": cat_val.get("keywords", [])[:5],
        }

    skills_list = arch.get("skills", {}).get("available_skills", [])

    cll_cats = {}
    for cat_key, cat_val in arch.get("cll_projects", {}).get("categories", {}).items():
        cll_cats[cat_key] = {
            "name": cat_val.get("name", ""),
            "count": cat_val.get("count", 0),
        }

    context = {
        "version": "1.0",
        "generated": datetime.now().isoformat(),
        "source": "ai_architecture.json + AGENTS.md",
        "project": {
            "name": "/python 智能自动工作平台",
            "architecture_version": arch.get("version", "5.0"),
            "last_updated": arch.get("updated", ""),
        },
        "runtime": {
            "ide": "TRAE 1.107",
            "python": "3.10",
            "node": "18",
            "ollama": "0.21",
            "models": ["qwen2.5-coder:7b", "deepseek-coder:6.7b"],
        },
        "mcp_summary": mcp_summary,
        "skills_count": len(skills_list),
        "skills_sample": skills_list[:10],
        "cll_project_count": arch.get("cll_projects", {}).get("project_count", 0),
        "cll_categories": cll_cats,
        "pipeline_version": arch.get("pipeline", {}).get("version", "6.0"),
        "directories": {
            k: v for k, v in arch.get("directories", {}).items()
            if Path(v).exists()
        },
        "last_check": arch.get("last_check", ""),
        "startup_checklist": arch.get("startup_checklist", []),
    }

    safe_write_json(ctx_path, context)
    log(f"context.json 已创建，包含 {len(context)} 个顶层字段", "OK")


# ──────────────────────────────────────────────────────────
# Fix 3: 更新 last_check + 注入自动更新逻辑
# ──────────────────────────────────────────────────────────
def fix3_update_last_check():
    log("=" * 50)
    log("Fix 3: 更新 last_check 并注入自动更新逻辑")
    log("=" * 50)

    arch_path = ROOT / "ai_architecture.json"
    if not arch_path.exists():
        log("ai_architecture.json 不存在", "ERR")
        return

    backup_file(arch_path)

    arch = json.loads(arch_path.read_text(encoding="utf-8"))
    old_check = arch.get("last_check", "unknown")
    new_check = datetime.now().isoformat()
    arch["last_check"] = new_check

    if not DRY_RUN:
        arch_path.write_text(json.dumps(arch, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"last_check: {old_check} -> {new_check}", "OK")
    else:
        log(f"[DRY] last_check: {old_check} -> {new_check}", "DRY")

    pipeline_path = ROOT / "core" / "pipeline_engine.py"
    if not pipeline_path.exists():
        log("pipeline_engine.py 不存在，跳过注入", "WARN")
        return

    content = pipeline_path.read_text(encoding="utf-8")

    auto_update_code = '''
    def _auto_update_last_check(self):
        """每次 Pipeline 启动时自动更新 ai_architecture.json 的 last_check"""
        arch_path = ROOT / "ai_architecture.json"
        if not arch_path.exists():
            return
        try:
            arch = json.loads(arch_path.read_text(encoding="utf-8"))
            arch["last_check"] = datetime.now().isoformat()
            arch_path.write_text(json.dumps(arch, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
'''

    if "_auto_update_last_check" in content:
        log("pipeline_engine.py 已包含 _auto_update_last_check，跳过注入", "WARN")
    else:
        backup_file(pipeline_path)

        insert_after = "self._register_default_handlers()"
        if insert_after in content:
            new_content = content.replace(
                insert_after,
                insert_after + "\n\n        self._auto_update_last_check()"
            )
            new_content = new_content.replace(
                "    def _register_default_handlers(self):",
                auto_update_code + "\n    def _register_default_handlers(self):"
            )
            if not DRY_RUN:
                pipeline_path.write_text(new_content, encoding="utf-8")
                log("已注入 _auto_update_last_check() 到 Pipeline.__init__", "OK")
            else:
                log("[DRY] 将注入 _auto_update_last_check() 到 Pipeline.__init__", "DRY")
        else:
            log("未找到注入点 _register_default_handlers()，跳过", "WARN")


# ──────────────────────────────────────────────────────────
# Fix 4: 拆分 requirements.txt
# ──────────────────────────────────────────────────────────
def fix4_split_requirements():
    log("=" * 50)
    log("Fix 4: 拆分 requirements.txt")
    log("=" * 50)

    req_path = ROOT / "requirements.txt"
    if not req_path.exists():
        log("requirements.txt 不存在", "ERR")
        return

    lines = req_path.read_text(encoding="utf-8").splitlines()

    PROD_PACKAGES = {
        "torch", "transformers", "ray", "vllm", "fastmcp", "mcp",
        "sqlalchemy", "deepspeed", "datasets", "pillow", "huggingface_hub",
        "peft", "redis", "accelerate", "httpx", "pyarrow", "yaml",
        "openai", "safetensors", "dotenv", "sentencepiece", "trl",
        "bitsandbytes", "diffusers", "flask_restx", "boto3", "grpc",
        "packaging", "typing_extensions", "loguru", "regex",
        "pydantic", "requests", "aiohttp", "websockets", "starlette",
        "werkzeug", "flask", "onnx", "sklearn", "scikit-learn",
        "numpy", "pandas", "matplotlib", "tqdm", "click", "rich",
        "jinja2", "markupsafe", "certifi", "urllib3", "charset-normalizer",
        "idna", "protobuf", "google", "optax", "jax", "triton",
        "torchvision", "evaluate", "tokenizers", "pymilvus",
        "llama_index", "colossalai", "paddle", "paddlenlp",
        "megatron", "composer", "fairscale", "axolotl",
        "trlx", "flash_attn", "flashinfer", "transformer_engine",
    }

    DEV_PACKAGES = {
        "pytest", "parameterized", "unittest", "coverage", "black",
        "flake8", "mypy", "isort", "autopep8", "pylint", "tox",
        "sphinx", "nbsphinx", "jupyter", "ipython", "notebook",
    }

    TEST_INTERNAL = {
        "test_", "tests", "testing_utils", "test_configuration_common",
        "test_modeling_common", "test_pipeline_mixin", "test_tokenization_common",
        "test_image_processing_common", "test_modeling_tf_common",
    }

    INTERNAL_MODULES = {
        "metadata", "utils", "models", "core", "dataclasses", "services",
        "common", "base", "activations", "controllers", "extensions",
        "image_utils", "processing_utils", "generation", "auto", "libs",
        "pipelines", "config", "deprecated", "integrations", "pytorch_utils",
        "tokenization_utils_base", "tokenization_utils", "cache_utils",
        "image_processing_utils", "modeling_layers", "modeling_utils",
        "configuration_utils", "modeling_outputs", "file_utils",
        "masking_utils", "modeling_rope_utils", "providers",
        "modeling_tf_utils", "tools", "agent", "plugin", "scripts",
        "ci", "extras", "model", "constants", "transport",
        "activations_tf", "unit", "interfaces", "workflow",
        "src", "cli", "libs", "mindsdb_sql_parser",
        "modeling_attn_mask_utils", "modeling_flash_attention_utils",
        "modeling_tf_outputs", "image_processing_backends",
        "image_transforms", "tokenization_utils_fast",
        "ray_release", "code_review_graph", "tf_utils",
        "pytorch_utils", "__about__",
    }

    version_only = re.compile(r'^>=?\d+\.\d+\.?\d*$')

    prod_lines = []
    dev_lines = []
    skipped_lines = []
    skipped_internal = 0
    skipped_version = 0

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        pkg_name = re.split(r'[><=!~\s#]', stripped)[0].strip().lower()

        if version_only.match(stripped) or not pkg_name:
            skipped_version += 1
            continue

        if pkg_name in INTERNAL_MODULES or any(stripped.startswith(t) for t in TEST_INTERNAL):
            skipped_internal += 1
            continue

        if pkg_name in DEV_PACKAGES:
            dev_lines.append(stripped)
        elif pkg_name in PROD_PACKAGES:
            prod_lines.append(stripped)
        else:
            use_count_match = re.search(r'#\s*(\d+)\s*uses', stripped)
            use_count = int(use_count_match.group(1)) if use_count_match else 0
            if use_count >= 500:
                prod_lines.append(stripped)
            elif use_count >= 100:
                dev_lines.append(stripped)
            else:
                skipped_lines.append(stripped)

    header = f"# Auto-split by system_optimize.py at {datetime.now().isoformat()}\n"
    header += "# Original: requirements.txt (8425 lines)\n\n"

    prod_content = header + "# Production core dependencies\n\n"
    for line in sorted(set(prod_lines)):
        clean = re.sub(r'\s*#\s*\d+\s*uses$', '', line)
        prod_content += clean + "\n"

    dev_content = header + "# Development & testing dependencies\n# Install: pip install -r requirements-dev.txt\n\n"
    for line in sorted(set(dev_lines)):
        clean = re.sub(r'\s*#\s*\d+\s*uses$', '', line)
        dev_content += clean + "\n"

    log(f"生产依赖: {len(set(prod_lines))} 个包", "INFO")
    log(f"开发依赖: {len(set(dev_lines))} 个包", "INFO")
    log(f"跳过内部模块: {skipped_internal} 个", "INFO")
    log(f"跳过纯版本行: {skipped_version} 个", "INFO")
    log(f"跳过低频包: {len(skipped_lines)} 个", "INFO")

    safe_write(ROOT / "requirements.txt", prod_content)
    safe_write(ROOT / "requirements-dev.txt", dev_content)

    if skipped_lines and not DRY_RUN:
        skip_path = ROOT / "requirements-skipped.txt"
        skip_content = header + "# Low-frequency packages (use count < 100)\n# Review before installing\n\n"
        for line in sorted(set(skipped_lines)):
            skip_content += line + "\n"
        safe_write(skip_path, skip_content)
        log(f"低频包已保存到 requirements-skipped.txt ({len(skipped_lines)} 个)", "INFO")


# ──────────────────────────────────────────────────────────
# Fix 5: 验证 Brain Topics 完整性
# ──────────────────────────────────────────────────────────
def fix5_brain_health_check():
    log("=" * 50)
    log("Fix 5: 验证 Brain Topics 完整性")
    log("=" * 50)

    topics_dir = ROOT / "storage" / "Brain" / "topics"
    index_path = topics_dir / "_index.json"

    if not index_path.exists():
        log("_index.json 不存在", "ERR")
        return

    index_data = json.loads(index_path.read_text(encoding="utf-8"))
    indexed_files = {entry["file"] for entry in index_data if "file" in entry}
    log(f"索引条目数: {len(indexed_files)}", "INFO")

    actual_files = set()
    for f in topics_dir.glob("*.json"):
        if f.name != "_index.json":
            actual_files.add(f.name)
    log(f"实际文件数: {len(actual_files)}", "INFO")

    missing_files = indexed_files - actual_files
    orphan_files = actual_files - indexed_files

    if missing_files:
        log(f"索引中有但文件缺失: {len(missing_files)} 个", "WARN")
        for f in sorted(missing_files)[:10]:
            log(f"  缺失: {f}", "WARN")
        if len(missing_files) > 10:
            log(f"  ... 还有 {len(missing_files) - 10} 个", "WARN")

    if orphan_files:
        log(f"文件存在但未索引: {len(orphan_files)} 个", "WARN")
        for f in sorted(orphan_files)[:10]:
            log(f"  未索引: {f}", "WARN")
        if len(orphan_files) > 10:
            log(f"  ... 还有 {len(orphan_files) - 10} 个", "WARN")

    corrupted = []
    for f in actual_files:
        fpath = topics_dir / f
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "title" not in data:
                corrupted.append(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            corrupted.append(f)

    if corrupted:
        log(f"损坏/格式异常文件: {len(corrupted)} 个", "ERR")
        for f in corrupted[:5]:
            log(f"  损坏: {f}", "ERR")
    else:
        log("所有文件 JSON 格式正常", "OK")

    if not DRY_RUN and orphan_files:
        backup_file(index_path)
        new_index = [e for e in index_data if e.get("file") in actual_files]
        for fname in orphan_files:
            fpath = topics_dir / fname
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                new_index.append({
                    "id": fname.replace(".json", ""),
                    "title": data.get("title", fname),
                    "tags": data.get("tags", []),
                    "date": data.get("date", datetime.now().isoformat()),
                    "file": fname,
                    "score": data.get("score", 5),
                })
            except Exception:
                new_index.append({
                    "id": fname.replace(".json", ""),
                    "title": f"[auto-indexed] {fname}",
                    "tags": [],
                    "date": datetime.now().isoformat(),
                    "file": fname,
                    "score": 3,
                })

        index_path.write_text(json.dumps(new_index, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"已修复索引: 移除 {len(missing_files)} 个失效条目，添加 {len(orphan_files)} 个新条目", "OK")
    elif DRY_RUN and orphan_files:
        log(f"[DRY] 将修复索引: 移除 {len(missing_files)} 个失效条目，添加 {len(orphan_files)} 个新条目", "DRY")

    if not missing_files and not orphan_files and not corrupted:
        log("Brain Topics 完整性检查通过！", "OK")


# ──────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────
ALL_FIXES = {
    1: ("创建 context.json", fix1_create_context_json),
    3: ("更新 last_check + 自动更新注入", fix3_update_last_check),
    4: ("拆分 requirements.txt", fix4_split_requirements),
    5: ("Brain Topics 健康检查", fix5_brain_health_check),
}


def main():
    global DRY_RUN, ONLY_ITEMS

    args = sys.argv[1:]
    if "--dry-run" in args:
        DRY_RUN = True
        args.remove("--dry-run")

    if "--only" in args:
        idx = args.index("--only")
        ONLY_ITEMS = [int(x) for x in args[idx + 1:] if x.isdigit()]
        args = args[:idx]

    print(f"\n{'='*60}")
    print(f"  /python 系统优化修复脚本 v1.0")
    print(f"  模式: {'DRY RUN (预览)' if DRY_RUN else 'LIVE (执行)'}")
    print(f"  时间: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    fixes_to_run = ONLY_ITEMS if ONLY_ITEMS else sorted(ALL_FIXES.keys())

    for fix_id in fixes_to_run:
        if fix_id in ALL_FIXES:
            name, func = ALL_FIXES[fix_id]
            print(f"\n>>> 执行 Fix {fix_id}: {name}\n")
            try:
                func()
            except Exception as e:
                log(f"Fix {fix_id} 执行失败: {e}", "ERR")
        else:
            log(f"Fix {fix_id} 不存在", "WARN")

    print(f"\n{'='*60}")
    print(f"  全部完成！模式: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
