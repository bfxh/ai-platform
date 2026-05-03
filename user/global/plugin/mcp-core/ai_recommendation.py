#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - AI 智能推荐系统

功能:
- 基于用户行为的技能推荐
- 自动工作流生成
- 智能错误诊断和修复
- 性能自动优化
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class UserBehavior:
    """用户行为数据"""
    user_id: str
    skill_name: str
    action: str
    timestamp: datetime
    success: bool
    duration: float
    params: dict = field(default_factory=dict)
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "skill_name": self.skill_name,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "duration": self.duration,
            "params": self.params,
            "error_message": self.error_message,
        }


@dataclass
class SkillRecommendation:
    """技能推荐"""
    skill_name: str
    confidence: float
    reason: str
    context: dict = field(default_factory=dict)


class UserBehaviorAnalyzer:
    """用户行为分析器"""

    def __init__(self):
        self.behaviors: List[UserBehavior] = []
        self.user_patterns: Dict[str, Dict] = defaultdict(lambda: defaultdict(int))
        self.skill_usage: Dict[str, int] = defaultdict(int)
        self.error_patterns: Dict[str, List[str]] = defaultdict(list)

    def record_behavior(self, behavior: UserBehavior):
        """记录用户行为"""
        self.behaviors.append(behavior)

        # 更新用户使用模式
        self.user_patterns[behavior.user_id][behavior.skill_name] += 1
        self.skill_usage[behavior.skill_name] += 1

        # 记录错误模式
        if not behavior.success and behavior.error_message:
            self.error_patterns[behavior.skill_name].append(behavior.error_message)

    def get_user_favorite_skills(self, user_id: str, limit: int = 5) -> List[Tuple[str, int]]:
        """获取用户最常用的技能"""
        user_skills = self.user_patterns[user_id]
        sorted_skills = sorted(user_skills.items(), key=lambda x: x[1], reverse=True)
        return sorted_skills[:limit]

    def get_skill_usage_stats(self, days: int = 7) -> Dict[str, int]:
        """获取技能使用统计"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_usage = defaultdict(int)

        for behavior in self.behaviors:
            if behavior.timestamp > cutoff_date:
                recent_usage[behavior.skill_name] += 1

        return dict(recent_usage)

    def get_error_patterns(self, skill_name: str) -> List[str]:
        """获取技能的错误模式"""
        return self.error_patterns.get(skill_name, [])

    def find_similar_users(self, user_id: str, limit: int = 5) -> List[Tuple[str, float]]:
        """查找相似用户（基于使用模式）"""
        target_patterns = self.user_patterns[user_id]
        similarities = []

        for other_id, patterns in self.user_patterns.items():
            if other_id != user_id:
                # 计算余弦相似度
                similarity = self._calculate_similarity(target_patterns, patterns)
                if similarity > 0:
                    similarities.append((other_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    def _calculate_similarity(self, patterns1: Dict, patterns2: Dict) -> float:
        """计算两个用户模式的相似度"""
        all_skills = set(patterns1.keys()) | set(patterns2.keys())

        if not all_skills:
            return 0.0

        dot_product = sum(
            patterns1.get(skill, 0) * patterns2.get(skill, 0)
            for skill in all_skills
        )

        norm1 = sum(count ** 2 for count in patterns1.values()) ** 0.5
        norm2 = sum(count ** 2 for count in patterns2.values()) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class SkillRecommender:
    """技能推荐器"""

    def __init__(self, analyzer: UserBehaviorAnalyzer):
        self.analyzer = analyzer
        self.skill_categories: Dict[str, List[str]] = {}
        self.skill_relationships: Dict[str, List[str]] = defaultdict(list)

    def add_skill_category(self, skill_name: str, categories: List[str]):
        """添加技能分类"""
        self.skill_categories[skill_name] = categories

    def add_skill_relationship(self, skill1: str, skill2: str):
        """添加技能关联"""
        if skill2 not in self.skill_relationships[skill1]:
            self.skill_relationships[skill1].append(skill2)
        if skill1 not in self.skill_relationships[skill2]:
            self.skill_relationships[skill2].append(skill1)

    def recommend_for_user(self, user_id: str, limit: int = 5) -> List[SkillRecommendation]:
        """为用户推荐技能"""
        recommendations = []

        # 1. 基于用户历史行为推荐
        behavior_recs = self._recommend_by_behavior(user_id)
        recommendations.extend(behavior_recs)

        # 2. 基于相似用户推荐
        similar_user_recs = self._recommend_by_similar_users(user_id)
        recommendations.extend(similar_user_recs)

        # 3. 基于技能关联推荐
        relationship_recs = self._recommend_by_relationships(user_id)
        recommendations.extend(relationship_recs)

        # 去重并排序
        unique_recs = self._deduplicate_recommendations(recommendations)
        unique_recs.sort(key=lambda x: x.confidence, reverse=True)

        return unique_recs[:limit]

    def recommend_for_task(self, task_description: str, limit: int = 5) -> List[SkillRecommendation]:
        """基于任务描述推荐技能"""
        recommendations = []

        # 简单的关键词匹配
        keywords = self._extract_keywords(task_description)

        for skill_name, categories in self.skill_categories.items():
            score = 0
            matched_keywords = []

            for keyword in keywords:
                if keyword.lower() in skill_name.lower():
                    score += 0.5
                    matched_keywords.append(keyword)

                for category in categories:
                    if keyword.lower() in category.lower():
                        score += 0.3
                        matched_keywords.append(keyword)

            if score > 0:
                recommendations.append(SkillRecommendation(
                    skill_name=skill_name,
                    confidence=min(score, 1.0),
                    reason=f"匹配关键词: {', '.join(matched_keywords)}",
                    context={"matched_keywords": matched_keywords}
                ))

        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        return recommendations[:limit]

    def _recommend_by_behavior(self, user_id: str) -> List[SkillRecommendation]:
        """基于用户行为推荐"""
        recommendations = []
        favorite_skills = self.analyzer.get_user_favorite_skills(user_id)

        # 推荐同一类别的其他技能
        for skill_name, count in favorite_skills:
            categories = self.skill_categories.get(skill_name, [])

            for other_skill, other_categories in self.skill_categories.items():
                if other_skill != skill_name:
                    common_categories = set(categories) & set(other_categories)
                    if common_categories:
                        confidence = len(common_categories) / max(len(categories), len(other_categories))
                        confidence *= min(count / 10, 1.0)  # 根据使用频率调整

                        recommendations.append(SkillRecommendation(
                            skill_name=other_skill,
                            confidence=confidence,
                            reason=f"与您常用的 '{skill_name}' 属于同一类别",
                            context={"related_skill": skill_name, "categories": list(common_categories)}
                        ))

        return recommendations

    def _recommend_by_similar_users(self, user_id: str) -> List[SkillRecommendation]:
        """基于相似用户推荐"""
        recommendations = []
        similar_users = self.analyzer.find_similar_users(user_id)

        target_skills = set(self.analyzer.user_patterns[user_id].keys())

        for similar_id, similarity in similar_users:
            similar_skills = set(self.analyzer.user_patterns[similar_id].keys())
            new_skills = similar_skills - target_skills

            for skill in new_skills:
                recommendations.append(SkillRecommendation(
                    skill_name=skill,
                    confidence=similarity * 0.8,
                    reason=f"与您相似的用户 '{similar_id}' 经常使用",
                    context={"similar_user": similar_id, "similarity": similarity}
                ))

        return recommendations

    def _recommend_by_relationships(self, user_id: str) -> List[SkillRecommendation]:
        """基于技能关联推荐"""
        recommendations = []
        user_skills = set(self.analyzer.user_patterns[user_id].keys())

        for skill in user_skills:
            related_skills = self.skill_relationships.get(skill, [])
            for related in related_skills:
                if related not in user_skills:
                    recommendations.append(SkillRecommendation(
                        skill_name=related,
                        confidence=0.7,
                        reason=f"与 '{skill}' 经常一起使用",
                        context={"related_skill": skill}
                    ))

        return recommendations

    def _deduplicate_recommendations(self, recommendations: List[SkillRecommendation]) -> List[SkillRecommendation]:
        """去重推荐结果"""
        seen = {}

        for rec in recommendations:
            if rec.skill_name in seen:
                # 合并置信度
                seen[rec.skill_name].confidence = max(
                    seen[rec.skill_name].confidence,
                    rec.confidence
                )
            else:
                seen[rec.skill_name] = rec

        return list(seen.values())

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fa5]+\b', text.lower())
        # 过滤常见停用词
        stop_words = {'的', '了', '和', '是', '在', '有', '我', '都', '个', '与', 'the', 'a', 'an', 'is', 'are'}
        return [w for w in words if w not in stop_words and len(w) > 1]


class WorkflowGenerator:
    """工作流生成器"""

    def __init__(self, recommender: SkillRecommender):
        self.recommender = recommender
        self.workflow_patterns: Dict[str, List[List[str]]] = defaultdict(list)

    def learn_workflow(self, workflow_name: str, skills: List[str]):
        """学习工作流模式"""
        self.workflow_patterns[workflow_name].append(skills)

    def generate_workflow(self, goal: str, available_skills: List[str]) -> List[SkillRecommendation]:
        """基于目标生成工作流"""
        # 推荐相关技能
        recommendations = self.recommender.recommend_for_task(goal, limit=10)

        # 过滤可用技能
        available_recommendations = [
            rec for rec in recommendations
            if rec.skill_name in available_skills
        ]

        # 尝试匹配已知工作流模式
        for workflow_name, patterns in self.workflow_patterns.items():
            for pattern in patterns:
                if all(skill in available_skills for skill in pattern):
                    # 如果找到匹配的工作流，提升相关技能的置信度
                    for skill in pattern:
                        for rec in available_recommendations:
                            if rec.skill_name == skill:
                                rec.confidence = min(rec.confidence + 0.2, 1.0)
                                rec.reason += f" (来自工作流: {workflow_name})"

        # 按置信度排序
        available_recommendations.sort(key=lambda x: x.confidence, reverse=True)

        return available_recommendations

    def suggest_workflow_optimization(self, current_workflow: List[str]) -> List[dict]:
        """建议工作流优化"""
        suggestions = []

        # 检查是否有已知更好的工作流模式
        for workflow_name, patterns in self.workflow_patterns.items():
            for pattern in patterns:
                if set(current_workflow) == set(pattern):
                    continue

                # 计算相似度
                common_skills = set(current_workflow) & set(pattern)
                if len(common_skills) >= len(current_workflow) * 0.5:
                    missing_skills = set(pattern) - set(current_workflow)
                    extra_skills = set(current_workflow) - set(pattern)

                    if missing_skills or extra_skills:
                        suggestions.append({
                            "type": "workflow_alternative",
                            "workflow_name": workflow_name,
                            "confidence": len(common_skills) / max(len(current_workflow), len(pattern)),
                            "suggested_additions": list(missing_skills),
                            "suggested_removals": list(extra_skills),
                            "reason": f"基于工作流 '{workflow_name}' 的优化建议",
                        })

        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:3]


class ErrorDiagnostician:
    """错误诊断器"""

    def __init__(self, analyzer: UserBehaviorAnalyzer):
        self.analyzer = analyzer
        self.error_solutions: Dict[str, List[dict]] = defaultdict(list)
        self.common_errors: Dict[str, int] = defaultdict(int)

    def record_error_solution(self, error_pattern: str, solution: str, success_rate: float = 1.0):
        """记录错误解决方案"""
        self.error_solutions[error_pattern].append({
            "solution": solution,
            "success_rate": success_rate,
            "usage_count": 1,
        })
        self.common_errors[error_pattern] += 1

    def diagnose(self, skill_name: str, error_message: str) -> List[dict]:
        """诊断错误并提供解决方案"""
        solutions = []

        # 1. 查找已知解决方案
        for pattern, pattern_solutions in self.error_solutions.items():
            if pattern in error_message or error_message in pattern:
                for sol in pattern_solutions:
                    solutions.append({
                        "type": "known_solution",
                        "solution": sol["solution"],
                        "confidence": sol["success_rate"],
                        "reason": "基于历史错误模式匹配",
                    })

        # 2. 分析错误类型
        error_type = self._classify_error(error_message)
        type_solutions = self._get_solutions_for_error_type(error_type)
        solutions.extend(type_solutions)

        # 3. 检查是否是常见错误
        if error_message in self.common_errors:
            solutions.append({
                "type": "common_error",
                "solution": "这是一个常见错误，请参考文档",
                "confidence": 0.6,
                "reason": f"该错误已发生 {self.common_errors[error_message]} 次",
            })

        # 按置信度排序
        solutions.sort(key=lambda x: x["confidence"], reverse=True)
        return solutions[:5]

    def _classify_error(self, error_message: str) -> str:
        """分类错误类型"""
        error_lower = error_message.lower()

        if any(word in error_lower for word in ["permission", "access", "denied", "权限"]):
            return "permission_error"
        elif any(word in error_lower for word in ["network", "connection", "timeout", "网络", "连接"]):
            return "network_error"
        elif any(word in error_lower for word in ["file", "not found", "path", "文件", "路径"]):
            return "file_error"
        elif any(word in error_lower for word in ["memory", "out of", "内存"]):
            return "memory_error"
        elif any(word in error_lower for word in ["invalid", "format", "parse", "格式", "解析"]):
            return "format_error"
        else:
            return "unknown_error"

    def _get_solutions_for_error_type(self, error_type: str) -> List[dict]:
        """获取错误类型的解决方案"""
        solutions_map = {
            "permission_error": [
                {"solution": "检查文件/目录权限", "confidence": 0.9},
                {"solution": "以管理员身份运行", "confidence": 0.8},
            ],
            "network_error": [
                {"solution": "检查网络连接", "confidence": 0.9},
                {"solution": "检查防火墙设置", "confidence": 0.7},
                {"solution": "增加超时时间", "confidence": 0.6},
            ],
            "file_error": [
                {"solution": "检查文件路径是否正确", "confidence": 0.9},
                {"solution": "确保文件存在", "confidence": 0.8},
                {"solution": "检查文件名拼写", "confidence": 0.7},
            ],
            "memory_error": [
                {"solution": "关闭其他程序释放内存", "confidence": 0.8},
                {"solution": "增加系统内存", "confidence": 0.6},
                {"solution": "优化代码减少内存使用", "confidence": 0.7},
            ],
            "format_error": [
                {"solution": "检查输入数据格式", "confidence": 0.9},
                {"solution": "验证数据完整性", "confidence": 0.8},
            ],
        }

        solutions = solutions_map.get(error_type, [])
        return [
            {"type": "error_type_solution", "solution": s["solution"], "confidence": s["confidence"], "reason": f"错误类型: {error_type}"}
            for s in solutions
        ]


class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self, analyzer: UserBehaviorAnalyzer):
        self.analyzer = analyzer
        self.performance_history: Dict[str, List[dict]] = defaultdict(list)

    def record_performance(self, skill_name: str, duration: float, params: dict):
        """记录性能数据"""
        self.performance_history[skill_name].append({
            "duration": duration,
            "params": params,
            "timestamp": datetime.now().isoformat(),
        })

    def analyze_performance(self, skill_name: str) -> dict:
        """分析技能性能"""
        history = self.performance_history.get(skill_name, [])

        if not history:
            return {"status": "no_data", "suggestions": []}

        durations = [h["duration"] for h in history]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)

        suggestions = []

        # 分析性能趋势
        if len(durations) >= 5:
            recent_avg = sum(durations[-5:]) / 5
            old_avg = sum(durations[:5]) / 5

            if recent_avg > old_avg * 1.2:
                suggestions.append({
                    "type": "performance_degradation",
                    "severity": "warning",
                    "message": f"性能下降: 最近平均耗时 {recent_avg:.2f}s, 之前 {old_avg:.2f}s",
                    "suggestion": "检查最近的代码变更或数据量变化",
                })

        # 检查异常值
        threshold = avg_duration * 2
        slow_executions = [d for d in durations if d > threshold]
        if slow_executions:
            suggestions.append({
                "type": "slow_executions",
                "severity": "info",
                "message": f"发现 {len(slow_executions)} 次慢执行 (> {threshold:.2f}s)",
                "suggestion": "检查这些执行的参数是否有异常",
            })

        return {
            "status": "analyzed",
            "statistics": {
                "avg_duration": avg_duration,
                "max_duration": max_duration,
                "min_duration": min_duration,
                "execution_count": len(durations),
            },
            "suggestions": suggestions,
        }

    def suggest_optimizations(self, skill_name: str) -> List[dict]:
        """建议优化方案"""
        analysis = self.analyze_performance(skill_name)
        return analysis.get("suggestions", [])


class AIRecommendationEngine:
    """AI 推荐引擎主类"""

    def __init__(self):
        self.analyzer = UserBehaviorAnalyzer()
        self.recommender = SkillRecommender(self.analyzer)
        self.workflow_generator = WorkflowGenerator(self.recommender)
        self.error_diagnostician = ErrorDiagnostician(self.analyzer)
        self.performance_optimizer = PerformanceOptimizer(self.analyzer)

    def record_usage(self, user_id: str, skill_name: str, action: str,
                     success: bool, duration: float, params: dict = None,
                     error_message: str = ""):
        """记录技能使用"""
        behavior = UserBehavior(
            user_id=user_id,
            skill_name=skill_name,
            action=action,
            timestamp=datetime.now(),
            success=success,
            duration=duration,
            params=params or {},
            error_message=error_message,
        )
        self.analyzer.record_behavior(behavior)

        # 记录性能数据
        self.performance_optimizer.record_performance(skill_name, duration, params or {})

    def get_recommendations(self, user_id: str, limit: int = 5) -> List[SkillRecommendation]:
        """获取技能推荐"""
        return self.recommender.recommend_for_user(user_id, limit)

    def get_task_recommendations(self, task_description: str, limit: int = 5) -> List[SkillRecommendation]:
        """基于任务获取推荐"""
        return self.recommender.recommend_for_task(task_description, limit)

    def generate_workflow(self, goal: str, available_skills: List[str]) -> List[SkillRecommendation]:
        """生成工作流"""
        return self.workflow_generator.generate_workflow(goal, available_skills)

    def diagnose_error(self, skill_name: str, error_message: str) -> List[dict]:
        """诊断错误"""
        return self.error_diagnostician.diagnose(skill_name, error_message)

    def analyze_performance(self, skill_name: str) -> dict:
        """分析性能"""
        return self.performance_optimizer.analyze_performance(skill_name)

    def add_skill_category(self, skill_name: str, categories: List[str]):
        """添加技能分类"""
        self.recommender.add_skill_category(skill_name, categories)

    def add_skill_relationship(self, skill1: str, skill2: str):
        """添加技能关联"""
        self.recommender.add_skill_relationship(skill1, skill2)

    def learn_workflow(self, workflow_name: str, skills: List[str]):
        """学习工作流"""
        self.workflow_generator.learn_workflow(workflow_name, skills)

    def record_error_solution(self, error_pattern: str, solution: str, success_rate: float = 1.0):
        """记录错误解决方案"""
        self.error_diagnostician.record_error_solution(error_pattern, solution, success_rate)


# 使用示例
if __name__ == "__main__":
    engine = AIRecommendationEngine()

    # 配置技能分类和关联
    engine.add_skill_category("file_backup", ["文件", "备份", "工具"])
    engine.add_skill_category("github_download", ["GitHub", "下载", "网络"])
    engine.add_skill_category("ai_toolkit_manager", ["AI", "工具", "管理"])

    engine.add_skill_relationship("file_backup", "file_restore")
    engine.add_skill_relationship("github_download", "github_repo_manager")

    # 模拟用户使用
    engine.record_usage("user1", "file_backup", "backup", True, 2.5)
    engine.record_usage("user1", "file_backup", "backup", True, 2.3)
    engine.record_usage("user1", "github_download", "download", True, 5.0)

    engine.record_usage("user2", "file_backup", "backup", True, 2.0)
    engine.record_usage("user2", "ai_toolkit_manager", "list", True, 1.0)

    # 获取推荐
    print("为用户 user1 推荐技能:")
    recommendations = engine.get_recommendations("user1")
    for rec in recommendations:
        print(f"  - {rec.skill_name}: {rec.reason} (置信度: {rec.confidence:.2f})")

    # 基于任务推荐
    print("\n为任务 '备份文件到GitHub' 推荐技能:")
    task_recs = engine.get_task_recommendations("备份文件到GitHub")
    for rec in task_recs:
        print(f"  - {rec.skill_name}: {rec.reason} (置信度: {rec.confidence:.2f})")

    # 错误诊断
    print("\n诊断错误:")
    engine.record_usage("user1", "file_backup", "backup", False, 0.0,
                       error_message="Permission denied: cannot access directory")
    solutions = engine.diagnose_error("file_backup", "Permission denied: cannot access directory")
    for sol in solutions:
        print(f"  - {sol['type']}: {sol['solution']} (置信度: {sol['confidence']:.2f})")

    # 性能分析
    print("\n性能分析 (file_backup):")
    analysis = engine.analyze_performance("file_backup")
    print(f"  状态: {analysis['status']}")
    if 'statistics' in analysis:
        stats = analysis['statistics']
        print(f"  平均耗时: {stats['avg_duration']:.2f}s")
        print(f"  执行次数: {stats['execution_count']}")
