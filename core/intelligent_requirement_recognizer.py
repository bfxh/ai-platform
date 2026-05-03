#!/usr/bin/env python3
"""
/python 智能需求识别系统
自动理解用户需求，推荐合适的工具
"""

import json
import re
from typing import Dict, List, Optional, Tuple


class IntelligentRequirementRecognizer:
    """智能需求识别器"""

    def __init__(self):
        # 需求模式库
        self.patterns = {
            # 代码相关
            "code_generation": {
                "keywords": ["写代码", "生成代码", "编程", "code", "python", "javascript", "写个", "帮我写"],
                "tools": ["code", "skill"],
            },
            "code_analysis": {
                "keywords": ["分析代码", "审查代码", "检查代码", "review", "analyze", "优化代码"],
                "tools": ["code_analyzer", "skill"],
            },
            "code_fix": {
                "keywords": ["修复代码", "bug", "错误", "fix", "修复", "报错"],
                "tools": ["code_fix", "skill"],
            },
            # 3D建模相关
            "3d_modeling": {
                "keywords": ["3d", "建模", "blender", "ue5", "unity", "godot", "三维", "模型"],
                "tools": ["blender_mcp", "ue_mcp", "unity_mcp", "godot_mcp"],
            },
            "game_development": {
                "keywords": ["游戏", "game", "开发", "制作游戏"],
                "tools": ["godot_mcp", "ue_mcp", "unity_mcp"],
            },
            # 系统相关
            "system_management": {
                "keywords": ["系统", "管理", "配置", "设置", "system", "config"],
                "tools": ["system_manager", "skill"],
            },
            "file_operation": {
                "keywords": ["文件", "读取", "写入", "复制", "移动", "file", "read", "write"],
                "tools": ["file_tool", "skill"],
            },
            "download": {"keywords": ["下载", "download", "获取", "拉取"], "tools": ["download_manager", "skill"]},
            # AI相关
            "ai_chat": {"keywords": ["聊天", "对话", "说", "告诉", "chat", "talk"], "tools": ["ai_chat", "skill"]},
            "ai_search": {"keywords": ["搜索", "查找", "查询", "search", "find"], "tools": ["ai_search", "skill"]},
            # 项目相关
            "project_creation": {
                "keywords": ["创建项目", "新建项目", "初始化", "init", "create project"],
                "tools": ["project_manager", "skill"],
            },
            "project_build": {
                "keywords": ["构建", "编译", "build", "compile", "打包"],
                "tools": ["build_tool", "skill"],
            },
            # 测试相关
            "testing": {"keywords": ["测试", "test", "调试", "debug"], "tools": ["test_tool", "skill"]},
        }

        # 工具映射
        _base = Path(os.environ.get("AI_BASE_DIR", Path(__file__).resolve().parent.parent))
        self.tool_mapping = {
            "code": str(_base / "user/skills/code.py"),
            "skill": str(_base / "user/skills"),
            "code_analyzer": str(_base / "user/plugins/code_analyzer.py"),
            "blender_mcp": str(_base / "storage/mcp/JM/blender_mcp.py"),
            "ue_mcp": str(_base / "storage/mcp/JM/ue_mcp.py"),
            "unity_mcp": str(_base / "storage/mcp/JM/unity_mcp.py"),
            "godot_mcp": str(_base / "storage/mcp/JM/godot_mcp.py"),
        }

        # 上下文记忆
        self.context_memory = []
        self.max_context = 10

    def recognize(self, user_input: str) -> Tuple[str, List[str], float]:
        """
        识别用户需求
        返回: (需求类型, 推荐工具列表, 置信度)
        """
        user_input_lower = user_input.lower()

        best_match = None
        best_tools = []
        best_confidence = 0.0

        for requirement_type, pattern_info in self.patterns.items():
            keywords = pattern_info["keywords"]
            tools = pattern_info["tools"]

            # 计算匹配度
            match_count = sum(1 for keyword in keywords if keyword.lower() in user_input_lower)
            confidence = match_count / len(keywords) if keywords else 0

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = requirement_type
                best_tools = tools

        # 如果置信度太低，默认为通用对话
        if best_confidence < 0.1:
            best_match = "general_chat"
            best_tools = ["ai_chat"]
            best_confidence = 0.5

        return best_match, best_tools, best_confidence

    def add_context(self, user_input: str, requirement_type: str):
        """添加上下文记忆"""
        self.context_memory.append({"input": user_input, "type": requirement_type})

        # 保持记忆数量
        if len(self.context_memory) > self.max_context:
            self.context_memory.pop(0)

    def get_context(self) -> List[Dict]:
        """获取上下文记忆"""
        return self.context_memory

    def clear_context(self):
        """清空上下文记忆"""
        self.context_memory = []

    def recommend_tool(self, requirement_type: str) -> Optional[str]:
        """推荐工具"""
        if requirement_type in self.patterns:
            tools = self.patterns[requirement_type]["tools"]
            if tools:
                primary_tool = tools[0]
                return self.tool_mapping.get(primary_tool, primary_tool)
        return None

    def get_all_tools(self) -> Dict[str, str]:
        """获取所有可用工具"""
        return self.tool_mapping


def main():
    """测试函数"""
    recognizer = IntelligentRequirementRecognizer()

    # 测试用例
    test_cases = [
        "帮我写一个Python代码",
        "用Blender创建一个3D模型",
        "修复这个bug",
        "分析一下这个代码",
        "配置一下系统",
        "你好",
    ]

    print("=" * 60)
    print("智能需求识别系统测试")
    print("=" * 60)
    print()

    for test_input in test_cases:
        req_type, tools, confidence = recognizer.recognize(test_input)
        recommended_tool = recognizer.recommend_tool(req_type)

        print(f"输入: {test_input}")
        print(f"  识别类型: {req_type}")
        print(f"  推荐工具: {tools}")
        print(f"  置信度: {confidence:.2f}")
        print(f"  工具路径: {recommended_tool}")
        print()


if __name__ == "__main__":
    main()
