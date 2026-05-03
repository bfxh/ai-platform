#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据桥接 — TRAE ↔ CLAUDE 双向同步引擎

桥接模式: TRAE 和 CLAUDE 各自独立存储, Bridge 层按需同步:
  - TRAE → CLAUDE: 对话记录导入 session_memory (已有 trae_importer)
  - CLAUDE → TRAE: evo 优化建议推送到 TRAE workspace (TraeExporter)
  - 双向广播: shared_context 系统跨系统上下文广播

用法:
    from core.data_bridge import DataBridge

    bridge = DataBridge()
    bridge.sync_now("conversations")   # 立即同步
    bridge.start_sync()                # 启动定时同步 (后台线程)
    bridge.get_sync_status()           # 查看状态
    bridge.stop_sync()                 # 停止
"""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable


# ============================================================
# 同步配置
# ============================================================

DEFAULT_SYNC_CONFIG = {
    "bridge_mode": "sync",
    "interval_seconds": 300,
    "direction": "bidirectional",
    "scope": ["conversations", "insights", "skills"],
    "auto_start": False,
    "retry_on_failure": True,
    "max_retries": 3,
}


class SyncConfig:
    """同步配置管理"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            base_dir = os.environ.get(
                "AI_BASE_DIR",
                str(Path(__file__).resolve().parent.parent)
            )
            config_path = str(Path(base_dir) / "storage" / "bridge" / "sync_config.yaml")
        self.config_path = Path(config_path)
        self.data = self._load()

    def _load(self) -> dict:
        if self.config_path.exists():
            try:
                import yaml
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data:
                    return {**DEFAULT_SYNC_CONFIG, **data}
            except Exception:
                pass
        # 写默认
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._save(DEFAULT_SYNC_CONFIG)
        return dict(DEFAULT_SYNC_CONFIG)

    def _save(self, data: dict):
        try:
            import yaml
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        except ImportError:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def update(self, key: str, value):
        self.data[key] = value
        self._save(self.data)

    def to_dict(self) -> dict:
        return dict(self.data)


# ============================================================
# 数据桥接
# ============================================================

