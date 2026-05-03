#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控模块

监控CPU、内存、GPU使用情况

用法:
    from system_monitor import SystemMonitor
    
    monitor = SystemMonitor()
    metrics = monitor.collect_metrics()
    print(metrics)
"""

import psutil
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import json

# 尝试导入GPUtil
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

from logging_config import setup_logger

logger = setup_logger("system_monitor")

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.metrics_history: List[Dict] = []
        self.alerts: List[Dict] = []
    
    def collect_metrics(self) -> Dict[str, Any]:
        """
        收集系统指标
        
        Returns:
            系统指标字典
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": self._get_cpu_metrics(),
            "memory": self._get_memory_metrics(),
            "disk": self._get_disk_metrics(),
            "gpu": self._get_gpu_metrics() if GPU_AVAILABLE else None
        }
        
        # 保存到历史
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.history_size:
            self.metrics_history = self.metrics_history[-self.history_size:]
        
        return metrics
    
    def _get_cpu_metrics(self) -> Dict:
        """获取CPU指标"""
        return {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
    
    def _get_memory_metrics(self) -> Dict:
        """获取内存指标"""
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / 1024**3, 2),
            "available_gb": round(mem.available / 1024**3, 2),
            "percent": mem.percent,
            "used_gb": round(mem.used / 1024**3, 2)
        }
    
    def _get_disk_metrics(self) -> Dict:
        """获取磁盘指标"""
        disk = psutil.disk_usage('D:/')
        return {
            "total_gb": round(disk.total / 1024**3, 2),
            "free_gb": round(disk.free / 1024**3, 2),
            "percent": disk.percent
        }
    
    def _get_gpu_metrics(self) -> List[Dict]:
        """获取GPU指标"""
        if not GPU_AVAILABLE:
            return []
        
        gpus = GPUtil.getGPUs()
        return [
            {
                "id": gpu.id,
                "name": gpu.name,
                "load_percent": round(gpu.load * 100, 2),
                "memory_used_mb": gpu.memoryUsed,
                "memory_total_mb": gpu.memoryTotal,
                "memory_percent": round(gpu.memoryUsed / gpu.memoryTotal * 100, 2),
                "temperature": gpu.temperature
            }
            for gpu in gpus
        ]
    
    def check_alerts(self, metrics: Dict) -> List[Dict]:
        """
        检查告警
        
        Args:
            metrics: 系统指标
        
        Returns:
            告警列表
        """
        alerts = []
        
        # CPU告警
        cpu_percent = metrics["cpu"]["percent"]
        if cpu_percent > 90:
            alerts.append({
                "level": "critical",
                "type": "cpu",
                "message": f"CPU usage critical: {cpu_percent}%",
                "timestamp": datetime.now().isoformat()
            })
        elif cpu_percent > 75:
            alerts.append({
                "level": "warning",
                "type": "cpu",
                "message": f"CPU usage high: {cpu_percent}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # 内存告警
        mem_percent = metrics["memory"]["percent"]
        if mem_percent > 90:
            alerts.append({
                "level": "critical",
                "type": "memory",
                "message": f"Memory usage critical: {mem_percent}%",
                "timestamp": datetime.now().isoformat()
            })
        elif mem_percent > 80:
            alerts.append({
                "level": "warning",
                "type": "memory",
                "message": f"Memory usage high: {mem_percent}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # 磁盘告警
        disk_percent = metrics["disk"]["percent"]
        if disk_percent > 90:
            alerts.append({
                "level": "critical",
                "type": "disk",
                "message": f"Disk usage critical: {disk_percent}%",
                "timestamp": datetime.now().isoformat()
            })
        elif disk_percent > 80:
            alerts.append({
                "level": "warning",
                "type": "disk",
                "message": f"Disk usage high: {disk_percent}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # GPU告警
        if metrics["gpu"]:
            for gpu in metrics["gpu"]:
                if gpu["memory_percent"] > 90:
                    alerts.append({
                        "level": "critical",
                        "type": "gpu",
                        "device": gpu["name"],
                        "message": f"GPU memory critical: {gpu['memory_percent']}%",
                        "timestamp": datetime.now().isoformat()
                    })
                elif gpu["temperature"] > 85:
                    alerts.append({
                        "level": "warning",
                        "type": "gpu",
                        "device": gpu["name"],
                        "message": f"GPU temperature high: {gpu['temperature']}°C",
                        "timestamp": datetime.now().isoformat()
                    })
        
        self.alerts.extend(alerts)
        # 只保留最近100条告警
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        return alerts
    
    def save_metrics(self, filepath: str = "/python/Logs/metrics.json"):
        """保存指标到文件"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.metrics_history, f, indent=2)
        
        logger.info(f"Metrics saved to {filepath}")
    
    def get_summary(self) -> Dict:
        """获取汇总信息"""
        if not self.metrics_history:
            return {}
        
        latest = self.metrics_history[-1]
        
        return {
            "latest": latest,
            "history_count": len(self.metrics_history),
            "alert_count": len(self.alerts),
            "alerts": self.alerts[-10:]  # 最近10条告警
        }

# 使用示例
if __name__ == "__main__":
    monitor = SystemMonitor()
    
    # 收集指标
    metrics = monitor.collect_metrics()
    print("=" * 50)
    print("System Metrics")
    print("=" * 50)
    print(f"CPU: {metrics['cpu']['percent']}%")
    print(f"Memory: {metrics['memory']['percent']}%")
    print(f"Disk: {metrics['disk']['percent']}%")
    
    if metrics['gpu']:
        for gpu in metrics['gpu']:
            print(f"GPU {gpu['name']}: {gpu['load_percent']}% load, {gpu['memory_percent']}% memory")
    
    # 检查告警
    alerts = monitor.check_alerts(metrics)
    if alerts:
        print("\n⚠️ Alerts:")
        for alert in alerts:
            print(f"[{alert['level'].upper()}] {alert['message']}")
    else:
        print("\n✅ No alerts")
