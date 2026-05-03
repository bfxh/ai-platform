#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能系统模块

包含：
- 自然语言理解（NLP）
- 任务规划器
- 学习系统
- 智能调度
- 上下文管理

使系统能够理解自然语言任务，智能规划和执行。
"""

import json
import re
import time
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TaskAnalysis:
    """任务分析结果"""
    intent: str
    entities: Dict[str, Any]
    steps: List[Dict]
    confidence: float
    raw_input: str


@dataclass
class ExecutionResult:
    """执行结果"""
    action: str
    params: Dict
    success: bool
    data: Any
    error: str
    timestamp: str


class NLPUnderstanding:
    """自然语言理解模块"""

    def __init__(self):
        # 意图模式
        self.intent_patterns = {
            "SEARCH_REPOS": [
                r"查找.*GitHub.*(仓库|项目|repo)",
                r"搜索.*(GitHub|仓库|项目)",
                r"GitHub.*最.*(受欢迎|热门|star).*",
                r"(Python|JavaScript|Java).*框架",
                r"寻找.*(库|工具|SDK)"
            ],
            "GET_USER_INFO": [
                r"获取.*(用户|开发者).*信息",
                r"查看.*(用户|开发者).*详情",
                r"(用户|开发者).*资料",
                r"了解.*(用户|开发者)"
            ],
            "GET_REPO_INFO": [
                r"获取.*(仓库|项目).*信息",
                r"查看.*(仓库|项目).*详情",
                r"(仓库|项目).*资料",
                r"分析.*(仓库|项目)"
            ],
            "ANALYZE_REPO": [
                r"分析.*(仓库|项目)",
                r"(仓库|项目).*分析",
                r"(仓库|项目).*活跃度",
                r"(仓库|项目).*统计"
            ],
            "COMPARE_REPOS": [
                r"比较.*(仓库|项目)",
                r"(仓库|项目).*对比",
                r"(仓库|项目).*vs.*(仓库|项目)"
            ],
            "BATCH_GET": [
                r"批量.*(获取|查询)",
                r"(获取|查询).*多个.*(仓库|用户)"
            ]
        }

        # 实体提取模式
        self.entity_patterns = {
            "username": [
                r"用户\s*([a-zA-Z0-9_-]+)",
                r"开发者\s*([a-zA-Z0-9_-]+)",
                r"(octocat|microsoft|google|facebook|github)"
            ],
            "repo": [
                r"仓库\s*([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)",
                r"项目\s*([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)",
                r"([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)"
            ],
            "language": [
                r"(Python|JavaScript|Java|C\+\+|Go|Rust|TypeScript|PHP|Ruby|Swift|Kotlin)"
            ],
            "framework": [
                r"(Django|Flask|React|Vue|Angular|Spring|Express|Laravel|Ruby on Rails)"
            ],
            "query": [
                r"查找\s*(.*)",
                r"搜索\s*(.*)",
                r"寻找\s*(.*)"
            ],
            "metric": [
                r"(star|stars|fork|forks|contributor|contributors|commit|commits|issue|issues)"
            ]
        }

    def analyze_task(self, task_description: str) -> TaskAnalysis:
        """分析自然语言任务描述"""
        task_description = task_description.lower().strip()

        # 1. 识别意图
        intent = self._identify_intent(task_description)

        # 2. 提取实体
        entities = self._extract_entities(task_description)

        # 3. 分解任务
        steps = self._break_down_task(task_description, intent, entities)

        # 4. 计算置信度
        confidence = self._calculate_confidence(intent, entities)

        return TaskAnalysis(
            intent=intent,
            entities=entities,
            steps=steps,
            confidence=confidence,
            raw_input=task_description
        )

    def _identify_intent(self, text: str) -> str:
        """识别意图"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent
        return "UNKNOWN"

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """提取实体"""
        entities = {}

        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # 处理捕获组
                    if isinstance(matches[0], tuple):
                        matches = [m for m in matches[0] if m]
                    entities[entity_type] = matches[0] if len(matches) == 1 else matches
                    break

        # 特殊处理仓库格式
        if "repo" not in entities and "query" in entities:
            query = entities["query"]
            repo_match = re.search(r"([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)", query)
            if repo_match:
                entities["repo"] = repo_match.group(1)

        return entities

    def _break_down_task(self, text: str, intent: str, entities: Dict) -> List[Dict]:
        """分解任务"""
        steps = []

        if intent == "SEARCH_REPOS":
            query = entities.get("query", "") or entities.get("language", "") or entities.get("framework", "")
            if query:
                steps.append({
                    "action": "search_repos",
                    "params": {
                        "query": query,
                        "limit": 10
                    }
                })

        elif intent == "GET_USER_INFO":
            username = entities.get("username")
            if username:
                steps.append({
                    "action": "get_user",
                    "params": {
                        "username": username
                    }
                })

        elif intent == "GET_REPO_INFO":
            repo = entities.get("repo")
            if repo:
                owner, repo_name = repo.split("/")
                steps.append({
                    "action": "get_repo",
                    "params": {
                        "owner": owner,
                        "repo": repo_name
                    }
                })

        elif intent == "ANALYZE_REPO":
            repo = entities.get("repo")
            if repo:
                owner, repo_name = repo.split("/")
                steps.append({
                    "action": "analyze_repo",
                    "params": {
                        "owner": owner,
                        "repo": repo_name
                    }
                })

        elif intent == "COMPARE_REPOS":
            # 提取多个仓库
            repo_matches = re.findall(r"([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)", text)
            if len(repo_matches) >= 2:
                steps.append({
                    "action": "batch_get",
                    "params": {
                        "type": "repo",
                        "items": repo_matches[:5]  # 最多比较5个
                    }
                })

        elif intent == "BATCH_GET":
            # 提取多个项目
            items = []
            if "repo" in entities:
                if isinstance(entities["repo"], list):
                    items.extend(entities["repo"])
                else:
                    items.append(entities["repo"])
            steps.append({
                "action": "batch_get",
                "params": {
                    "type": "repo",
                    "items": items[:10]  # 最多10个
                }
            })

        # 如果没有识别到具体步骤，尝试搜索
        if not steps and intent != "UNKNOWN":
            steps.append({
                "action": "search_repos",
                "params": {
                    "query": text,
                    "limit": 5
                }
            })

        return steps

    def _calculate_confidence(self, intent: str, entities: Dict) -> float:
        """计算置信度"""
        if intent == "UNKNOWN":
            return 0.1

        base_confidence = 0.5
        entity_bonus = min(len(entities) * 0.1, 0.4)
        return min(base_confidence + entity_bonus, 0.9)


