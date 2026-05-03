#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控模块
用于监控技能执行性能和分析瓶颈
"""

import functools
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """性能指标数据类"""

    function_name: str
    skill_name: str
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "function_name": self.function_name,
            "skill_name": self.skill_name,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error_message": self.error_message,
        }


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.enabled = True
        self.max_metrics = 10000  # 最大保存的指标数量

    def record_metric(self, metric: PerformanceMetric):
        """记录性能指标"""
        if not self.enabled:
            return

        self.metrics.append(metric)

        # 限制指标数量
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics :]

        # 记录慢操作
        if metric.execution_time > 1.0:  # 超过1秒认为是慢操作
            logger.warning(
                f"慢操作检测: {metric.skill_name}.{metric.function_name} "
                f"耗时 {metric.execution_time:.3f}s"
            )

    def get_metrics(self, skill_name: Optional[str] = None) -> List[PerformanceMetric]:
        """获取性能指标"""
        if skill_name:
            return [m for m in self.metrics if m.skill_name == skill_name]
        return self.metrics.copy()

    def get_average_time(self, skill_name: Optional[str] = None) -> float:
        """获取平均执行时间"""
        metrics = self.get_metrics(skill_name)
        if not metrics:
            return 0.0
        return sum(m.execution_time for m in metrics) / len(metrics)

    def get_slowest_operations(self, limit: int = 10) -> List[PerformanceMetric]:
        """获取最慢的操作"""
        sorted_metrics = sorted(self.metrics, key=lambda x: x.execution_time, reverse=True)
        return sorted_metrics[:limit]

    def get_skill_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取技能统计信息"""
        stats = defaultdict(
            lambda: {
                "count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "success_count": 0,
                "error_count": 0,
            }
        )

        for metric in self.metrics:
            skill_stats = stats[metric.skill_name]
            skill_stats["count"] += 1
            skill_stats["total_time"] += metric.execution_time
            if metric.success:
                skill_stats["success_count"] += 1
            else:
                skill_stats["error_count"] += 1

        # 计算平均值
        for skill_name, skill_stats in stats.items():
            if skill_stats["count"] > 0:
                skill_stats["avg_time"] = skill_stats["total_time"] / skill_stats["count"]

        return dict(stats)

    def export_metrics(self, file_path: str):
        """导出指标到文件"""
        data = {
            "export_time": datetime.now().isoformat(),
            "total_metrics": len(self.metrics),
            "metrics": [m.to_dict() for m in self.metrics],
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"性能指标已导出到: {file_path}")

    def clear_metrics(self):
        """清空指标"""
        self.metrics.clear()
        logger.info("性能指标已清空")


# 全局性能监控器实例
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    return _performance_monitor


def monitor_performance(skill_name: Optional[str] = None):
    """性能监控装饰器"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error_message = None
            success = True

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                execution_time = time.time() - start_time

                # 获取技能名称
                actual_skill_name = skill_name
                if actual_skill_name is None and args:
                    # 尝试从 self 获取技能名称
                    self_obj = args[0]
                    if hasattr(self_obj, "name"):
                        actual_skill_name = self_obj.name

                if actual_skill_name is None:
                    actual_skill_name = "unknown"

                # 记录性能指标
                metric = PerformanceMetric(
                    function_name=func.__name__,
                    skill_name=actual_skill_name,
                    execution_time=execution_time,
                    success=success,
                    error_message=error_message,
                )

                _performance_monitor.record_metric(metric)

        return wrapper

    return decorator


class PerformanceProfiler:
    """性能分析器"""

    def __init__(self):
        self.monitor = get_performance_monitor()

    def analyze_bottlenecks(self) -> List[Dict[str, Any]]:
        """分析性能瓶颈"""
        bottlenecks = []

        # 获取统计信息
        stats = self.monitor.get_skill_statistics()

        for skill_name, skill_stats in stats.items():
            # 识别慢技能（平均执行时间超过1秒）
            if skill_stats["avg_time"] > 1.0:
                bottlenecks.append(
                    {
                        "type": "slow_skill",
                        "skill_name": skill_name,
                        "avg_time": skill_stats["avg_time"],
                        "recommendation": "考虑优化技能执行逻辑或添加缓存",
                    }
                )

            # 识别高错误率技能（错误率超过10%）
            if skill_stats["count"] > 0:
                error_rate = skill_stats["error_count"] / skill_stats["count"]
                if error_rate > 0.1:
                    bottlenecks.append(
                        {
                            "type": "high_error_rate",
                            "skill_name": skill_name,
                            "error_rate": error_rate,
                            "recommendation": "检查错误处理逻辑和输入验证",
                        }
                    )

        # 获取最慢的操作
        slowest_ops = self.monitor.get_slowest_operations(5)
        for op in slowest_ops:
            if op.execution_time > 0.5:  # 超过0.5秒
                bottlenecks.append(
                    {
                        "type": "slow_operation",
                        "skill_name": op.skill_name,
                        "function": op.function_name,
                        "execution_time": op.execution_time,
                        "recommendation": "优化此特定操作的性能",
                    }
                )

        return bottlenecks

    def generate_report(self) -> str:
        """生成性能报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("性能监控报告")
        lines.append("=" * 60)
        lines.append("")

        # 总体统计
        lines.append("总体统计:")
        lines.append(f"  总指标数: {len(self.monitor.metrics)}")
        lines.append(f"  平均执行时间: {self.monitor.get_average_time():.3f}s")
        lines.append("")

        # 技能统计
        lines.append("技能统计:")
        stats = self.monitor.get_skill_statistics()
        for skill_name, skill_stats in sorted(
            stats.items(), key=lambda x: x[1]["avg_time"], reverse=True
        ):
            lines.append(f"  {skill_name}:")
            lines.append(f"    调用次数: {skill_stats['count']}")
            lines.append(f"    平均时间: {skill_stats['avg_time']:.3f}s")
            lines.append(
                f"    成功率: {(skill_stats['success_count'] / skill_stats['count'] * 100):.1f}%"
                if skill_stats["count"] > 0
                else "    成功率: N/A"
            )
        lines.append("")

        # 瓶颈分析
        lines.append("性能瓶颈:")
        bottlenecks = self.analyze_bottlenecks()
        if bottlenecks:
            for bottleneck in bottlenecks:
                lines.append(f"  [{bottleneck['type']}] {bottleneck.get('skill_name', 'N/A')}")
                if "function" in bottleneck:
                    lines.append(f"    函数: {bottleneck['function']}")
                if "avg_time" in bottleneck:
                    lines.append(f"    平均时间: {bottleneck['avg_time']:.3f}s")
                if "error_rate" in bottleneck:
                    lines.append(f"    错误率: {bottleneck['error_rate']:.1%}")
                if "execution_time" in bottleneck:
                    lines.append(f"    执行时间: {bottleneck['execution_time']:.3f}s")
                lines.append(f"    建议: {bottleneck['recommendation']}")
                lines.append("")
        else:
            lines.append("  未发现明显性能瓶颈")

        lines.append("=" * 60)

        return "\n".join(lines)


if __name__ == "__main__":
    # 测试性能监控
    monitor = get_performance_monitor()

    # 模拟一些性能指标
    for i in range(10):
        metric = PerformanceMetric(
            function_name=f"test_function_{i}",
            skill_name="test_skill",
            execution_time=0.1 * (i + 1),
            success=True,
        )
        monitor.record_metric(metric)

    # 生成报告
    profiler = PerformanceProfiler()
    print(profiler.generate_report())

    # 导出指标
    monitor.export_metrics("performance_metrics.json")
