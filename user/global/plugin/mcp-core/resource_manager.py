#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源管理器 - 统一管理线程池、观察者、钩子等资源

功能:
- 线程池生命周期管理
- 文件观察者管理
- 钩子函数注册与清理
- 资源泄漏检测
"""

import threading
import time
import weakref
from typing import Dict, List, Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta


class ResourceTracker:
    """资源追踪器"""
    
    def __init__(self):
        self._tracked_resources: Dict[str, List[dict]] = {}
        self._lock = threading.RLock()
    
    def track(self, resource_type: str, resource: Any, name: str = ""):
        """追踪资源"""
        with self._lock:
            if resource_type not in self._tracked_resources:
                self._tracked_resources[resource_type] = []
            
            self._tracked_resources[resource_type].append({
                'resource': weakref.ref(resource),
                'name': name,
                'created_at': datetime.now(),
                'access_count': 0
            })
    
    def untrack(self, resource_type: str, resource: Any):
        """停止追踪资源"""
        with self._lock:
            if resource_type not in self._tracked_resources:
                return
            
            resources = self._tracked_resources[resource_type]
            self._tracked_resources[resource_type] = [
                item for item in resources if item['resource']() is not resource
            ]
    
    def get_resource_count(self, resource_type: str) -> int:
        """获取资源数量"""
        with self._lock:
            return len(self._tracked_resources.get(resource_type, []))
    
    def get_resource_info(self, resource_type: str) -> List[dict]:
        """获取资源信息"""
        info = []
        with self._lock:
            for item in self._tracked_resources.get(resource_type, []):
                resource = item['resource']()
                if resource is not None:
                    info.append({
                        'name': item['name'],
                        'created_at': item['created_at'].isoformat(),
                        'age_minutes': (datetime.now() - item['created_at']).total_seconds() / 60,
                        'access_count': item['access_count']
                    })
        return info
    
    def cleanup_stale(self, max_age_minutes: int = 60):
        """清理过期资源"""
        with self._lock:
            for resource_type, resources in self._tracked_resources.items():
                fresh_resources = []
                for item in resources:
                    resource = item['resource']()
                    age = (datetime.now() - item['created_at']).total_seconds() / 60
                    if resource is None or age > max_age_minutes:
                        # 资源已被垃圾回收或过期
                        continue
                    fresh_resources.append(item)
                self._tracked_resources[resource_type] = fresh_resources


class ManagedThreadPoolExecutor(ThreadPoolExecutor):
    """带资源管理的线程池"""
    
    def __init__(self, max_workers: int = 4, name: str = ""):
        super().__init__(max_workers=max_workers)
        self._name = name
        self._created_at = datetime.now()
        self._task_count = 0
        self._shutdown_event = threading.Event()
        self._monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._monitor_thread.start()
        
        # 注册到资源追踪器
        _global_tracker.track('thread_pool', self, name)
    
    def submit(self, fn, *args, **kwargs):
        """提交任务"""
        self._task_count += 1
        return super().submit(fn, *args, **kwargs)
    
    def _monitor(self):
        """监控线程池状态"""
        while not self._shutdown_event.is_set():
            # 每30秒检查一次
            time.sleep(30)
    
    def shutdown(self, wait: bool = True):
        """关闭线程池"""
        self._shutdown_event.set()
        super().shutdown(wait=wait)
        _global_tracker.untrack('thread_pool', self)
    
    @property
    def stats(self):
        """获取线程池统计信息"""
        return {
            'name': self._name,
            'created_at': self._created_at.isoformat(),
            'max_workers': self._max_workers,
            'task_count': self._task_count,
            'active_threads': sum(1 for t in self._threads if t.is_alive())
        }


class HookManager:
    """钩子管理器"""
    
    def __init__(self, max_hooks_per_type: int = 100):
        self._hooks: Dict[str, List[dict]] = {}
        self._max_hooks = max_hooks_per_type
        self._lock = threading.RLock()
    
    def register(self, hook_type: str, callback: Callable, name: str = "", priority: int = 0):
        """注册钩子"""
        with self._lock:
            if hook_type not in self._hooks:
                self._hooks[hook_type] = []
            
            # 检查是否已注册
            for existing in self._hooks[hook_type]:
                if existing['callback'] is callback:
                    return False
            
            # 如果超过限制，移除最老的或优先级最低的
            if len(self._hooks[hook_type]) >= self._max_hooks:
                # 按优先级排序，移除优先级最低的
                self._hooks[hook_type].sort(key=lambda x: x['priority'], reverse=True)
                self._hooks[hook_type] = self._hooks[hook_type][:-1]
            
            self._hooks[hook_type].append({
                'callback': weakref.ref(callback),
                'name': name,
                'priority': priority,
                'registered_at': datetime.now(),
                'call_count': 0
            })
            
            return True
    
    def unregister(self, hook_type: str, callback: Callable):
        """注销钩子"""
        with self._lock:
            if hook_type not in self._hooks:
                return False
            
            hooks = self._hooks[hook_type]
            original_len = len(hooks)
            self._hooks[hook_type] = [
                item for item in hooks if item['callback']() is not callback
            ]
            return len(self._hooks[hook_type]) < original_len
    
    def execute(self, hook_type: str, *args, **kwargs):
        """执行钩子"""
        results = []
        with self._lock:
            if hook_type not in self._hooks:
                return results
            
            # 按优先级排序
            hooks = sorted(self._hooks[hook_type], key=lambda x: x['priority'], reverse=True)
            
            for item in hooks[:]:
                callback = item['callback']()
                if callback is None:
                    # 回调已被垃圾回收，移除
                    self._hooks[hook_type].remove(item)
                    continue
                
                try:
                    item['call_count'] += 1
                    result = callback(*args, **kwargs)
                    results.append({
                        'name': item['name'],
                        'success': True,
                        'result': result
                    })
                except Exception as e:
                    results.append({
                        'name': item['name'],
                        'success': False,
                        'error': str(e)
                    })
        
        return results
    
    def get_hook_count(self, hook_type: str = None) -> int:
        """获取钩子数量"""
        with self._lock:
            if hook_type:
                return len(self._hooks.get(hook_type, []))
            return sum(len(hooks) for hooks in self._hooks.values())
    
    def clear(self, hook_type: str = None):
        """清除钩子"""
        with self._lock:
            if hook_type:
                self._hooks[hook_type] = []
            else:
                self._hooks.clear()
    
    def get_hook_info(self, hook_type: str = None) -> Dict[str, List[dict]]:
        """获取钩子信息"""
        info = {}
        with self._lock:
            types = [hook_type] if hook_type else self._hooks.keys()
            
            for htype in types:
                if htype not in self._hooks:
                    continue
                
                info[htype] = []
                for item in self._hooks[htype]:
                    callback = item['callback']()
                    info[htype].append({
                        'name': item['name'],
                        'priority': item['priority'],
                        'registered_at': item['registered_at'].isoformat(),
                        'call_count': item['call_count'],
                        'active': callback is not None
                    })
        
        return info


class ObserverManager:
    """观察者管理器"""
    
    def __init__(self):
        self._observers: Dict[str, dict] = {}
        self._lock = threading.RLock()
    
    def register(self, observer_id: str, observer, callback: Callable):
        """注册观察者"""
        with self._lock:
            self._observers[observer_id] = {
                'observer': weakref.ref(observer),
                'callback': weakref.ref(callback),
                'registered_at': datetime.now(),
                'event_count': 0
            }
            _global_tracker.track('observer', observer, observer_id)
    
    def unregister(self, observer_id: str):
        """注销观察者"""
        with self._lock:
            if observer_id in self._observers:
                item = self._observers.pop(observer_id)
                observer = item['observer']()
                if observer:
                    _global_tracker.untrack('observer', observer)
                return True
        return False
    
    def notify(self, observer_id: str, *args, **kwargs):
        """通知观察者"""
        with self._lock:
            if observer_id not in self._observers:
                return False
            
            item = self._observers[observer_id]
            callback = item['callback']()
            
            if callback is None:
                # 回调已被垃圾回收
                del self._observers[observer_id]
                return False
            
            try:
                item['event_count'] += 1
                callback(*args, **kwargs)
                return True
            except Exception as e:
                return False
    
    def get_observer_count(self) -> int:
        """获取观察者数量"""
        with self._lock:
            return len(self._observers)
    
    def cleanup(self):
        """清理无效观察者"""
        with self._lock:
            stale_ids = []
            for observer_id, item in self._observers.items():
                observer = item['observer']()
                callback = item['callback']()
                
                if observer is None or callback is None:
                    stale_ids.append(observer_id)
            
            for observer_id in stale_ids:
                del self._observers[observer_id]
    
    def get_observer_info(self) -> List[dict]:
        """获取观察者信息"""
        info = []
        with self._lock:
            for observer_id, item in self._observers.items():
                observer = item['observer']()
                callback = item['callback']()
                info.append({
                    'id': observer_id,
                    'registered_at': item['registered_at'].isoformat(),
                    'event_count': item['event_count'],
                    'active': observer is not None and callback is not None
                })
        
        return info


# 全局资源追踪器
_global_tracker = ResourceTracker()


def get_resource_tracker() -> ResourceTracker:
    """获取全局资源追踪器"""
    return _global_tracker


def create_thread_pool(max_workers: int = 4, name: str = "") -> ManagedThreadPoolExecutor:
    """创建带管理的线程池"""
    return ManagedThreadPoolExecutor(max_workers=max_workers, name=name)


# 示例用法
if __name__ == "__main__":
    # 创建资源管理器
    hook_manager = HookManager()
    observer_manager = ObserverManager()
    
    # 注册钩子
    def on_event(data):
        print(f"事件触发: {data}")
    
    hook_manager.register('test_event', on_event, 'test_hook', priority=10)
    
    # 执行钩子
    results = hook_manager.execute('test_event', {'key': 'value'})
    print(f"钩子执行结果: {results}")
    
    # 获取状态
    print(f"\n钩子数量: {hook_manager.get_hook_count()}")
    print(f"钩子信息: {hook_manager.get_hook_info()}")
    
    # 创建线程池
    pool = create_thread_pool(max_workers=2, name='test_pool')
    print(f"\n线程池统计: {pool.stats}")
    
    # 获取资源追踪器状态
    tracker = get_resource_tracker()
    print(f"\n线程池数量: {tracker.get_resource_count('thread_pool')}")
    print(f"观察者数量: {tracker.get_resource_count('observer')}")
    
    # 清理
    hook_manager.clear()
    pool.shutdown()
    
    print("\n资源管理测试完成")