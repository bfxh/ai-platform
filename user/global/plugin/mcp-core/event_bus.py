#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 事件总线（已修复资源泄漏）

功能:
- 技能间异步通信
- 事件订阅与发布
- 事件持久化
- 错误隔离
- 资源泄漏防护
"""

import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
from queue import Queue, Empty
from dataclasses import dataclass
from datetime import datetime

# 导入资源管理器
from resource_manager import ManagedThreadPoolExecutor, HookManager, get_resource_tracker


@dataclass
class Event:
    """事件对象"""
    type: str
    data: Dict[str, Any]
    timestamp: float
    source: str
    id: str

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type,
            'data': self.data,
            'timestamp': self.timestamp,
            'source': self.source
        }


class EventBus:
    """事件总线（已修复资源泄漏）"""

    def __init__(self, max_workers: int = 4, persist_events: bool = False):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.async_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_queue = Queue()
        self.running = False
        self.max_workers = max_workers
        self.persist_events = persist_events
        self.event_history: List[Event] = []
        self.max_history = 1000  # 最大历史记录数
        self._lock = threading.RLock()

        # 使用带资源管理的线程池
        self._executor = ManagedThreadPoolExecutor(max_workers=max_workers, name='event_bus')
        self._event_counter = 0

        # 使用钩子管理器
        self._hooks = HookManager(max_hooks_per_type=50)

        # 持久化路径
        if persist_events:
            self.persist_path = Path('/python/MCP_Core/events')
            self.persist_path.mkdir(parents=True, exist_ok=True)

        # 注册到资源追踪器
        get_resource_tracker().track('event_bus', self, 'main_event_bus')

    def start(self):
        """启动事件总线"""
        if not self.running:
            self.running = True
            self._worker_thread = threading.Thread(target=self._process_events, daemon=True)
            self._worker_thread.start()

    def stop(self):
        """停止事件总线"""
        self.running = False
        self._executor.shutdown(wait=True)
        get_resource_tracker().untrack('event_bus', self)

    def subscribe(self, event_type: str, callback: Callable, async_mode: bool = False):
        """订阅事件"""
        with self._lock:
            if async_mode:
                self.async_subscribers[event_type].append(callback)
                # 注册到钩子管理器
                self._hooks.register(f'async_{event_type}', callback)
            else:
                self.subscribers[event_type].append(callback)
                self._hooks.register(f'sync_{event_type}', callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅"""
        with self._lock:
            if callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
                self._hooks.unregister(f'sync_{event_type}', callback)
            if callback in self.async_subscribers[event_type]:
                self.async_subscribers[event_type].remove(callback)
                self._hooks.unregister(f'async_{event_type}', callback)

    def publish(self, event_type: str, data: Dict[str, Any], source: str = 'unknown'):
        """发布事件"""
        self._event_counter += 1
        event = Event(
            type=event_type,
            data=data,
            timestamp=time.time(),
            source=source,
            id=f"evt_{int(time.time())}_{self._event_counter}"
        )

        self.event_queue.put(event)

        # 持久化
        if self.persist_events:
            self._persist_event(event)

    def _process_events(self):
        """事件处理循环"""
        while self.running:
            try:
                event = self.event_queue.get(timeout=0.1)
                self._handle_event(event)
            except Empty:
                continue
            except Exception as e:
                print(f"[EventBus] 处理事件错误: {e}")

    def _handle_event(self, event: Event):
        """处理单个事件"""
        # 记录历史（带大小限制）
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            # 超过限制时清理一半，避免频繁清理
            self.event_history = self.event_history[-self.max_history//2:]

        # 同步回调
        with self._lock:
            callbacks = self.subscribers.get(event.type, []).copy()

        for callback in callbacks:
            try:
                callback(event.data)
            except Exception as e:
                print(f"[EventBus] 回调错误 ({callback.__name__}): {e}")

        # 异步回调
        with self._lock:
            async_callbacks = self.async_subscribers.get(event.type, []).copy()

        for callback in async_callbacks:
            self._executor.submit(self._safe_async_callback, callback, event.data)

    def _safe_async_callback(self, callback: Callable, data: Dict):
        """安全的异步回调包装"""
        try:
            callback(data)
        except Exception as e:
            print(f"[EventBus] 异步回调错误: {e}")

    def _persist_event(self, event: Event):
        """持久化事件"""
        try:
            date_str = datetime.now().strftime('%Y%m%d')
            file_path = self.persist_path / f"events_{date_str}.jsonl"
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"[EventBus] 持久化错误: {e}")

    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """获取事件历史"""
        history = self.event_history
        if event_type:
            history = [e for e in history if e.type == event_type]
        return history[-limit:]

    def wait_for_event(self, event_type: str, timeout: float = 30.0) -> Optional[Event]:
        """等待特定事件"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            for event in reversed(self.event_history):
                if event.type == event_type:
                    return event
            time.sleep(0.1)
        return None

    def clear_history(self):
        """清空历史"""
        self.event_history.clear()

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'queue_size': self.event_queue.qsize(),
            'history_size': len(self.event_history),
            'subscriber_count': sum(len(callbacks) for callbacks in self.subscribers.values()),
            'async_subscriber_count': sum(len(callbacks) for callbacks in self.async_subscribers.values()),
            'executor_stats': self._executor.stats
        }


# 全局事件总线实例
_event_bus_instance = None


def get_event_bus() -> EventBus:
    """获取全局事件总线"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
        _event_bus_instance.start()
    return _event_bus_instance


if __name__ == '__main__':
    # 测试事件总线
    bus = EventBus()
    bus.start()

    # 定义回调
    def on_transfer_complete(data):
        print(f"[回调] 传输完成: {data}")

    # 订阅事件
    bus.subscribe('transfer_complete', on_transfer_complete)

    # 发布事件
    print("发布事件...")
    bus.publish('transfer_complete', {'file': 'test.txt', 'size': 1024}, source='test')

    # 等待处理
    time.sleep(1)

    print("\n事件历史:")
    for event in bus.get_history():
        print(f"  - {event.type}: {event.data}")

    print(f"\n统计信息: {bus.get_stats()}")

    bus.stop()
    print("\n事件总线测试完成")
