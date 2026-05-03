#!/usr/bin/env python
"""Event Bridge - 跨软件事件桥接器

将Brain记忆系统与系统级EventBus连接:
- 监听Dispatcher事件 → 触发记忆记录
- 监听Skill事件 → 触发成长追踪
- 监听KB事件 → 同步到Brain知识库
- 监听Workflow事件 → 记录决策链
- 将Brain召回的事件推送到其他组件
"""

import json
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# 添加MCP Core路径
MCP_CORE_PATH = Path("/python/user/global/plugin/mcp-core")
if str(MCP_CORE_PATH) not in sys.path:
    sys.path.insert(0, str(MCP_CORE_PATH))

ROOT = Path(__file__).parent.parent  # storage/Brain/
INTEGRATION_DIR = ROOT / "integration"
INTEGRATION_DIR.mkdir(parents=True, exist_ok=True)


class EventBridge:
    """事件桥接器 - Brain ↔ System EventBus"""

    def __init__(self, auto_subscribe: bool = True):
        self._lock = threading.Lock()
        self._event_bus = None
        self._connected = False
        self._subscribed_events = []
        self._handlers = {}  # event_type → handler list
        self._event_count = 0

        # 懒加载Brain模块
        self._engine = None
        self._tracker = None
        self._auditor = None

        if auto_subscribe:
            self.connect()

    @property
    def engine(self):
        if self._engine is None:
            from memory.engine import get_memory_engine
            self._engine = get_memory_engine()
        return self._engine

    @property
    def tracker(self):
        if self._tracker is None:
            from growth.tracker import get_growth_tracker
            self._tracker = get_growth_tracker()
        return self._tracker

    @property
    def auditor(self):
        if self._auditor is None:
            from supervisor.audit import get_auditor
            self._auditor = get_auditor()
        return self._auditor

    # ─── 连接管理 ──────────────────────────────────────

    def connect(self):
        """连接到系统EventBus"""
        try:
            from event_bus import EventBus

            # 尝试获取现有的EventBus实例
            # 如果不存在则创建新的
            self._event_bus = self._find_or_create_bus()
            if self._event_bus:
                self._connected = True
                self._event_bus.start()
                self._setup_listeners()
                print("[EventBridge] 已连接到系统EventBus")
                return True
        except ImportError:
            print("[EventBridge] MCP Core event_bus不可用，使用独立模式")
        except Exception as e:
            print(f"[EventBridge] 连接失败: {e}")
        return False

    def _find_or_create_bus(self):
        """查找或创建EventBus"""
        try:
            from event_bus import EventBus

            # 检查是否有运行的实例
            from resource_manager import get_resource_tracker
            rt = get_resource_tracker()
            # 尝试获取已追踪的event_bus
            for resource in rt.list_resources():
                if resource.get("type") == "event_bus":
                    return resource.get("instance")

            # 创建新实例
            bus = EventBus(persist_events=True)
            return bus
        except Exception:
            return None

    def disconnect(self):
        """断开连接"""
        self._connected = False
        print("[EventBridge] 已断开")

    # ─── 事件监听器 ────────────────────────────────────

    def _setup_listeners(self):
        """设置默认监听器"""
        if not self._event_bus:
            return

        # Dispatcher事件
        self.listen("dispatcher.unit.executed", self._on_unit_executed)
        self.listen("dispatcher.unit.registered", self._on_unit_registered)

        # Skill事件
        self.listen("skill.completed", self._on_skill_completed)
        self.listen("skill.failed", self._on_skill_failed)

        # Knowledge Base事件
        self.listen("kb.entry.added", self._on_kb_added)
        self.listen("kb.entry.updated", self._on_kb_updated)

        # Workflow事件
        self.listen("workflow.completed", self._on_workflow_completed)

        # System事件
        self.listen("system.error", self._on_system_error)

        # Plugin事件
        self.listen("plugin.loaded", self._on_plugin_loaded)

    def listen(self, event_type: str, handler: Callable):
        """订阅事件类型"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

        if self._event_bus:
            try:
                self._event_bus.subscribe(event_type, handler, async_mode=True)
                self._subscribed_events.append(event_type)
            except Exception as e:
                print(f"[EventBridge] 订阅失败 {event_type}: {e}")

    # ─── 事件处理器 ────────────────────────────────────

    def _on_unit_executed(self, event):
        """Dispatcher单元执行完成"""
        data = event.get("data", event) if isinstance(event, dict) else {}
        unit_type = data.get("unit_type", "unknown")
        unit_name = data.get("name", "unknown")
        result = data.get("result", "unknown")
        duration = data.get("duration_ms", 0)

        # 记录到成长追踪
        self.tracker.log_task_complete(
            task=f"{unit_type}:{unit_name}",
            method=f"通过Dispatcher执行{unit_type}",
            result=str(result)[:200],
            experience=f"{unit_type} '{unit_name}' 执行完成",
            duration_minutes=duration / 60000 if duration else 0,
        )

        # 作为工作记忆
        self.engine.wm_set(f"last_{unit_type}_execution", {
            "name": unit_name,
            "result": str(result)[:200],
            "timestamp": datetime.now().isoformat(),
        })

        self._event_count += 1

    def _on_unit_registered(self, event):
        """新单元注册"""
        data = event.get("data", event) if isinstance(event, dict) else {}
        unit_type = data.get("unit_type", "unknown")
        unit_name = data.get("name", "unknown")

        # 记录知识
        self.engine.kb_save(
            category="tool_usage_patterns",
            entry_id=f"unit_{unit_type}_{unit_name}".replace(" ", "_"),
            title=f"注册{unit_type}: {unit_name}",
            content=f"系统中注册了{unit_type}单元: {unit_name}",
            tags=[unit_type, "registration"],
            importance=3,
        )
        self._event_count += 1

    def _on_skill_completed(self, event):
        """Skill完成"""
        data = event.get("data", event) if isinstance(event, dict) else {}
        skill_name = data.get("skill_name", data.get("name", "unknown"))
        duration = data.get("duration_ms", 0)

        self.tracker.log_task_complete(
            task=f"Skill: {skill_name}",
            method="Skill系统执行",
            result="completed",
            experience=f"技能 '{skill_name}' 执行成功",
            duration_minutes=duration / 60000 if duration else 0,
        )
        self._event_count += 1

    def _on_skill_failed(self, event):
        """Skill失败"""
        data = event.get("data", event) if isinstance(event, dict) else {}
        skill_name = data.get("skill_name", data.get("name", "unknown"))
        error = data.get("error", "unknown error")

        self.tracker.log_error_resolved(
            error=f"Skill {skill_name} 失败",
            root_cause=str(error)[:200],
            fix="待分析",
            prevention="记录此错误模式以供后续参考",
        )
        self._event_count += 1

    def _on_kb_added(self, event):
        """知识条目添加"""
        data = event.get("data", event) if isinstance(event, dict) else {}
        title = data.get("title", "unknown")
        content = data.get("content", "")
        category = data.get("category", "domain_knowledge")
        entry_id = data.get("id", f"kb_import_{self._event_count}")

        # 同步到Brain知识库
        try:
            self.engine.kb_save(
                category=category,
                entry_id=entry_id,
                title=title,
                content=content,
                tags=data.get("tags", []),
                importance=data.get("importance", 5),
            )
        except Exception:
            pass
        self._event_count += 1

    def _on_kb_updated(self, event):
        """知识条目更新 - 同步更新"""
        # 由kb_added覆盖，kb_load会自动更新
        self._event_count += 1

    def _on_workflow_completed(self, event):
        """工作流完成"""
        data = event.get("data", event) if isinstance(event, dict) else {}
        workflow_name = data.get("workflow_name", data.get("name", "unknown"))
        steps = data.get("total_steps", data.get("steps_count", 0))
        duration = data.get("duration_ms", 0)

        # 保存会话
        self.engine.save_session(
            session_id=f"wf_{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            summary=f"工作流 '{workflow_name}' 完成，共{steps}步",
            key_decisions=[f"执行工作流: {workflow_name}"],
            lessons=[f"工作流包含{steps}个步骤"],
            duration_minutes=int(duration / 60000) if duration else 0,
        )

        self.tracker.log_task_complete(
            task=f"Workflow: {workflow_name}",
            method=f"执行{steps}个步骤",
            result="completed",
            experience=f"工作流模式: {steps}步流水线",
            duration_minutes=duration / 60000 if duration else 0,
        )
        self._event_count += 1

    def _on_system_error(self, event):
        """系统错误"""
        data = event.get("data", event) if isinstance(event, dict) else {}
        error_msg = data.get("error", data.get("message", "unknown error"))
        source = data.get("source", event.get("source", "unknown"))

        self.tracker.log_error_resolved(
            error=f"系统错误 [{source}]",
            root_cause=str(error_msg)[:300],
            fix="待处理",
            prevention="错误已记录，待下次遇到时参考",
        )
        self._event_count += 1

    def _on_plugin_loaded(self, event):
        """插件加载"""
        data = event.get("data", event) if isinstance(event, dict) else {}
        plugin_name = data.get("plugin_name", data.get("name", "unknown"))
        plugin_type = data.get("plugin_type", "unknown")

        self.engine.kb_save(
            category="tool_usage_patterns",
            entry_id=f"plugin_{plugin_name}".replace(" ", "_"),
            title=f"加载插件: {plugin_name}",
            content=f"类型: {plugin_type}",
            tags=["plugin", plugin_type],
            importance=3,
        )
        self._event_count += 1

    # ─── 主动推送 ──────────────────────────────────────

    def push_event(self, event_type: str, data: dict, source: str = "Brain"):
        """向EventBus推送事件"""
        if self._event_bus and self._connected:
            try:
                self._event_bus.publish(event_type, data, source=source)
                return True
            except Exception as e:
                print(f"[EventBridge] 推送失败: {e}")
        return False

    def notify_knowledge_gained(self, title: str, content: str,
                                category: str = "domain_knowledge"):
        """通知系统学到了新知识"""
        return self.push_event("brain.knowledge.gained", {
            "title": title,
            "content": content,
            "category": category,
            "source": "Brain",
            "timestamp": datetime.now().isoformat(),
        })

    def notify_pattern_discovered(self, pattern_name: str,
                                  description: str):
        """通知系统发现了新模式"""
        return self.push_event("brain.pattern.discovered", {
            "name": pattern_name,
            "description": description,
            "source": "Brain",
            "timestamp": datetime.now().isoformat(),
        })

    def notify_compliance_issue(self, violation_type: str,
                                detail: str):
        """通知合规问题"""
        return self.push_event("brain.compliance.issue", {
            "violation_type": violation_type,
            "detail": detail,
            "source": "Brain::Auditor",
            "timestamp": datetime.now().isoformat(),
        })

    # ─── 状态 ──────────────────────────────────────────

    def status(self) -> dict:
        return {
            "connected": self._connected,
            "subscribed_events": self._subscribed_events,
            "handlers_count": sum(len(h) for h in self._handlers.values()),
            "events_processed": self._event_count,
        }


# ─── 全局单例 ───────────────────────────────────────────
_bridge_instance: Optional[EventBridge] = None


def get_event_bridge(auto_connect: bool = True) -> EventBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = EventBridge(auto_subscribe=auto_connect)
    return _bridge_instance


# ─── CLI ────────────────────────────────────────────────
if __name__ == "__main__":
    bridge = get_event_bridge()
    print("=== Event Bridge Status ===")
    print(json.dumps(bridge.status(), ensure_ascii=False, indent=2))

    # 模拟推送
    bridge.notify_knowledge_gained(
        "内存引擎设计模式",
        "使用LRU缓存+文件持久化双层架构管理记忆"
    )
    print("\n事件桥接器就绪")
