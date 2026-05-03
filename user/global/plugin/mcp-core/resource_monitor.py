#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 资源监控工具

功能:
- 实时监控线程池、钩子、观察者等资源
- 资源泄漏检测
- 资源使用报告生成
"""

import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime
import json

# 导入资源管理器
from resource_manager import get_resource_tracker, ManagedThreadPoolExecutor, HookManager, ObserverManager


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self._tracker = get_resource_tracker()
        self._running = False
        self._monitor_thread = None
        self._report_interval = 60  # 报告间隔（秒）
        self._alerts = []
        self._alert_thresholds = {
            'thread_pool_max_workers': 20,
            'hook_max_per_type': 100,
            'observer_max': 50,
            'event_history_max': 5000
        }
    
    def start(self):
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        print("[ResourceMonitor] 资源监控器已启动")
    
    def stop(self):
        """停止监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join()
        print("[ResourceMonitor] 资源监控器已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        last_report_time = time.time()
        
        while self._running:
            # 定期生成报告
            if time.time() - last_report_time >= self._report_interval:
                self._generate_report()
                last_report_time = time.time()
            
            # 检查告警
            self._check_alerts()
            
            time.sleep(1)
    
    def _check_alerts(self):
        """检查资源使用是否超过阈值"""
        current_time = datetime.now().isoformat()
        new_alerts = []
        
        # 检查线程池
        thread_pools = self._tracker.get_resource_info('thread_pool')
        for pool in thread_pools:
            if pool.get('age_minutes', 0) > 60:
                new_alerts.append({
                    'time': current_time,
                    'level': 'WARNING',
                    'type': 'thread_pool',
                    'message': f"线程池 '{pool.get('name', 'unknown')}' 运行时间超过1小时",
                    'details': pool
                })
        
        # 检查观察者
        observer_count = self._tracker.get_resource_count('observer')
        if observer_count > self._alert_thresholds['observer_max']:
            new_alerts.append({
                'time': current_time,
                'level': 'WARNING',
                'type': 'observer',
                'message': f"观察者数量过多: {observer_count} (阈值: {self._alert_thresholds['observer_max']})",
                'details': {'count': observer_count}
            })
        
        # 更新告警列表（保留最近50条）
        self._alerts.extend(new_alerts)
        if len(self._alerts) > 50:
            self._alerts = self._alerts[-50:]
        
        # 输出新告警
        for alert in new_alerts:
            print(f"[ALERT] [{alert['level']}] {alert['message']}")
    
    def _generate_report(self):
        """生成资源使用报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'resources': {
                'thread_pools': {
                    'count': self._tracker.get_resource_count('thread_pool'),
                    'details': self._tracker.get_resource_info('thread_pool')
                },
                'observers': {
                    'count': self._tracker.get_resource_count('observer'),
                    'details': []
                },
                'event_buses': {
                    'count': self._tracker.get_resource_count('event_bus'),
                    'details': self._tracker.get_resource_info('event_bus')
                },
                'workflow_engines': {
                    'count': self._tracker.get_resource_count('workflow_engine'),
                    'details': self._tracker.get_resource_info('workflow_engine')
                },
                'skill_registries': {
                    'count': self._tracker.get_resource_count('skill_registry'),
                    'details': self._tracker.get_resource_info('skill_registry')
                },
                'config_managers': {
                    'count': self._tracker.get_resource_count('config_manager'),
                    'details': self._tracker.get_resource_info('config_manager')
                }
            },
            'alerts': self._alerts[-10:]  # 最近10条告警
        }
        
        # 打印报告摘要
        self._print_report_summary(report)
        
        return report
    
    def _print_report_summary(self, report: Dict):
        """打印报告摘要"""
        print("\n" + "="*60)
        print(f"资源使用报告 - {report['timestamp']}")
        print("="*60)
        
        for resource_type, data in report['resources'].items():
            print(f"{resource_type}: {data['count']}")
            if data['details']:
                for detail in data['details'][:3]:  # 只显示前3个详情
                    name = detail.get('name', 'unknown')
                    age = detail.get('age_minutes', 0)
                    print(f"  - {name} (运行 {age:.1f} 分钟)")
        
        if report['alerts']:
            print("\n最近告警:")
            for alert in report['alerts']:
                print(f"  [{alert['time']}] [{alert['level']}] {alert['message']}")
        
        print("="*60 + "\n")
    
    def get_report(self) -> Dict:
        """获取当前资源报告"""
        return self._generate_report()
    
    def get_alerts(self, level: str = None) -> list:
        """获取告警列表"""
        if level:
            return [a for a in self._alerts if a['level'] == level]
        return self._alerts
    
    def clear_alerts(self):
        """清空告警"""
        self._alerts.clear()
    
    def cleanup_stale_resources(self, max_age_minutes: int = 60):
        """清理过期资源"""
        self._tracker.cleanup_stale(max_age_minutes)
        print(f"[ResourceMonitor] 已清理运行超过 {max_age_minutes} 分钟的过期资源")
    
    def set_alert_threshold(self, threshold_name: str, value: int):
        """设置告警阈值"""
        if threshold_name in self._alert_thresholds:
            self._alert_thresholds[threshold_name] = value
            return True
        return False
    
    def get_alert_thresholds(self) -> Dict:
        """获取当前告警阈值"""
        return self._alert_thresholds.copy()


# 全局资源监控器实例
_monitor_instance = None


def get_monitor() -> ResourceMonitor:
    """获取全局资源监控器"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ResourceMonitor()
    return _monitor_instance


if __name__ == '__main__':
    # 测试资源监控器
    monitor = get_monitor()
    
    print("资源监控器测试")
    
    # 启动监控
    monitor.start()
    
    # 模拟一些资源使用
    from resource_manager import create_thread_pool
    
    # 创建线程池
    pool1 = create_thread_pool(max_workers=2, name='test_pool_1')
    pool2 = create_thread_pool(max_workers=3, name='test_pool_2')
    
    # 提交一些任务
    def test_task():
        time.sleep(1)
        return "done"
    
    pool1.submit(test_task)
    pool2.submit(test_task)
    
    # 获取报告
    print("\n生成资源报告...")
    report = monitor.get_report()
    
    # 打印完整报告
    print("\n完整报告:")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    
    # 清理
    pool1.shutdown()
    pool2.shutdown()
    
    # 停止监控
    time.sleep(2)
    monitor.stop()
    
    print("\n资源监控器测试完成")