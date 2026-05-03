#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件保护与自动备份系统 — CC 三级缓存

功能:
- 标记核心文件为"受保护"（修改前必须备份）
- 自动备份被修改的文件到 storage/cc/2_old/
- 原始下载文件归档到 storage/cc/1_raw/
- 30天未使用的文件移到 storage/cc/3_unused/
- 保护注册表持久化（.protected_files.json）

设计理念 (来自  系统):
    "缓存即历史" — 不删除，只归档。每次修改都有迹可循。

用法:
    from core.file_protector import FileProtector

    fp = FileProtector()
    fp.register("core/dispatcher.py")          # 标记为受保护
    fp.safe_write("core/dispatcher.py", code)  # 安全写入（自动备份）
    fp.is_protected("core/dispatcher.py")      # 检查是否受保护
"""

import json
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set


class FileProtector:
    """文件保护 + CC 三级缓存管理器"""

    CC_RAW = "1_raw"       # 原始下载文件
    CC_OLD = "2_old"       # 被替换的旧版本
    CC_UNUSED = "3_unused" # 30天未使用的文件
    UNUSED_AGE_DAYS = 30
    BACKUP_RETENTION = 50  # 每个文件最多保留的备份数

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.environ.get(
                "AI_BASE_DIR",
                str(Path(__file__).resolve().parent.parent)
            )
        self.base_dir = Path(base_dir)
        self.cc_root = self.base_dir / "storage" / "cc"
        self.cc_raw = self.cc_root / self.CC_RAW
        self.cc_old = self.cc_root / self.CC_OLD
        self.cc_unused = self.cc_root / self.CC_UNUSED

        for d in [self.cc_raw, self.cc_old, self.cc_unused]:
            d.mkdir(parents=True, exist_ok=True)

        # 受保护文件注册表
        self._registry_path = self.base_dir / ".protected_files.json"
        self._protected: Set[str] = set()
        self._load_registry()

    # ================================================================
    # 注册管理
    # ================================================================

    def _load_registry(self):
        """加载受保护文件列表"""
        if self._registry_path.exists():
            try:
                data = json.loads(self._registry_path.read_text(encoding="utf-8"))
                self._protected = set(data.get("files", []))
            except Exception:
                self._protected = set()
        else:
            # 默认保护列表
            self._protected = set()

    def _save_registry(self):
        """保存受保护文件列表"""
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "files": sorted(self._protected),
        }
        self._registry_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def register(self, rel_path: str):
        """将文件标记为受保护

        Args:
            rel_path: 相对于 base_dir 的文件路径
        """
        self._protected.add(rel_path)
        self._save_registry()

    def unregister(self, rel_path: str):
        """取消保护"""
        self._protected.discard(rel_path)
        self._save_registry()

    def is_protected(self, rel_path: str) -> bool:
        """检查文件是否受保护"""
        return rel_path in self._protected

    def list_protected(self) -> List[str]:
        """列出所有受保护文件"""
        return sorted(self._protected)

    def register_core_files(self):
        """自动注册所有核心架构文件"""
        core_patterns = [
            "core/trae_ide_bridge.py",
            "core/dispatcher.py",
            "core/session_memory.py",
            "core/file_protector.py",
            "core/mcp_classifier.py",
            "core/infra_adapter.py",
            "core/superpowers.py",
            "core/evaluator.py",
            "core/data_bridge.py",
            "core/evo_engine.py",
            "core/ai_rules.py",
            "core/__init__.py",
            "scripts/run_orchestrated_agent.py",
            "scripts/chat_to_orchestrator.py",
            "scripts/start_orchestrated.py",
            "user/global/plugin/mcp-core/agent/claude_orch/claude_orchestrator.py",
            "user/global/plugin/mcp-core/agent/claude_orch/routing_rules.yaml",
            "user/global/plugin/mcp-core/agent/claude_orch/agent.yaml",
            "user/global/plugin/mcp-core/agent/trae_control.py",
            "user/global/workflows/test-before-commit.yaml",
            "user/global/workflows/daily-health-check.yaml",
            "user/global/clis/pytest-runner.yaml",
            "user/global/clis/flake8-runner.yaml",
            "user/global/clis/git-commit.yaml",
            "user/global/skill/vuln-hunter/skill.yaml",
            "user/global/skill/vuln-hunter/knowledge/web_vuln_patterns.md",
            "user/global/skill/vuln-hunter/knowledge/code_audit_checklist.md",
            "user/global/skill/vuln-hunter/knowledge/network_recon.md",
            "user/global/skill/vuln-hunter/knowledge/decompile_sop.md",
            "user/global/clis/jadx-decompiler.yaml",
            "user/global/clis/dnspy-decompiler.yaml",
            "user/global/clis/ghidra-headless.yaml",
            "user/global/clis/ilspy-decompiler.yaml",
            "user/global/clis/jd-gui-decompiler.yaml",
            "storage/rules/ai_rules.yaml",
            "storage/bridge/sync_config.yaml",
        ]

        count = 0
        for pattern in core_patterns:
            abs_path = self.base_dir / pattern
            if abs_path.exists():
                self._protected.add(pattern)
                count += 1

        if count > 0:
            self._save_registry()

        return count

    # ================================================================
    # 安全读写
    # ================================================================

    def safe_write(self, rel_path: str, content: str,
                   encoding: str = "utf-8") -> bool:
        """安全写入文件 — 如果文件受保护，先备份再写入

        Args:
            rel_path: 相对于 base_dir 的文件路径
            content:  要写入的内容

        Returns:
            是否成功
        """
        abs_path = self.base_dir / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        # 如果文件已存在且受保护 → 备份
        if abs_path.exists() and self.is_protected(rel_path):
            self._backup_to_old(rel_path, abs_path)

        # 写入
        try:
            abs_path.write_text(content, encoding=encoding)
            return True
        except Exception as e:
            print(f"[FileProtector] 写入失败 ({rel_path}): {e}")
            return False

    def safe_read(self, rel_path: str, encoding: str = "utf-8") -> Optional[str]:
        """安全读取文件"""
        abs_path = self.base_dir / rel_path
        if not abs_path.exists():
            return None
        try:
            return abs_path.read_text(encoding=encoding)
        except Exception as e:
            print(f"[FileProtector] 读取失败 ({rel_path}): {e}")
            return None

    def _backup_to_old(self, rel_path: str, abs_path: Path):
        """将文件备份到 CC/2_old/

        命名格式: {filename}.{timestamp}.bak
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{abs_path.name}.{ts}.bak"
        backup_path = self.cc_old / backup_name

        try:
            shutil.copy2(str(abs_path), str(backup_path))

            # 限制每个文件的备份数量
            prefix = f"{abs_path.name}."
            backups = sorted(
                [p for p in self.cc_old.glob(f"{abs_path.name}.*.bak")],
                key=lambda p: p.stat().st_mtime
            )
            while len(backups) > self.BACKUP_RETENTION:
                oldest = backups.pop(0)
                oldest.unlink()

        except Exception as e:
            print(f"[FileProtector] 备份失败 ({rel_path}): {e}")

    # ================================================================
    # CC 缓存管理
    # ================================================================

    def archive_raw(self, rel_path: str, source_path: str = None):
        """将原始下载文件归档到 CC/1_raw/

        Args:
            rel_path:    目标相对路径（在 1_raw 下）
            source_path: 源文件绝对路径（默认: base_dir/rel_path）
        """
        src = Path(source_path) if source_path else (self.base_dir / rel_path)
        if not src.exists():
            return False

        dst = self.cc_raw / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            if src.is_dir():
                shutil.copytree(str(src), str(dst))
            else:
                shutil.copy2(str(src), str(dst))
            return True
        except Exception as e:
            print(f"[FileProtector] 归档失败 ({rel_path}): {e}")
            return False

    def move_to_unused(self, rel_path: str):
        """将不常用的文件移到 CC/3_unused/"""
        src = self.base_dir / rel_path
        if not src.exists():
            return False

        dst = self.cc_unused / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dst))
            return True
        except Exception as e:
            print(f"[FileProtector] 移动失败 ({rel_path}): {e}")
            return False

    def scan_unused(self, dry_run: bool = True) -> List[dict]:
        """扫描 30 天未使用的文件

        Returns:
            [{"path": str, "days_unused": int, "size_kb": float}, ...]
        """
        cutoff = time.time() - (self.UNUSED_AGE_DAYS * 86400)
        results = []
        skip_prefixes = ["storage/", ".git/", ".venv/", "node_modules/",
                         "__pycache__/", ".mypy_cache/"]

        for f in self.base_dir.rglob("*"):
            if f.is_file() and f.stat().st_atime < cutoff:
                rel = str(f.relative_to(self.base_dir)).replace("\\", "/")
                if any(rel.startswith(p) for p in skip_prefixes):
                    continue
                days = (time.time() - f.stat().st_atime) / 86400
                results.append({
                    "path": rel,
                    "days_unused": round(days, 1),
                    "size_kb": round(f.stat().st_size / 1024, 1),
                })

        results.sort(key=lambda r: r["days_unused"], reverse=True)

        if not dry_run:
            for r in results:
                self.move_to_unused(r["path"])

        return results

    def get_cc_stats(self) -> dict:
        """获取 CC 缓存统计"""
        stats = {}
        for name, path in [
            ("raw", self.cc_raw),
            ("old", self.cc_old),
            ("unused", self.cc_unused),
        ]:
            files = list(path.rglob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            stats[name] = {
                "count": len(files),
                "size_mb": round(total_size / (1024 * 1024), 2),
            }
        return stats

    def generate_cc_report(self) -> str:
        """生成 CC 缓存报告"""
        stats = self.get_cc_stats()
        unused = self.scan_unused(dry_run=True)

        lines = ["# CC 缓存报告", f"生成时间: {datetime.now().isoformat()}", ""]
        lines.append("## 存储统计")
        for name, s in stats.items():
            lines.append(f"- **{name}**: {s['count']} 文件, {s['size_mb']} MB")
        lines.append("")
        lines.append(f"## 受保护文件 ({len(self._protected)} 个)")
        for p in sorted(self._protected)[:20]:
            lines.append(f"- `{p}`")
        if len(self._protected) > 20:
            lines.append(f"- ... 及另外 {len(self._protected) - 20} 个文件")
        lines.append("")
        lines.append(f"## 30天未使用 ({len(unused)} 个)")
        for u in unused[:10]:
            lines.append(f"- `{u['path']}` ({u['days_unused']}天, {u['size_kb']}KB)")

        return "\n".join(lines)


# ============================================================
# 模块级便捷函数
# ============================================================

_protector_instance = None


def get_protector() -> FileProtector:
    """获取全局文件保护实例"""
    global _protector_instance
    if _protector_instance is None:
        _protector_instance = FileProtector()
    return _protector_instance


# ============================================================
# 自测试
# ============================================================
if __name__ == "__main__":
    print("=" * 55)
    print("File Protector — 自测试")
    print("=" * 55)

    fp = FileProtector()

    # 1. 注册核心文件
    print("\n[1] 注册核心文件...")
    count = fp.register_core_files()
    print(f"  已注册 {count} 个核心文件")

    # 2. 列出受保护文件
    print("\n[2] 受保护文件列表 (前 5 个):")
    for p in fp.list_protected()[:5]:
        print(f"  - {p}")

    # 3. 检查保护
    print("\n[3] 检查保护状态...")
    test_path = "core/dispatcher.py"
    print(f"  {test_path}: {'受保护' if fp.is_protected(test_path) else '未保护'}")

    # 4. 安全写入测试
    print("\n[4] 安全写入测试...")
    test_file = "storage/cc/_test_protected.txt"
    fp.register(test_file)
    fp.safe_write(test_file, "第一版本内容")
    fp.safe_write(test_file, "第二版本内容（修改后）")
    backups = list(fp.cc_old.glob("_test_protected.txt.*.bak"))
    print(f"  备份数: {len(backups)}")
    for b in backups:
        print(f"    - {b.name}")

    # 5. CC 统计
    print("\n[5] CC 缓存统计...")
    stats = fp.get_cc_stats()
    for name, s in stats.items():
        print(f"  {name}: {s['count']} 文件, {s['size_mb']} MB")

    # 清理测试文件
    fp.unregister(test_file)
    (fp.base_dir / test_file).unlink(missing_ok=True)
    for b in backups:
        b.unlink(missing_ok=True)

    print("\n" + "=" * 55)
    print("测试完成")
