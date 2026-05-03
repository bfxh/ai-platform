#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 扩展功能系统

功能:
- 速率限制管理
- 批量操作
- 数据处理
- 分析工具
- 智能调度
- 错误处理
- 数据可视化
"""

import json
import os
import time
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

import requests

import sys
# 导入技能基类
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill


class GitHubExtended(Skill):
    """GitHub扩展功能技能"""

    name = "github_extended"
    description = "GitHub扩展功能系统 - 速率限制管理、批量操作、数据处理、分析工具"
    version = "1.1.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.api_cache_file = self.config.get("api_cache_file", "/python/GitHub/github_apis_smart_export.json")
        self.data_dir = self.config.get("data_dir", "/python/GitHub/data")
        self.analysis_dir = self.config.get("analysis_dir", "/python/GitHub/analysis")
        self.rate_limit_file = self.config.get("rate_limit_file", "/python/GitHub/rate_limit.json")
        self.api_endpoints = []
        self.rate_limit_info = {}
        self._session = requests.Session()
        self._rate_limit_semaphore = None
        self._ensure_directories()
        self._load_api_data()
        self._load_rate_limit_info()


    def close(self):
        """Close requests session to free connections"""
        self._session.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _log(self, message: str, level: str = "info"):
        """简单的日志方法"""
        print(f"[GitHubExtended] [{level.upper()}] {message}")

    def execute(self, action: str, params: Dict) -> Dict:
        """执行技能

        支持的动作:
        - rate_limit_management: 速率限制管理
            子动作: check, wait, optimize
        - batch_operation: 批量操作
        - data_processing: 数据处理
            子动作: transform, validate, clean, aggregate
        - analysis: 分析
        - intelligent_scheduling: 智能调度
        - error_handling: 错误处理
        - data_visualization: 数据可视化
        """
        sub_action = params.get("sub_action", params.get("action", ""))

        if action == "rate_limit_management":
            return self._rate_limit_management(params, sub_action)
        elif action == "batch_operation":
            return self._batch_operation(params)
        elif action == "data_processing":
            return self._data_processing(params, sub_action)
        elif action == "analysis":
            return self._analysis(params)
        elif action == "intelligent_scheduling":
            return self._intelligent_scheduling(params)
        elif action == "error_handling":
            return self._error_handling(params)
        elif action == "data_visualization":
            return self._data_visualization(params)
        else:
            return {
                "success": False,
                "error": f"未知动作: {action}"
            }

    def _ensure_directories(self):
        """确保目录存在"""
        directories = [
            self.data_dir,
            self.analysis_dir,
            Path(self.data_dir) / "raw",
            Path(self.data_dir) / "processed",
            Path(self.analysis_dir) / "reports",
            Path(self.analysis_dir) / "visualizations"
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            self._log(f"确保目录存在: {directory}")

    def _load_api_data(self):
        """加载API数据"""
        try:
            if os.path.exists(self.api_cache_file):
                with open(self.api_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.api_endpoints = data.get("endpoints", [])
                    self._log(f"加载了 {len(self.api_endpoints)} 个API端点")
            else:
                self._log(f"API缓存文件不存在: {self.api_cache_file}")
                self.api_endpoints = []
        except Exception as e:
            self._log(f"加载API数据失败: {e}", "error")
            self.api_endpoints = []

    def _load_rate_limit_info(self):
        """加载速率限制信息"""
        try:
            if os.path.exists(self.rate_limit_file):
                with open(self.rate_limit_file, "r", encoding="utf-8") as f:
                    self.rate_limit_info = json.load(f)
                    self._log("加载速率限制信息")
            else:
                self._update_rate_limit_info()
        except Exception as e:
            self._log(f"加载速率限制信息失败: {e}", "error")
            self.rate_limit_info = {}

    def _update_rate_limit_info(self):
        """更新速率限制信息"""
        try:
            response = self._session.get(
                "https://api.github.com/rate_limit",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "GitHubExtended/1.0"
                }
            )

            if response.status_code == 200:
                self.rate_limit_info = response.json()
                self._save_rate_limit_info()
                self._log("速率限制信息已更新")
            else:
                self._log(f"更新速率限制信息失败: {response.status_code}", "error")

        except Exception as e:
            self._log(f"更新速率限制信息异常: {e}", "error")

    def _save_rate_limit_info(self):
        """保存速率限制信息"""
        try:
            with open(self.rate_limit_file, "w", encoding="utf-8") as f:
                json.dump(self.rate_limit_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"保存速率限制信息失败: {e}", "error")

    def _rate_limit_management(self, params: Dict, sub_action: str = "") -> Dict:
        """速率限制管理

        子动作:
        - check: 检查速率限制（默认）
        - wait: 等待速率限制重置
        - optimize: 优化速率限制使用
        """
        action = sub_action or params.get("action", "check")

        if action == "check":
            self._update_rate_limit_info()
            return {
                "success": True,
                "rate_limit": self.rate_limit_info
            }
        elif action == "wait":
            wait_time = params.get("wait_time", params.get("wait", 60))
            self._log(f"等待速率限制重置: {wait_time} 秒")
            time.sleep(wait_time)
            return {
                "success": True,
                "message": f"等待 {wait_time} 秒完成"
            }
        elif action == "optimize":
            optimization = self._optimize_rate_limit()
            return {
                "success": True,
                "optimization": optimization
            }
        else:
            return {
                "success": False,
                "error": f"未知的速率限制操作: {action}"
            }

    def _optimize_rate_limit(self) -> Dict:
        """优化速率限制使用"""
        core = self.rate_limit_info.get("resources", {}).get("core", {})
        search = self.rate_limit_info.get("resources", {}).get("search", {})
        graphql = self.rate_limit_info.get("resources", {}).get("graphql", {})

        optimization = {
            "current_status": {
                "core": {
                    "remaining": core.get("remaining", 0),
                    "limit": core.get("limit", 0),
                    "reset": core.get("reset", 0)
                },
                "search": {
                    "remaining": search.get("remaining", 0),
                    "limit": search.get("limit", 0),
                    "reset": search.get("reset", 0)
                },
                "graphql": {
                    "remaining": graphql.get("remaining", 0),
                    "limit": graphql.get("limit", 0),
                    "reset": graphql.get("reset", 0)
                }
            },
            "recommendations": []
        }

        if core.get("remaining", 0) < 100:
            optimization["recommendations"].append({
                "type": "core",
                "message": "Core API剩余请求数较低，建议批量操作以节省请求"
            })

        if search.get("remaining", 0) < 50:
            optimization["recommendations"].append({
                "type": "search",
                "message": "Search API剩余请求数较低，建议减少搜索频率"
            })

        return optimization

    def _batch_operation(self, params: Dict) -> Dict:
        """批量操作"""
        operations = params.get("operations", [])
        concurrency = params.get("concurrency", 5)

        if not operations:
            return {
                "success": False,
                "error": "缺少operations参数"
            }

        self._log(f"开始批量操作: {len(operations)} 个操作, 并发度: {concurrency}")

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_op = {executor.submit(self._execute_single_operation, op): op for op in operations}

            for future in concurrent.futures.as_completed(future_to_op):
                op = future_to_op[future]
                try:
                    result = future.result()
                    results.append({
                        "operation": op,
                        "result": result,
                        "success": True
                    })
                except Exception as e:
                    results.append({
                        "operation": op,
                        "error": str(e),
                        "success": False
                    })

        success_count = sum(1 for r in results if r.get("success"))
        return {
            "success": True,
            "results": results,
            "summary": {
                "total": len(operations),
                "success": success_count,
                "failure": len(operations) - success_count
            }
        }

    def _execute_single_operation(self, operation: Dict) -> Dict:
        """执行单个操作"""
        endpoint = operation.get("endpoint")
        method = operation.get("method", "GET")

        if not endpoint:
            raise ValueError("缺少endpoint参数")

        try:
            if method == "GET":
                response = self._session.get(
                    f"https://api.github.com{endpoint}",
                    headers={
                        "Accept": "application/vnd.github.v3+json",
                        "User-Agent": "GitHubExtended/1.0"
                    }
                )
            elif method == "POST":
                response = self._session.post(
                    f"https://api.github.com{endpoint}",
                    json=operation.get("data", {}),
                    headers={
                        "Accept": "application/vnd.github.v3+json",
                        "User-Agent": "GitHubExtended/1.0"
                    }
                )
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            return {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text
            }

        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")

    def _data_processing(self, params: Dict, sub_action: str = "") -> Dict:
        """数据处理

        子动作:
        - transform: 数据转换（默认）
        - validate: 数据验证
        - clean: 数据清洗
        - aggregate: 数据聚合
        """
        action = sub_action or params.get("action", "transform")
        data = params.get("data", [])
        transform_rules = params.get("transform_rules", {})

        if not data:
            return {
                "success": False,
                "error": "缺少data参数"
            }

        if action == "transform":
            return self._transform_data(data, transform_rules)
        elif action == "validate":
            return self._validate_data(data, params.get("validation_rules", {}))
        elif action == "clean":
            return self._clean_data(data)
        elif action == "aggregate":
            return self._aggregate_data(data, params.get("group_by", []))
        else:
            return {
                "success": False,
                "error": f"不支持的数据处理操作: {action}"
            }

    def _transform_data(self, data: List[Dict], transform_rules: Dict) -> Dict:
        """数据转换"""
        transformed = []

        for item in data:
            new_item = {}
            for key, value in item.items():
                new_key = transform_rules.get(key, key)
                new_item[new_key] = value
            transformed.append(new_item)

        return {
            "success": True,
            "transformed_data": transformed,
            "count": len(transformed)
        }

    def _validate_data(self, data: List[Dict], validation_rules: Dict) -> Dict:
        """数据验证"""
        validated = []
        errors = []

        for i, item in enumerate(data):
            item_errors = []
            for field, rules in validation_rules.items():
                if rules.get("required") and field not in item:
                    item_errors.append(f"缺少必填字段: {field}")

                if field in item:
                    value = item[field]
                    if "type" in rules and not isinstance(value, {"str": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict, "str|int": (str, int)}.get(rules["type"], type(None))):
                        item_errors.append(f"字段 {field} 类型错误")

            if item_errors:
                errors.append({"index": i, "errors": item_errors})
            else:
                validated.append(item)

        return {
            "success": True,
            "validated_data": validated,
            "valid_count": len(validated),
            "invalid_count": len(errors),
            "errors": errors
        }

    def _clean_data(self, data: List[Dict]) -> Dict:
        """数据清洗"""
        cleaned = []

        for item in data:
            cleaned_item = {k: v for k, v in item.items() if v is not None}
            cleaned_item = {k: v.strip() if isinstance(v, str) else v for k, v in cleaned_item.items()}
            cleaned.append(cleaned_item)

        return {
            "success": True,
            "cleaned_data": cleaned,
            "count": len(cleaned)
        }

    def _aggregate_data(self, data: List[Dict], group_by: List[str]) -> Dict:
        """数据聚合"""
        aggregated = {}

        for item in data:
            key_parts = []
            for field in group_by:
                key_parts.append(str(item.get(field, "unknown")))

            key = "|".join(key_parts)

            if key not in aggregated:
                aggregated[key] = {
                    "items": [],
                    "count": 0
                }

            aggregated[key]["items"].append(item)
            aggregated[key]["count"] += 1

        return {
            "success": True,
            "aggregated_data": aggregated,
            "group_count": len(aggregated)
        }

    def _analysis(self, params: Dict) -> Dict:
        """分析工具"""
        analysis_type = params.get("analysis_type", "api_usage")
        data = params.get("data", [])

        if analysis_type == "api_usage":
            return self._analyze_api_usage(data)
        elif analysis_type == "performance":
            return self._analyze_performance(data)
        elif analysis_type == "error_rate":
            return self._analyze_error_rate(data)
        else:
            return {
                "success": False,
                "error": f"不支持的分析类型: {analysis_type}"
            }

    def _analyze_api_usage(self, data: List[Dict]) -> Dict:
        """分析API使用情况"""
        endpoint_stats = {}

        for item in data:
            endpoint = item.get("operation", {}).get("endpoint", "unknown")
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    "count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "total_duration": 0
                }

            endpoint_stats[endpoint]["count"] += 1

            if item.get("success"):
                endpoint_stats[endpoint]["success_count"] += 1
            else:
                endpoint_stats[endpoint]["failure_count"] += 1

            result = item.get("result", {})
            if isinstance(result, dict) and "duration" in result:
                endpoint_stats[endpoint]["total_duration"] += result["duration"]

        return {
            "success": True,
            "analysis_type": "api_usage",
            "endpoint_stats": endpoint_stats,
            "total_requests": len(data)
        }

    def _analyze_performance(self, data: List[Dict]) -> Dict:
        """分析性能"""
        durations = []

        for item in data:
            result = item.get("result", {})
            if isinstance(result, dict) and "duration" in result:
                durations.append(result["duration"])

        if not durations:
            return {
                "success": True,
                "analysis_type": "performance",
                "message": "没有足够的性能数据"
            }

        durations.sort()
        return {
            "success": True,
            "analysis_type": "performance",
            "min": min(durations) if durations else 0,
            "max": max(durations) if durations else 0,
            "avg": sum(durations) / len(durations) if durations else 0,
            "median": durations[len(durations) // 2] if durations else 0,
            "count": len(durations)
        }

    def _analyze_error_rate(self, data: List[Dict]) -> Dict:
        """分析错误率"""
        total = len(data)
        success_count = sum(1 for item in data if item.get("success"))
        failure_count = total - success_count

        error_types = {}
        for item in data:
            if not item.get("success"):
                error = item.get("error", "unknown")
                error_types[error] = error_types.get(error, 0) + 1

        return {
            "success": True,
            "analysis_type": "error_rate",
            "total": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "error_rate": failure_count / total if total > 0 else 0,
            "error_types": error_types
        }

    def _intelligent_scheduling(self, params: Dict) -> Dict:
        """智能调度"""
        tasks = params.get("tasks", [])

        if not tasks:
            return {
                "success": False,
                "error": "缺少tasks参数"
            }

        scheduled_tasks = []
        current_time = time.time()

        for i, task in enumerate(tasks):
            priority = task.get("priority", 5)
            delay = (10 - priority) * 10

            scheduled_tasks.append({
                "task": task,
                "scheduled_time": current_time + delay,
                "priority": priority
            })

        scheduled_tasks.sort(key=lambda x: x["scheduled_time"])

        return {
            "success": True,
            "scheduled_tasks": scheduled_tasks,
            "count": len(scheduled_tasks)
        }

    def _error_handling(self, params: Dict) -> Dict:
        """错误处理"""
        errors = params.get("errors", [])

        if not errors:
            return {
                "success": False,
                "error": "缺少errors参数"
            }

        error_summary = {}
        for error in errors:
            error_key = error.get("error", "unknown")
            if error_key not in error_summary:
                error_summary[error_key] = {
                    "count": 0,
                    "first_occurrence": error.get("timestamp"),
                    "last_occurrence": error.get("timestamp")
                }

            error_summary[error_key]["count"] += 1

        return {
            "success": True,
            "error_summary": error_summary,
            "total_errors": len(errors)
        }

    def _data_visualization(self, params: Dict) -> Dict:
        """数据可视化"""
        viz_type = params.get("visualization_type", "api_usage")
        data = params.get("data", [])

        visualization_data = {
            "type": viz_type,
            "timestamp": datetime.now().isoformat(),
            "data_points": len(data)
        }

        if viz_type == "api_usage":
            endpoint_counts = {}
            for item in data:
                endpoint = item.get("operation", {}).get("endpoint", "unknown")
                endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

            visualization_data["endpoints"] = endpoint_counts

        elif viz_type == "performance":
            durations = [item.get("result", {}).get("duration", 0) for item in data if isinstance(item.get("result"), dict)]
            visualization_data["durations"] = durations
            visualization_data["avg_duration"] = sum(durations) / len(durations) if durations else 0

        elif viz_type == "error_rate":
            total = len(data)
            success = sum(1 for item in data if item.get("success"))
            visualization_data["success_rate"] = success / total if total > 0 else 0
            visualization_data["error_rate"] = (total - success) / total if total > 0 else 0

        return {
            "success": True,
            "visualization": visualization_data
        }


skill = GitHubExtended()
