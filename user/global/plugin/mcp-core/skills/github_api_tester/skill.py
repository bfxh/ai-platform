#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级GitHub API测试工具

功能:
- 批量API测试
- 实时调试
- 测试报告生成
- 性能测试
- 并发测试
- 错误处理测试
- 速率限制测试
- 认证测试
"""

import json
import os
import time
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

import sys
# 导入技能基类
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill


class GitHubAPITester(Skill):
    """GitHub API测试技能"""

    name = "github_api_tester"
    description = "高级GitHub API测试工具 - 批量测试、实时调试、性能测试"
    version = "1.0.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.api_cache_file = self.config.get("api_cache_file", "/python/GitHub/github_apis_smart_export.json")
        self.test_results_dir = self.config.get("test_results_dir", "/python/GitHub/test_results")
        self.api_endpoints = []
        self.test_history = []
        self._session = requests.Session()
        self._ensure_directories()
        self._load_api_data()


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
        print(f"[GitHubAPITester] [{level.upper()}] {message}")

    def execute(self, action: str, params: Dict) -> Dict:
        """执行技能"""
        action_param = params.get("action", action)

        if action_param == "test_api":
            return self._test_api(params)
        elif action_param == "batch_test":
            return self._batch_test(params)
        elif action_param == "performance_test":
            return self._performance_test(params)
        elif action_param == "concurrent_test":
            return self._concurrent_test(params)
        elif action_param == "rate_limit_test":
            return self._rate_limit_test(params)
        elif action_param == "auth_test":
            return self._auth_test(params)
        elif action_param == "get_test_history":
            return self._get_test_history()
        elif action_param == "generate_report":
            return self._generate_report(params)
        else:
            return {
                "success": False,
                "error": f"未知动作: {action_param}"
            }

    def _ensure_directories(self):
        """确保目录存在"""
        Path(self.test_results_dir).mkdir(parents=True, exist_ok=True)
        self._log(f"确保测试结果目录存在: {self.test_results_dir}")

    def _load_api_data(self):
        """加载API数据"""
        try:
            if os.path.exists(self.api_cache_file):
                with open(self.api_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.api_endpoints = data.get("apis", [])
                self._log(f"加载了 {len(self.api_endpoints)} 个API端点")
            else:
                self._log("API缓存文件不存在，使用默认数据", "warn")
                self._load_default_apis()
        except Exception as e:
            self._log(f"加载API数据失败: {e}", "error")
            self._load_default_apis()

    def _load_default_apis(self):
        """加载默认API数据"""
        self.api_endpoints = [
            {
                "id": "github_rest_v3",
                "name": "GitHub REST API v3",
                "base_url": "https://api.github.com",
                "description": "GitHub REST API v3",
                "endpoints": [
                    {
                        "path": "/user",
                        "method": "GET",
                        "description": "获取当前用户信息"
                    },
                    {
                        "path": "/users/octocat",
                        "method": "GET",
                        "description": "获取指定用户信息"
                    },
                    {
                        "path": "/repos/octocat/Hello-World",
                        "method": "GET",
                        "description": "获取指定仓库信息"
                    },
                    {
                        "path": "/repos/octocat/Hello-World/issues",
                        "method": "GET",
                        "description": "获取仓库的 issues"
                    },
                    {
                        "path": "/rate_limit",
                        "method": "GET",
                        "description": "获取速率限制"
                    }
                ]
            }
        ]

    def _test_api(self, params: Dict) -> Dict:
        """测试单个API"""
        endpoint = params.get("endpoint")
        method = params.get("method", "GET")
        headers = params.get("headers", {})
        params = params.get("params", {})
        data = params.get("data")

        if not endpoint:
            return {
                "success": False,
                "error": "缺少endpoint参数"
            }

        try:
            # 构建URL
            if not endpoint.startswith("http"):
                url = f"https://api.github.com{endpoint}"
            else:
                url = endpoint

            # 替换路径参数
            for key, value in params.items():
                if f"{{{key}}}" in url:
                    url = url.replace(f"{{{key}}}", str(value))

            # 准备请求
            request_kwargs = {
                "headers": {
                    "Accept": "application/vnd.github.v3+json",
                    **headers
                },
                "timeout": 30
            }

            if method == "GET":
                request_kwargs["params"] = params
                response = self._session.get(url, **request_kwargs)
            elif method == "POST":
                request_kwargs["json"] = data or params
                response = self._session.post(url, **request_kwargs)
            elif method == "PUT":
                request_kwargs["json"] = data or params
                response = self._session.put(url, **request_kwargs)
            elif method == "DELETE":
                response = self._session.delete(url, **request_kwargs)
            else:
                return {
                    "success": False,
                    "error": f"不支持的HTTP方法: {method}"
                }

            # 记录测试结果
            test_result = {
                "endpoint": endpoint,
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "duration": response.elapsed.total_seconds(),
                "timestamp": datetime.now().isoformat(),
                "success": 200 <= response.status_code < 300
            }

            self.test_history.append(test_result)

            return {
                "success": True,
                "test_result": test_result
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"测试API失败: {str(e)}"
            }

    def _batch_test(self, params: Dict) -> Dict:
        """批量测试API"""
        endpoints = params.get("endpoints", [])
        concurrency = params.get("concurrency", 5)

        if not endpoints:
            # 如果没有提供端点，使用默认端点
            endpoints = []
            for api in self.api_endpoints:
                for endpoint in api.get("endpoints", []):
                    endpoints.append({
                        "endpoint": endpoint["path"],
                        "method": endpoint["method"]
                    })

        results = []
        start_time = time.time()

        # 使用线程池并发测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_endpoint = {}
            for endpoint_info in endpoints:
                future = executor.submit(self._test_api, {
                    "endpoint": endpoint_info["endpoint"],
                    "method": endpoint_info.get("method", "GET"),
                    "params": endpoint_info.get("params", {})
                })
                future_to_endpoint[future] = endpoint_info

            for future in concurrent.futures.as_completed(future_to_endpoint):
                endpoint_info = future_to_endpoint[future]
                try:
                    result = future.result()
                    if result.get("success"):
                        results.append(result.get("test_result"))
                    else:
                        results.append({
                            "endpoint": endpoint_info["endpoint"],
                            "method": endpoint_info.get("method", "GET"),
                            "error": result.get("error"),
                            "timestamp": datetime.now().isoformat(),
                            "success": False
                        })
                except Exception as e:
                    results.append({
                        "endpoint": endpoint_info["endpoint"],
                        "method": endpoint_info.get("method", "GET"),
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                        "success": False
                    })

        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.get("success"))

        # 保存测试结果
        test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = Path(self.test_results_dir) / f"batch_test_{test_id}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "results": results,
                "summary": {
                    "total": len(results),
                    "success": success_count,
                    "failure": len(results) - success_count,
                    "total_time": total_time,
                    "average_time": total_time / len(results) if results else 0
                },
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "results": results,
            "summary": {
                "total": len(results),
                "success": success_count,
                "failure": len(results) - success_count,
                "total_time": total_time,
                "average_time": total_time / len(results) if results else 0
            },
            "result_file": str(result_file)
        }

    def _performance_test(self, params: Dict) -> Dict:
        """性能测试"""
        endpoint = params.get("endpoint", "/users/octocat")
        method = params.get("method", "GET")
        iterations = params.get("iterations", 100)
        concurrency = params.get("concurrency", 10)

        results = []
        start_time = time.time()

        # 并发性能测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = []
            for _ in range(iterations):
                future = executor.submit(self._test_api, {
                    "endpoint": endpoint,
                    "method": method
                })
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result.get("success"):
                        results.append(result.get("test_result"))
                except Exception as e:
                    pass

        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.get("success"))
        durations = [r.get("duration", 0) for r in results if r.get("success")]

        # 计算性能指标
        performance_metrics = {
            "total_requests": iterations,
            "success_requests": success_count,
            "failure_requests": iterations - success_count,
            "total_time": total_time,
            "average_response_time": sum(durations) / len(durations) if durations else 0,
            "max_response_time": max(durations) if durations else 0,
            "min_response_time": min(durations) if durations else 0,
            "requests_per_second": iterations / total_time if total_time > 0 else 0
        }

        # 保存性能测试结果
        test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = Path(self.test_results_dir) / f"performance_test_{test_id}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "endpoint": endpoint,
                "method": method,
                "metrics": performance_metrics,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "performance_metrics": performance_metrics,
            "result_file": str(result_file)
        }

    def _concurrent_test(self, params: Dict) -> Dict:
        """并发测试"""
        endpoint = params.get("endpoint", "/users/octocat")
        method = params.get("method", "GET")
        concurrent_users = params.get("concurrent_users", 50)
        duration = params.get("duration", 60)  # 秒

        start_time = time.time()
        end_time = start_time + duration
        results = []

        def test_worker():
            while time.time() < end_time:
                result = self._test_api({
                    "endpoint": endpoint,
                    "method": method
                })
                if result.get("success"):
                    results.append(result.get("test_result"))

        # 启动并发测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for _ in range(concurrent_users):
                future = executor.submit(test_worker)
                futures.append(future)

            # 等待所有测试完成
            concurrent.futures.wait(futures)

        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.get("success"))

        # 计算并发测试指标
        concurrent_metrics = {
            "concurrent_users": concurrent_users,
            "test_duration": total_time,
            "total_requests": len(results),
            "success_requests": success_count,
            "failure_requests": len(results) - success_count,
            "requests_per_second": len(results) / total_time if total_time > 0 else 0,
            "error_rate": (len(results) - success_count) / len(results) if results else 0
        }

        # 保存并发测试结果
        test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = Path(self.test_results_dir) / f"concurrent_test_{test_id}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "endpoint": endpoint,
                "method": method,
                "metrics": concurrent_metrics,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "concurrent_metrics": concurrent_metrics,
            "result_file": str(result_file)
        }

    def _rate_limit_test(self, params: Dict) -> Dict:
        """速率限制测试"""
        endpoint = params.get("endpoint", "/rate_limit")
        method = params.get("method", "GET")
        requests_per_minute = params.get("requests_per_minute", 60)
        duration = params.get("duration", 120)  # 秒

        results = []
        start_time = time.time()
        requests_made = 0

        # 控制请求速率
        while time.time() - start_time < duration:
            result = self._test_api({
                "endpoint": endpoint,
                "method": method
            })
            if result.get("success"):
                test_result = result.get("test_result")
                results.append(test_result)
                requests_made += 1

                # 检查速率限制
                if "X-RateLimit-Remaining" in test_result.get("headers", {}):
                    remaining = int(test_result["headers"].get("X-RateLimit-Remaining", 0))
                    if remaining < 10:
                        self._log(f"速率限制警告: 剩余 {remaining} 次请求", "warn")

            # 控制速率
            time.sleep(60 / requests_per_minute)

        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r.get("success"))

        # 分析速率限制
        rate_limit_metrics = {
            "total_requests": requests_made,
            "success_requests": success_count,
            "failure_requests": requests_made - success_count,
            "test_duration": total_time,
            "requests_per_minute": requests_made / (total_time / 60),
            "rate_limit_encountered": any(403 == r.get("status_code") for r in results)
        }

        # 保存速率限制测试结果
        test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = Path(self.test_results_dir) / f"rate_limit_test_{test_id}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "endpoint": endpoint,
                "method": method,
                "metrics": rate_limit_metrics,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "rate_limit_metrics": rate_limit_metrics,
            "result_file": str(result_file)
        }

    def _auth_test(self, params: Dict) -> Dict:
        """认证测试"""
        endpoint = params.get("endpoint", "/user")
        method = params.get("method", "GET")
        token = params.get("token")

        results = []

        # 测试无认证
        self._log("测试无认证请求")
        result = self._test_api({
            "endpoint": endpoint,
            "method": method
        })
        if result.get("success"):
            results.append({
                "type": "no_auth",
                "result": result.get("test_result")
            })

        # 测试有认证
        if token:
            self._log("测试有认证请求")
            result = self._test_api({
                "endpoint": endpoint,
                "method": method,
                "headers": {
                    "Authorization": f"token {token}"
                }
            })
            if result.get("success"):
                results.append({
                    "type": "with_auth",
                    "result": result.get("test_result")
                })

        # 保存认证测试结果
        test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = Path(self.test_results_dir) / f"auth_test_{test_id}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "endpoint": endpoint,
                "method": method,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "results": results,
            "result_file": str(result_file)
        }

    def _get_test_history(self) -> Dict:
        """获取测试历史"""
        return {
            "success": True,
            "history": self.test_history,
            "count": len(self.test_history)
        }

    def _generate_report(self, params: Dict) -> Dict:
        """生成测试报告"""
        test_files = params.get("test_files", [])
        output_file = params.get("output_file", f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        if not test_files:
            # 自动查找测试结果文件
            test_files = list(Path(self.test_results_dir).glob("*.json"))

        all_results = []
        for test_file in test_files:
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    all_results.append(data)
            except Exception as e:
                self._log(f"读取测试文件失败: {e}", "error")

        # 生成综合报告
        report = {
            "summary": {
                "total_tests": len(all_results),
                "total_requests": sum(len(r.get("results", [])) for r in all_results),
                "total_success": sum(sum(1 for res in r.get("results", []) if res.get("success")) for r in all_results),
                "total_failure": sum(sum(1 for res in r.get("results", []) if not res.get("success")) for r in all_results),
                "generated_at": datetime.now().isoformat()
            },
            "tests": all_results
        }

        # 保存报告
        report_file = Path(self.test_results_dir) / output_file
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "report": report,
            "report_file": str(report_file)
        }


# 技能实例
skill = GitHubAPITester()


if __name__ == "__main__":
    # 测试技能
    tester = GitHubAPITester()

    # 测试单个API
    print("1. 测试单个API:")
    result = tester.execute("test_api", {
        "action": "test_api",
        "endpoint": "/users/octocat",
        "method": "GET"
    })
    if result.get("success"):
        test_result = result.get("test_result")
        print(f"   状态码: {test_result['status_code']}")
        print(f"   响应时间: {test_result['duration']:.3f} 秒")

    # 批量测试
    print("\n2. 批量测试API:")
    result = tester.execute("batch_test", {
        "action": "batch_test",
        "concurrency": 3
    })
    if result.get("success"):
        summary = result.get("summary")
        print(f"   总计: {summary['total']} 个API")
        print(f"   成功: {summary['success']} 个")
        print(f"   失败: {summary['failure']} 个")
        print(f"   总时间: {summary['total_time']:.2f} 秒")

    # 性能测试
    print("\n3. 性能测试:")
    result = tester.execute("performance_test", {
        "action": "performance_test",
        "iterations": 10,
        "concurrency": 5
    })
    if result.get("success"):
        metrics = result.get("performance_metrics")
        print(f"   总请求: {metrics['total_requests']}")
        print(f"   成功请求: {metrics['success_requests']}")
        print(f"   平均响应时间: {metrics['average_response_time']:.3f} 秒")
        print(f"   QPS: {metrics['requests_per_second']:.2f}")

    # 速率限制测试
    print("\n4. 速率限制测试:")
    result = tester.execute("rate_limit_test", {
        "action": "rate_limit_test",
        "requests_per_minute": 30,
        "duration": 30
    })
    if result.get("success"):
        metrics = result.get("rate_limit_metrics")
        print(f"   总请求: {metrics['total_requests']}")
        print(f"   成功请求: {metrics['success_requests']}")
        print(f"   遇到速率限制: {metrics['rate_limit_encountered']}")

    print("\nGitHub API测试工具测试完成")
