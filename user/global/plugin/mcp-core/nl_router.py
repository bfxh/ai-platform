#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然语言 Skill 路由引擎 v3
功能：接收自然语言指令，自动匹配并调用对应 Skill 或 Workflow
不需要用户记住任何命令，直接说人话即可
"""

import re
import json
import os
import sys
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

# ─── 技能意图映射表（关键词 → Skill 名称）────────────────────────────────────
# 格式：[(关键词列表, skill_name, description)]
INTENT_MAP = [
    # 网络/传输
    (["传文件", "发文件", "传输", "发送到", "复制到另一台", "网络传输", "transfer", "发到另一台", "发给另一台", "传到另一台", "发文件到", "复制到", "共享文件"], "network_transfer", "文件网络传输"),
    (["exo", "集群", "cluster", "多机", "分布式推理"], "exo_cluster", "EXo 集群管理"),

    # 网络突破 / 下载（多策略镜像）
    (["下载", "clone", "拉取", "突破网络", "镜像", "多策略", "代理", "proxy", "直连", "ghproxy", "gitclone", "jsdelivr", "statically", "mirror", "pip镜像", "npm镜像"], "network_bypass", "网络突破下载"),

    # GitHub 分支分析（理解分支原理）
    (["分支", "branch", "工作流", "gitflow", "trunk", "compare", "差异", "分析分支"], "github_branch_analyzer", "GitHub 分支分析"),

    # GitHub Skill 融合安装（先搜索类似项目再安装融合）
    (["融合", "fuse", "融合安装", "skill融合", "分析项目", "理解原理", "安装github项目", "github安装"], "github_skill_fuser", "GitHub Skill 融合安装"),

    # GitHub 基础功能
    (["github", "搜索项目", "找项目", "开源", "仓库", "下载项目"], "github_project_search", "GitHub 项目搜索"),
    (["github api", "api 调用", "接口"], "github_api_manager", "GitHub API 管理"),
    (["安装技能", "安装 skill", "install skill", "下载技能"], "skill_installer", "Skill 安装"),

    # 通知
    (["通知", "提醒", "notify", "notification", "发消息", "弹窗"], "notification", "系统通知"),

    # 系统配置
    (["配置", "设置", "config", "系统设置", "system config"], "system_config", "系统配置"),

    # 系统优化
    (["优化系统", "清理内存", "加速", "optimize", "performance", "性能", "优化一下", "内存占用", "系统卡", "内存不足", "释放内存", "清理缓存"], "system_optimizer", "系统优化"),

    # AI工具
    (["ai 工具", "ai toolkit", "工具链", "ai 生态"], "ai_toolkit_manager", "AI 工具链管理"),

    # 备份
    (["备份", "backup", "快照", "恢复文件"], "file_backup", "文件备份"),

    # 知识库/记忆
    (["记住", "记录", "知识库", "memory", "知识", "笔记", "mempalace"], "mempalace", "知识库"),

    # 工作流
    (["工作流", "workflow", "流程", "自动化流程", "automation"], "workflow_runner", "工作流执行"),

    # 软件管理 / 位置查询（知识库驱动）
    (["软件在哪", "找软件", "软件位置", "where is", "locate", "哪个软件", "打开", "启动"], "software_scanner", "软件位置查询"),
    (["扫描软件", "更新软件库", "刷新软件"], "software_scanner", "软件库扫描"),

    # 项目文档
    (["生成文档", "创建文档", "项目文档", ".PROJECT.md", "project doc"], "project_doc_generator", "项目文档生成"),

    # 测试
    (["测试", "test", "单测", "验证", "check", "跑测试", "运行测试", "自动化测试"], "auto_tester", "自动化测试"),

    # 持续集成
    (["ci", "cd", "持续集成", "构建", "build", "deploy", "部署"], "continuous_integration", "持续集成"),
]

# ─── WorkBuddy Skills 意图映射（%USERPROFILE%\.workbuddy\skills）──────────────
WORKBUDDY_INTENT_MAP = [
    # 搜索/信息
    (["搜索", "查询", "search", "找信息", "搜一下", "查一下", "帮我找"], "多引擎搜索", "多引擎搜索"),
    (["github搜索", "github找", "github项目", "找github", "开源项目"], "github-opensource", "GitHub 开源项目"),
    (["新闻", "资讯", "news", "热点", "最近发生了什么"], "ai-news-collectors", "AI/科技新闻聚合"),

    # AI工具
    (["天气", "weather", "几度", "温度", "下雨"], "天气查询", "天气查询"),
    (["翻译", "translate", "英文", "中文转换", "翻译一下"], None, "内置翻译"),

    # 浏览器/网页
    (["浏览器", "browser", "打开网页", "访问网站", "截图", "网页", "自动化浏览器"], "agent-browser", "浏览器自动化"),

    # 图片/视觉
    (["画图", "生成图片", "图像", "image gen", "ai绘图", "壁纸", "绘图", "生成一张", "画一张", "图片生成", "生成图像"], "AI绘图", "AI 绘图"),

    # 文档
    (["ppt", "演示文稿", "幻灯片", "做PPT"], "ai-ppt-generate", "PPT 生成"),
    (["视频", "video", "生成视频", "动画", "制作视频"], "video-generator", "视频生成"),
    (["视频笔记", "提取视频", "视频摘要"], "ai-notes-of-video", "视频笔记"),
    (["markdown", "文档", "笔记", "document", "写文档"], "academic-writing", "文档写作"),
    (["学术", "论文", "arxiv", "研究", "deep research"], "academic-deep-research", "学术深度研究"),

    # 金融
    (["股票", "股价", "a股", "基金", "行情", "量化", "A股分析"], "A股量化-AkShare", "A股量化分析"),

    # 邮件/通信
    (["邮件", "email", "发邮件", "收邮件"], "邮件管理", "邮件管理"),

    # 开发/编程
    (["代码", "编程", "coding", "写代码", "开发", "写程序"], "前端开发", "前端开发"),
    (["3D", "建模", "blender", "打印", "雕刻"], "3D-Maker-Companion", "3D打印与建模"),

    # 工具类
    (["密码", "密码管理", "1password", "密钥"], "1password", "密码管理"),
    (["截图", "capture", "屏幕截图"], "截图工具", "截图工具"),
]


@dataclass
class RouteResult:
    """路由结果"""
    skill_name: str
    skill_type: str  # "mcp_core" | "workbuddy" | "workflow" | "unknown"
    confidence: float  # 0.0 ~ 1.0
    description: str
    extracted_params: Dict[str, Any] = field(default_factory=dict)
    original_query: str = ""


class NLRouter:
    """自然语言 Skill 路由器"""

    def __init__(self):
        self.history_file = Path("/python/MCP_Core/data/nl_router_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_history()

    def _load_history(self):
        """加载历史路由记录（用于学习）"""
        self.history = []
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    def _save_history(self, query: str, result: RouteResult):
        """保存路由历史"""
        self.history.append({
            "query": query,
            "skill": result.skill_name,
            "type": result.skill_type,
            "confidence": result.confidence,
        })
        if len(self.history) > 500:
            self.history = self.history[-500:]
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def route(self, query: str) -> RouteResult:
        """主路由入口：接收自然语言，返回最匹配的 Skill"""
        query_lower = query.lower()
        best_match = None
        best_score = 0.0

        # ── 1. 精确关键词匹配（MCP Core Skills）──────────────────────────────
        for keywords, skill_name, desc in INTENT_MAP:
            score = self._keyword_score(query_lower, keywords)
            if score > best_score:
                best_score = score
                best_match = RouteResult(
                    skill_name=skill_name,
                    skill_type="mcp_core",
                    confidence=score,
                    description=desc,
                    original_query=query,
                )

        # ── 2. WorkBuddy Skills 匹配 ──────────────────────────────────────────
        for keywords, skill_name, desc in WORKBUDDY_INTENT_MAP:
            if skill_name is None:
                continue
            score = self._keyword_score(query_lower, keywords)
            if score > best_score:
                best_score = score
                best_match = RouteResult(
                    skill_name=skill_name,
                    skill_type="workbuddy",
                    confidence=score,
                    description=desc,
                    original_query=query,
                )

        # ── 3. 模糊匹配（历史记录学习）──────────────────────────────────────
        if best_score < 0.3 and self.history:
            fuzzy_match = self._fuzzy_history_match(query)
            if fuzzy_match and fuzzy_match[1] > best_score:
                skill_name, score = fuzzy_match
                best_score = score
                best_match = RouteResult(
                    skill_name=skill_name,
                    skill_type="learned",
                    confidence=score,
                    description=f"从历史记录学习: {skill_name}",
                    original_query=query,
                )

        # ── 4. 兜底：参数提取 ────────────────────────────────────────────────
        if best_match:
            best_match.extracted_params = self._extract_params(query, best_match.skill_name)
            self._save_history(query, best_match)
            return best_match

        return RouteResult(
            skill_name="unknown",
            skill_type="unknown",
            confidence=0.0,
            description="未能识别意图，请尝试更具体的描述",
            original_query=query,
        )

    def _keyword_score(self, query: str, keywords: List[str]) -> float:
        """计算关键词匹配分数"""
        score = 0.0
        for kw in keywords:
            if kw.lower() in query:
                score = max(score, min(1.0, len(kw) / 10 + 0.3))
        return score

    def _fuzzy_history_match(self, query: str) -> Optional[Tuple[str, float]]:
        """从历史记录中模糊匹配"""
        if not self.history:
            return None
        queries = [h["query"] for h in self.history]
        matches = difflib.get_close_matches(query, queries, n=1, cutoff=0.5)
        if matches:
            matched_query = matches[0]
            for h in reversed(self.history):
                if h["query"] == matched_query:
                    return h["skill"], 0.5
        return None

    def _extract_params(self, query: str, skill_name: str) -> Dict[str, Any]:
        """从自然语言中提取参数"""
        params = {}
        path_pattern = r'[A-Za-z]:\\[^\s\'\u201c\u201d\uff08\uff09]+|/[^\s\'\u201c\u201d\uff08\uff09]+'
        paths = re.findall(path_pattern, query)
        if paths:
            params["path"] = paths[0]
            if len(paths) > 1:
                params["dest"] = paths[1]
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        ips = re.findall(ip_pattern, query)
        if ips:
            params["target_ip"] = ips[0]
        numbers = re.findall(r'\b\d+\b', query)
        if numbers:
            params["count"] = int(numbers[0])
        quoted = re.findall(r'["\']([^"\']+)["\']', query)
        if not quoted:
            keywords_after = re.findall(r'(?:搜索|查找|找|search|安装|分析)\s+(.+?)(?:的|$)', query)
            if keywords_after:
                quoted = keywords_after
        if quoted:
            params["query"] = quoted[0]
            params["keyword"] = quoted[0]
        return params

    def suggest_skills(self, partial_query: str, top_n: int = 5) -> List[Dict]:
        """根据部分输入提供 Skill 建议（用于自动补全）"""
        suggestions = []
        partial_lower = partial_query.lower()
        for keywords, skill_name, desc in INTENT_MAP + WORKBUDDY_INTENT_MAP:
            if skill_name is None:
                continue
            score = self._keyword_score(partial_lower, keywords)
            if score > 0:
                suggestions.append({
                    "skill": skill_name,
                    "description": desc,
                    "score": score,
                    "keywords": keywords[:3],
                })
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions[:top_n]

    def list_all_skills(self) -> Dict[str, List[Dict]]:
        """列出所有可用 Skill（按类型分组）"""
        result = {"mcp_core_skills": [], "workbuddy_skills": []}
        for keywords, skill_name, desc in INTENT_MAP:
            result["mcp_core_skills"].append({
                "name": skill_name,
                "description": desc,
                "trigger_words": keywords[:5],
            })
        for keywords, skill_name, desc in WORKBUDDY_INTENT_MAP:
            if skill_name:
                result["workbuddy_skills"].append({
                    "name": skill_name,
                    "description": desc,
                    "trigger_words": keywords[:5],
                })
        return result


# ─── MCP Tool 接口（供 TRAE/MCP 调用）───────────────────────────────────────
_router_instance = None


def get_router() -> NLRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = NLRouter()
    return _router_instance


def nl_route(query: str) -> Dict:
    """自然语言路由入口，供外部调用"""
    router = get_router()
    result = router.route(query)
    return {
        "success": True,
        "skill_name": result.skill_name,
        "skill_type": result.skill_type,
        "confidence": result.confidence,
        "description": result.description,
        "extracted_params": result.extracted_params,
        "original_query": result.original_query,
    }


def nl_suggest(partial_query: str) -> Dict:
    """自然语言建议，供外部调用"""
    router = get_router()
    suggestions = router.suggest_skills(partial_query)
    return {"success": True, "suggestions": suggestions}


def nl_list_skills() -> Dict:
    """列出所有可用 Skill"""
    router = get_router()
    skills = router.list_all_skills()
    return {"success": True, "skills": skills}


if __name__ == "__main__":
    router = NLRouter()
    test_queries = [
        "帮我搜索 GitHub 上有没有好的 AI 代理框架",
        "把 D:/test.py 传到另一台电脑",
        "系统太慢了，帮我优化一下内存",
        "记录一下：我今天的项目路径是 D:/MyProject",
        "天气怎么样",
        "生成一张赛博朋克风格的图片",
        "帮我备份 /python 文件夹",
        "GitHub下载太慢了，帮我用镜像",
        "分析一下这个项目的分支结构",
        "安装这个 GitHub 项目为 Skill",
    ]
    print("=== 自然语言路由测试 ===\n")
    for q in test_queries:
        result = router.route(q)
        print(f"输入: {q}")
        print(f"  → Skill: {result.skill_name} ({result.skill_type})")
        print(f"  → 置信度: {result.confidence:.2f}")
        print(f"  → 参数: {result.extracted_params}")
        print()