class TaskPlanner:
    """任务规划器"""

    def plan(self, task_analysis: TaskAnalysis) -> List[Dict]:
        """规划任务执行步骤"""
        steps = task_analysis.steps

        # 优化步骤顺序
        optimized_steps = self._optimize_steps(steps)

        # 添加必要的预处理步骤
        pre_steps = self._add_preprocessing_steps(task_analysis)

        # 添加后处理步骤
        post_steps = self._add_postprocessing_steps(task_analysis)

        return pre_steps + optimized_steps + post_steps

    def _optimize_steps(self, steps: List[Dict]) -> List[Dict]:
        """优化步骤顺序"""
        # 简单的优化：确保搜索步骤在前
        search_steps = []
        other_steps = []

        for step in steps:
            if step["action"] == "search_repos":
                search_steps.append(step)
            else:
                other_steps.append(step)

        return search_steps + other_steps

    def _add_preprocessing_steps(self, task_analysis: TaskAnalysis) -> List[Dict]:
        """添加预处理步骤"""
        pre_steps = []

        # 可以添加一些预处理步骤，比如验证输入等
        if task_analysis.confidence < 0.5:
            pre_steps.append({
                "action": "validate_input",
                "params": {
                    "input": task_analysis.raw_input,
                    "confidence": task_analysis.confidence
                }
            })

        return pre_steps

    def _add_postprocessing_steps(self, task_analysis: TaskAnalysis) -> List[Dict]:
        """添加后处理步骤"""
        post_steps = []

        # 可以添加一些后处理步骤，比如生成总结等
        if task_analysis.intent in ["SEARCH_REPOS", "ANALYZE_REPO", "COMPARE_REPOS"]:
            post_steps.append({
                "action": "generate_summary",
                "params": {
                    "intent": task_analysis.intent,
                    "entities": task_analysis.entities
                }
            })

        return post_steps


