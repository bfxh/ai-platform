#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 分类验证与自动分类工具 — 确保 JM/BC/Tools 分类准确

功能:
- 扫描 storage/mcp/ 下所有 MCP 工具
- 与 mcp-config.json 注册表交叉验证
- 检测未注册/未分类/分类错误的工具
- 基于关键词+目录的自动分类建议
- 生成分类报告

分类规则 (来自  系统):
    JM — 建模类: blender, 3d, model, mesh, texture, ue, godot, unity, vision, video
    BC — 编程类: code, github, git, fix, patch, search, workflow, dev, vscode
    Tools — 工具类: download, network, system, monitor, automation, config, memory

用法:
    python core/mcp_classifier.py           # 验证所有工具分类
    python core/mcp_classifier.py --report  # 生成详细报告
    python core/mcp_classifier.py --fix     # 自动修复分类错误
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MCPClassifier:
    """MCP 工具分类验证与自动分类"""

    # 分类关键词映射
    CATEGORY_KEYWORDS = {
        "JM": [
            "blender", "3d", "model", "character", "scene", "animation",
            "mesh", "texture", "ue", "unreal", "godot", "unity",
            "vision", "video", "render", "material", "particle",
            "skeleton", "rig", "bone", "convert", "pipeline", "bake"
        ],
        "BC": [
            "code", "github", "git", "fix", "patch", "verify", "search",
            "workflow", "dev", "vscode", "lint", "quality", "intelligence",
            "architecture", "claude", "narsil", "mcp_workflow",
            "smart", "unified", "web_research"
        ],
        "Tools": [
            "download", "network", "system", "monitor", "automation",
            "config", "memory", "cache", "aria2", "translate",
            "extract", "aes", "scan", "da\\.", "screen", "process",
            "browser", "disk", "lazy", "hybrid", "optimizer"
        ],
    }

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = str(Path(__file__).resolve().parent.parent)
        self.base_dir = Path(base_dir)
        self.mcp_root = self.base_dir / "storage" / "mcp"
        self.config_path = self.mcp_root / "mcp-config.json"

    # ================================================================
    # 扫描
    # ================================================================

    def scan_tools(self) -> Dict[str, List[dict]]:
        """扫描所有 MCP 工具文件

        Returns:
            {"JM": [{name, path, keywords, ...}], "BC": [...], "Tools": [...]}
        """
        results = {"JM": [], "BC": [], "Tools": [], "unknown": []}

        for category_dir in ["JM", "BC", "Tools"]:
            cat_path = self.mcp_root / category_dir
            if not cat_path.exists():
                continue

            for py_file in sorted(cat_path.glob("*.py")):
                info = self._analyze_tool(py_file, category_dir)
                results[category_dir].append(info)

        return results

    def _analyze_tool(self, filepath: Path, dir_category: str) -> dict:
        """分析单个工具文件"""
        name = filepath.stem
        content = ""
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass

        # 提取文档字符串
        docstring = self._extract_docstring(content)

        # 提取关键词
        keywords = self._extract_keywords(name, docstring)

        # 推断分类
        inferred = self._infer_category(name, keywords, dir_category)

        return {
            "name": name,
            "path": str(filepath),
            "dir_category": dir_category,      # 目录分类
            "inferred_category": inferred,      # 推断分类
            "keywords": keywords[:10],          # 提取的关键词
            "docstring": docstring[:200],       # 文档摘要
            "is_mismatch": inferred != dir_category and inferred != "unknown",
        }

    def _extract_docstring(self, content: str) -> str:
        """提取模块文档字符串"""
        patterns = [
            r'"""(.+?)"""',         # 三引号
            r"'''(.+?)'''",
            r'"""([\s\S]+?)"""',    # 多行
        ]
        for pat in patterns:
            match = re.search(pat, content[:2000])
            if match:
                return match.group(1)[:500]
        return ""

    def _extract_keywords(self, name: str, docstring: str) -> List[str]:
        """从文件名和文档中提取关键词"""
        text = (name + " " + docstring).lower()
        words = set()

        # 从文件名提取（下划线分词）
        for part in name.replace("-", "_").split("_"):
            if len(part) > 1:
                words.add(part)

        # 从文档中提取常见技术词汇
        tech_terms = re.findall(r'\b[a-z_]{3,20}\b', text)
        words.update(tech_terms)

        return sorted(words)

    def _infer_category(self, name: str, keywords: List[str],
                        dir_category: str) -> str:
        """基于关键词推断分类"""
        scores = {"JM": 0, "BC": 0, "Tools": 0}
        text = (name + " " + " ".join(keywords)).lower()

        for cat, kws in self.CATEGORY_KEYWORDS.items():
            for kw in kws:
                if kw.lower() in text:
                    scores[cat] += 1

        best_cat = max(scores, key=scores.get)
        if scores[best_cat] == 0:
            return "unknown"
        return best_cat

    # ================================================================
    # 配置验证
    # ================================================================

    def load_config(self) -> dict:
        """加载 mcp-config.json"""
        if not self.config_path.exists():
            return {"mcpServers": {}}
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception:
            return {"mcpServers": {}}

    def validate_config(self) -> dict:
        """验证 mcp-config.json 与文件系统的一致性

        Returns:
            {"registered_but_missing": [...],     # 注册了但文件不存在
             "exists_but_unregistered": [...],     # 文件存在但未注册
             "category_mismatch": [...],           # 分类不一致
             "missing_category_field": [...],      # 缺少 category 字段
             "stats": {...}}
        """
        config = self.load_config()
        registered = set()
        issues = {
            "registered_but_missing": [],
            "exists_but_unregistered": [],
            "category_mismatch": [],
            "missing_category_field": [],
        }

        for name, entry in config.get("mcpServers", {}).items():
            registered.add(name)

            # 检查是否有 category
            if "category" not in entry:
                issues["missing_category_field"].append(name)
                continue

            # 检查文件是否存在
            path = entry.get("path", "")
            if path and not Path(path).exists():
                issues["registered_but_missing"].append({
                    "name": name,
                    "path": path,
                    "category": entry.get("category", ""),
                })

        # 检查未注册的工具
        tool_scan = self.scan_tools()
        for cat in ["JM", "BC", "Tools"]:
            for tool in tool_scan.get(cat, []):
                if tool["name"] not in registered:
                    issues["exists_but_unregistered"].append({
                        "name": tool["name"],
                        "category": cat,
                        "path": tool["path"],
                        "inferred": tool["inferred_category"],
                    })
                # 检查分类不一致
                if tool["is_mismatch"]:
                    entry = config.get("mcpServers", {}).get(tool["name"], {})
                    config_cat = entry.get("category", cat)
                    if config_cat != tool["inferred_category"]:
                        issues["category_mismatch"].append({
                            "name": tool["name"],
                            "dir_category": cat,
                            "config_category": config_cat,
                            "inferred_category": tool["inferred_category"],
                            "path": tool["path"],
                        })

        issues["stats"] = {
            "total_registered": len(registered),
            "total_found": sum(
                len(tool_scan.get(c, [])) for c in ["JM", "BC", "Tools"]
            ),
            "missing_files": len(issues["registered_but_missing"]),
            "unregistered": len(issues["exists_but_unregistered"]),
            "mismatches": len(issues["category_mismatch"]),
            "missing_category": len(issues["missing_category_field"]),
        }

        return issues

    # ================================================================
    # 自动修复
    # ================================================================

    def auto_fix(self, dry_run: bool = True) -> dict:
        """自动修复分类问题

        - 为未注册工具添加到 mcp-config.json
        - 修正分类不一致的工具
        - 补充缺失的 category 字段
        """
        config = self.load_config()
        issues = self.validate_config()
        fixes_applied = []

        # 1. 添加未注册工具
        for tool in issues["exists_but_unregistered"]:
            category = tool.get("inferred", tool["category"])
            entry = {
                "name": tool["name"],
                "command": "python",
                "args": [tool["path"]],
                "path": tool["path"],
                "category": category,
                "status": "active",
                "last_validated": datetime.now().strftime("%Y-%m-%d"),
                "description": f"{tool['name']} (自动注册)",
            }
            if not dry_run:
                config.setdefault("mcpServers", {})[tool["name"]] = entry
            fixes_applied.append({
                "action": "register",
                "name": tool["name"],
                "category": category,
            })

        # 2. 修正分类不一致
        for tool in issues["category_mismatch"]:
            if not dry_run and tool["name"] in config.get("mcpServers", {}):
                config["mcpServers"][tool["name"]]["category"] = tool["inferred_category"]
            fixes_applied.append({
                "action": "fix_category",
                "name": tool["name"],
                "from": tool["config_category"],
                "to": tool["inferred_category"],
            })

        # 3. 补充缺失 category
        for name in issues["missing_category_field"]:
            if not dry_run and name in config.get("mcpServers", {}):
                # 尝试从路径推断
                path = config["mcpServers"][name].get("path", "")
                for cat in ["JM", "BC", "Tools"]:
                    if f"/{cat}/" in path or f"\\{cat}\\" in path:
                        config["mcpServers"][name]["category"] = cat
                        fixes_applied.append({
                            "action": "add_category",
                            "name": name,
                            "category": cat,
                        })
                        break

        # 保存
        if not dry_run and fixes_applied:
            config["_optimized"] = True
            config["_optimized_at"] = datetime.now().strftime("%Y-%m-%d")
            self.config_path.write_text(
                json.dumps(config, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

        return {"dry_run": dry_run, "fixes": fixes_applied,
                "total_fixes": len(fixes_applied)}

    # ================================================================
    # 报告生成
    # ================================================================

    def generate_report(self) -> str:
        """生成完整分类报告"""
        issues = self.validate_config()
        tools = self.scan_tools()

        lines = ["# MCP 分类报告",
                 f"生成时间: {datetime.now().isoformat()}",
                 f"基础路径: {self.mcp_root}",
                 ""]

        # 统计
        stats = issues["stats"]
        lines.append("## 总览")
        lines.append(f"- 已注册工具: {stats['total_registered']}")
        lines.append(f"- 文件系统工具: {stats['total_found']}")
        lines.append(f"- 文件缺失: {stats['missing_files']}")
        lines.append(f"- 未注册: {stats['unregistered']}")
        lines.append(f"- 分类不一致: {stats['mismatches']}")
        lines.append(f"- 缺少分类: {stats['missing_category']}")
        lines.append("")

        # 分类明细
        lines.append("## 工具分类明细")
        for cat in ["JM", "BC", "Tools"]:
            cat_tools = tools.get(cat, [])
            lines.append(f"### {cat} ({len(cat_tools)} 个)")
            for t in cat_tools:
                flag = " ⚠️" if t["is_mismatch"] else ""
                lines.append(f"- `{t['name']}` — {t['docstring'][:80]}{flag}")
            lines.append("")

        # 问题
        if issues["category_mismatch"]:
            lines.append("## 分类不一致")
            for m in issues["category_mismatch"]:
                lines.append(f"- `{m['name']}`: 目录={m['dir_category']}, "
                             f"配置={m['config_category']}, 推断={m['inferred_category']}")
            lines.append("")

        if issues["exists_but_unregistered"]:
            lines.append("## 未注册工具")
            for u in issues["exists_but_unregistered"]:
                lines.append(f"- `{u['name']}` ({u['category']}) → 推断: {u.get('inferred','?')}")
            lines.append("")

        return "\n".join(lines)


# ============================================================
# CLI
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="MCP 分类验证与自动分类工具"
    )
    parser.add_argument("--report", "-r", action="store_true",
                        help="生成完整报告")
    parser.add_argument("--fix", action="store_true",
                        help="自动修复分类问题")
    parser.add_argument("--dry-run", "-d", action="store_true",
                        help="仅预览修复（不改动）")
    parser.add_argument("--stats", "-s", action="store_true",
                        help="仅显示统计")

    args = parser.parse_args()
    classifier = MCPClassifier()

    if args.report:
        print(classifier.generate_report())
    elif args.stats:
        issues = classifier.validate_config()
        stats = issues["stats"]
        print(f"MCP 统计: {stats}")
    elif args.fix:
        dry_run = args.dry_run
        result = classifier.auto_fix(dry_run=dry_run)
        mode = "DRY-RUN (预览)" if dry_run else "已应用"
        print(f"修复结果 ({mode}): {result['total_fixes']} 项")
        for fix in result["fixes"]:
            print(f"  [{fix['action']}] {fix.get('name','?')}")
    else:
        # 默认：验证模式
        issues = classifier.validate_config()
        stats = issues["stats"]
        print(f"MCP 分类验证")
        print(f"  已注册: {stats['total_registered']}  "
              f"文件系统: {stats['total_found']}")
        print(f"  问题: 缺失{stats['missing_files']} "
              f"未注册{stats['unregistered']} "
              f"不一致{stats['mismatches']} "
              f"缺分类{stats['missing_category']}")

        if issues["category_mismatch"]:
            print(f"\n分类不一致 ({len(issues['category_mismatch'])}):")
            for m in issues["category_mismatch"][:5]:
                print(f"  {m['name']}: {m['dir_category']} → {m['inferred_category']}")

        if issues["exists_but_unregistered"]:
            print(f"\n未注册工具 ({len(issues['exists_but_unregistered'])}):")
            for u in issues["exists_but_unregistered"][:5]:
                print(f"  {u['name']} ({u['category']})")

        if stats["missing_files"] == 0 and stats["unregistered"] == 0 \
                and stats["mismatches"] == 0:
            print("\n[OK] 所有 MCP 工具分类正确")


if __name__ == "__main__":
    main()