class DataBridge:
    """TRAE ↔ CLAUDE 数据桥接"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.environ.get(
                "AI_BASE_DIR",
                str(Path(__file__).resolve().parent.parent)
            )
        self.base_dir = Path(base_dir)
        self.bridge_dir = self.base_dir / "storage" / "bridge"
        self.bridge_dir.mkdir(parents=True, exist_ok=True)

        # 配置
        self.config = SyncConfig()

        # 状态
        self._status: Dict[str, Any] = {
            "last_sync": None,
            "next_sync": None,
            "items_synced": 0,
            "errors": 0,
            "running": False,
            "direction": self.config.get("direction", "bidirectional"),
        }

        # 定时器线程
        self._timer: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 集成
        self._adapter = None
        try:
            from core.infra_adapter import get_adapter
            self._adapter = get_adapter()
        except Exception:
            pass

    # ================================================================
    # 同步操作
    # ================================================================

    def sync_now(self, scope: str = "all") -> dict:
        """立即执行一次同步

        Args:
            scope: conversations / insights / skills / all
        """
        if scope == "all":
            scope = "conversations,insights,skills"

        synced = {}
        errors = []

        scopes = [s.strip() for s in scope.split(",")]

        for s in scopes:
            try:
                if s == "conversations":
                    synced[s] = self._sync_conversations()
                elif s == "insights":
                    synced[s] = self._sync_insights()
                elif s == "skills":
                    synced[s] = self._sync_skills()
            except Exception as e:
                errors.append({s: str(e)})

        self._status["last_sync"] = datetime.now().isoformat()
        self._status["items_synced"] += sum(
            v.get("count", 0) if isinstance(v, dict) else 0
            for v in synced.values()
        )
        self._status["errors"] += len(errors)

        # 记录到 session_memory
        if self._adapter:
            self._adapter.add_session_note(
                "DataBridge", f"sync: {scope}",
                {"success": len(errors) == 0, "synced": synced,
                 "errors": errors}
            )

        return {"synced": synced, "errors": errors, "status": "ok" if not errors else "partial"}

    def _sync_conversations(self) -> dict:
        """TRAE 对话 → CLAUDE session_memory"""
        count = 0
        try:
            from storage.Brain.importers.trae_importer import TraeImporter
            importer = TraeImporter()
            vscdb_files = importer.scan_vscdb_files()
            if vscdb_files:
                stats = importer.import_all()
                count = stats.get("total_messages", 0)
        except Exception as e:
            return {"count": 0, "error": str(e)}
        return {"count": count}

    def _sync_insights(self) -> dict:
        """CLAUDE evo 建议 → TRAE 上下文"""
        count = 0
        try:
            from core.evo_engine import get_evo_engine
            evo = get_evo_engine()
            suggestions = evo.get_suggestions(min_severity="medium")

            if suggestions:
                try:
                    from storage.Brain.importers.trae_importer import TraeExporter
                    exporter = TraeExporter()
                    result = exporter.export_evo_feedback(suggestions)
                    count = result.get("exported", 0)
                except ImportError:
                    # TraeExporter 不可用 → 通过 shared_context 广播
                    count = self._broadcast_insights(suggestions)
        except Exception as e:
            return {"count": 0, "error": str(e)}
        return {"count": count}

    def _sync_skills(self) -> dict:
        """双向技能同步"""
        count = 0
        # CLAUDE → TRAE: 导出技能定义
        try:
            from storage.Brain.importers.trae_importer import TraeExporter
            exporter = TraeExporter()
            # 获取最近注册的技能
            try:
                from core.superpowers import get_superpower_engine
                sp = get_superpower_engine()
                skill_list = [s["name"] for s in sp.list_superpowers()]
                if skill_list:
                    result = exporter.export_skills_to_trae(skill_list)
                    count += result.get("exported", 0)
            except Exception:
                pass
        except Exception:
            pass
        return {"count": count}

    def _broadcast_insights(self, insights: List[dict]) -> int:
        """通过 shared_context 广播 insights"""
        count = 0
        try:
            from core.shared_context import ContextBroadcaster
            broadcaster = ContextBroadcaster()
            for insight in insights[:5]:
                broadcaster.broadcast({
                    "type": "evo_insight",
                    "agent": insight.get("agent", "unknown"),
                    "suggestion": insight.get("suggestion", ""),
                    "severity": insight.get("severity", "low"),
                    "timestamp": datetime.now().isoformat(),
                })
                count += 1
        except Exception:
            pass
        return count

    # ================================================================
    # 定时同步
    # ================================================================

    def start_sync(self) -> bool:
        """启动定时同步"""
        if self._timer and self._timer.is_alive():
            return True

        self._stop_event.clear()
        self._status["running"] = True
        interval = self.config.get("interval_seconds", 300)

        self._timer = threading.Thread(
            target=self._sync_loop,
            args=(interval,),
            daemon=True,
            name="DataBridge-Sync"
        )
        self._timer.start()
        return True

    def stop_sync(self) -> bool:
        """停止定时同步"""
        self._stop_event.set()
        self._status["running"] = False
        if self._timer:
            self._timer.join(timeout=5)
        return True

    def _sync_loop(self, interval: int):
        """同步循环"""
        while not self._stop_event.is_set():
            self._status["next_sync"] = (
                datetime.now() + time.__dict__.get("timedelta", lambda s: None)(seconds=interval)
            )
            # 等待间隔或停止信号
            if self._stop_event.wait(interval):
                break
            # 执行同步
            try:
                scope = ",".join(self.config.get("scope", ["conversations"]))
                self.sync_now(scope)
            except Exception:
                pass

    # ================================================================
    # 状态
    # ================================================================

    def get_sync_status(self) -> dict:
        """获取同步状态"""
        interval = self.config.get("interval_seconds", 300)
        last = self._status.get("last_sync")
        return {
            **self._status,
            "interval_seconds": interval,
            "next_sync_in": self._next_sync_in(interval),
            "config": self.config.to_dict(),
        }

    def _next_sync_in(self, interval: int) -> str:
        last = self._status.get("last_sync")
        if not last:
            return "未开始"
        try:
            last_dt = datetime.fromisoformat(last)
            elapsed = (datetime.now() - last_dt).total_seconds()
            remaining = max(0, interval - elapsed)
            if remaining <= 0:
                return "即将执行"
            return f"{int(remaining)}s"
        except Exception:
            return "?"


# ============================================================
# 模块级便捷函数
# ============================================================

_instance = None


def get_bridge() -> DataBridge:
    global _instance
    if _instance is None:
        _instance = DataBridge()
    return _instance