class LearningSystem:
    """学习系统"""

    def __init__(self, learning_data_path: str = "/python/gstack_core/learning_data.json"):
        self.learning_data_path = learning_data_path
        self.learning_data = self._load_learning_data()

    def _load_learning_data(self) -> Dict:
        """加载学习数据"""
        try:
            with open(self.learning_data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {
                "success_cases": [],
                "failure_cases": [],
                "patterns": {},
                "improvements": []
            }

    def _save_learning_data(self):
        """保存学习数据"""
        try:
            with open(self.learning_data_path, "w", encoding="utf-8") as f:
                json.dump(self.learning_data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def learn_from_success(self, action: str, params: Dict, result: Dict):
        """从成功中学习"""
        success_case = {
            "action": action,
            "params": params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

        self.learning_data["success_cases"].append(success_case)
        self._save_learning_data()

        # 分析成功模式
        self._analyze_patterns()

    def learn_from_failure(self, action: str, params: Dict, error: str):
        """从失败中学习"""
        failure_case = {
            "action": action,
            "params": params,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

        self.learning_data["failure_cases"].append(failure_case)
        self._save_learning_data()

        # 生成改进建议
        improvement = self._generate_improvement(action, error)
        if improvement:
            self.learning_data["improvements"].append(improvement)

    def _analyze_patterns(self):
        """分析成功模式"""
        # 简单的模式分析
        patterns = {}
        for case in self.learning_data["success_cases"]:
            action = case["action"]
            if action not in patterns:
                patterns[action] = {"count": 0, "params": {}}
            patterns[action]["count"] += 1

            # 分析参数模式
            for key, value in case["params"].items():
                if key not in patterns[action]["params"]:
                    patterns[action]["params"][key] = {}
                if value not in patterns[action]["params"][key]:
                    patterns[action]["params"][key][value] = 0
                patterns[action]["params"][key][value] += 1

        self.learning_data["patterns"] = patterns

    def _generate_improvement(self, action: str, error: str) -> Dict:
        """生成改进建议"""
        improvement = {
            "action": action,
            "error": error,
            "suggestion": self._generate_suggestion(action, error),
            "timestamp": datetime.now().isoformat()
        }
        return improvement

    def _generate_suggestion(self, action: str, error: str) -> str:
        """生成具体建议"""
        suggestions = {
            "get_user": {
                "Not Found": "检查用户名是否正确",
                "rate limit": "等待API限制恢复"
            },
            "get_repo": {
                "Not Found": "检查仓库路径是否正确",
                "rate limit": "等待API限制恢复"
            },
            "search_repos": {
                "rate limit": "等待API限制恢复",
                "timeout": "网络连接超时，请检查网络"
            }
        }

        for key, suggestion in suggestions.get(action, {}).items():
            if key in error:
                return suggestion

        return "尝试调整参数或稍后重试"

    def get_improvements(self) -> List[Dict]:
        """获取改进建议"""
        return self.learning_data["improvements"]


class SmartTaskScheduler:
    """智能任务调度器"""

    def schedule(self, tasks: List[Dict]) -> List[Dict]:
        """智能调度任务"""
        # 1. 优先级排序
        prioritized_tasks = self._prioritize_tasks(tasks)

        # 2. 依赖关系分析
        ordered_tasks = self._resolve_dependencies(prioritized_tasks)

        # 3. 资源优化
        optimized_tasks = self._optimize_resources(ordered_tasks)

        return optimized_tasks

    def _prioritize_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """优先级排序"""
        # 定义优先级
        priority_map = {
            "validate_input": 1,
            "search_repos": 2,
            "get_user": 3,
            "get_repo": 3,
            "analyze_repo": 4,
            "batch_get": 4,
            "generate_summary": 5
        }

        # 排序
        def get_priority(task):
            return priority_map.get(task.get("action"), 999)

        return sorted(tasks, key=get_priority)

    def _resolve_dependencies(self, tasks: List[Dict]) -> List[Dict]:
        """解析依赖关系"""
        # 简单的依赖分析
        # 这里可以实现更复杂的依赖解析
        return tasks

    def _optimize_resources(self, tasks: List[Dict]) -> List[Dict]:
        """优化资源使用"""
        # 合并相似任务
        optimized = []
        batch_tasks = []

        for task in tasks:
            if task["action"] == "get_repo":
                batch_tasks.append(task)
            else:
                if batch_tasks:
                    # 合并为批量任务
                    items = [f"{t['params']['owner']}/{t['params']['repo']}" for t in batch_tasks]
                    optimized.append({
                        "action": "batch_get",
                        "params": {
                            "type": "repo",
                            "items": items
                        }
                    })
                    batch_tasks = []
                optimized.append(task)

        if batch_tasks:
            items = [f"{t['params']['owner']}/{t['params']['repo']}" for t in batch_tasks]
            optimized.append({
                "action": "batch_get",
                "params": {
                    "type": "repo",
                    "items": items
                }
            })

        return optimized


class ContextManager:
    """上下文管理器"""

    def __init__(self, context_path: str = "/python/gstack_core/context.json"):
        self.context_path = context_path
        self.context = self._load_context()
        self.conversation_history = []

    def _load_context(self) -> Dict:
        """加载上下文"""
        try:
            with open(self.context_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {
                "last_user_input": "",
                "last_system_response": "",
                "recent_entities": {},
                "conversation_state": "active",
                "last_interaction": datetime.now().isoformat()
            }

    def _save_context(self):
        """保存上下文"""
        try:
            with open(self.context_path, "w", encoding="utf-8") as f:
                json.dump(self.context, f, ensure_ascii=False, indent=2)
        except:
            pass

    def track_interaction(self, user_input: str, system_response: Dict):
        """跟踪交互"""
        # 更新上下文
        self.context["last_user_input"] = user_input
        self.context["last_system_response"] = system_response
        self.context["last_interaction"] = datetime.now().isoformat()

        # 添加到对话历史
        self.conversation_history.append({
            "type": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        self.conversation_history.append({
            "type": "system",
            "content": system_response,
            "timestamp": datetime.now().isoformat()
        })

        # 限制历史长度
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

        self._save_context()

    def get_context(self) -> Dict:
        """获取当前上下文"""
        return self.context

    def get_recent_entities(self) -> Dict:
        """获取最近的实体"""
        return self.context.get("recent_entities", {})

    def update_entities(self, entities: Dict):
        """更新实体"""
        self.context["recent_entities"].update(entities)
        self._save_context()

    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history[-limit:]


class SmartSystem:
    """智能系统"""

    def __init__(self):
        self.nlp = NLPUnderstanding()
        self.planner = TaskPlanner()
        self.learning = LearningSystem()
        self.scheduler = SmartTaskScheduler()
        self.context = ContextManager()

    def process_task(self, task_description: str, core) -> Dict:
        """处理自然语言任务"""
        # 1. 分析任务
        analysis = self.nlp.analyze_task(task_description)

        # 2. 规划任务
        plan = self.planner.plan(analysis)

        # 3. 调度任务
        scheduled_tasks = self.scheduler.schedule(plan)

        # 4. 执行任务
        results = []
        for task in scheduled_tasks:
            action = task["action"]
            params = task["params"]

            # 跳过特殊动作
            if action in ["validate_input", "generate_summary"]:
                continue

            # 执行动作
            try:
                result = core.execute(action, params)
                results.append({
                    "action": action,
                    "params": params,
                    "success": result.get("success", False),
                    "data": result.get("data"),
                    "error": result.get("error", "")
                })

                # 学习
                if result.get("success"):
                    self.learning.learn_from_success(action, params, result)
                else:
                    self.learning.learn_from_failure(action, params, result.get("error", ""))

            except Exception as e:
                error_msg = str(e)
                results.append({
                    "action": action,
                    "params": params,
                    "success": False,
                    "data": None,
                    "error": error_msg
                })
                self.learning.learn_from_failure(action, params, error_msg)

            # 避免API限制
            time.sleep(0.5)

        # 5. 生成总结
        summary = self._generate_summary(analysis, results)

        # 6. 更新上下文
        self.context.track_interaction(task_description, {
            "analysis": analysis.__dict__,
            "results": results,
            "summary": summary
        })

        # 7. 更新实体
        self.context.update_entities(analysis.entities)

        return {
            "analysis": analysis.__dict__,
            "plan": plan,
            "scheduled_tasks": scheduled_tasks,
            "results": results,
            "summary": summary,
            "confidence": analysis.confidence,
            "improvements": self.learning.get_improvements()[-3:]  # 最近3个改进建议
        }

    def _generate_summary(self, analysis: TaskAnalysis, results: List[Dict]) -> str:
        """生成总结"""
        if not results:
            return "未执行任何任务"

        summary = f"任务分析: {analysis.intent}\n"
        summary += f"识别到的实体: {analysis.entities}\n"
        summary += "执行结果:\n"

        for i, result in enumerate(results, 1):
            status = "成功" if result["success"] else "失败"
            action = result["action"]
            summary += f"  {i}. {action}: {status}"
            if not result["success"]:
                summary += f" - {result['error']}"
            summary += "\n"

        # 添加统计
        success_count = sum(1 for r in results if r["success"])
        total_count = len(results)
        summary += f"\n统计: {success_count}/{total_count} 成功"

        return summary


# 测试
if __name__ == "__main__":
    print("🧪 测试智能系统")
    print("=" * 60)

    from gstack_core import GStackCore
    core = GStackCore()
    smart = SmartSystem()

    test_cases = [
        "查找GitHub上最受欢迎的Python Web框架",
        "获取octocat用户的信息",
        "分析microsoft/vscode仓库",
        "比较facebook/react和vuejs/vue",
        "批量获取microsoft/vscode和google/chrome"
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试 {i}: {test_case}")
        print("-" * 40)

        result = smart.process_task(test_case, core)

        print("分析结果:")
        print(f"  意图: {result['analysis']['intent']}")
        print(f"  实体: {result['analysis']['entities']}")
        print(f"  置信度: {result['confidence']:.2f}")

        print("\n执行计划:")
        for step in result['scheduled_tasks']:
            print(f"  - {step['action']}: {step['params']}")

        print("\n执行结果:")
        for res in result['results']:
            status = "✅" if res['success'] else "❌"
            print(f"  {status} {res['action']}: {'成功' if res['success'] else res['error']}")

        print("\n总结:")
        print(result['summary'])

        print("-" * 40)

    print("\n" + "=" * 60)
    print("✅ 智能系统测试完成！")
