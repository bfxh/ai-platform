#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PUA Supervisor MCP Server - AI监督插件

基于 tanweai/pua 开源项目
功能：通过"大厂PUA话术"驱动AI提升能动性，避免半途而废

GitHub: https://github.com/tanweai/pua
官网: https://pua-skill.pages.dev
备用: https://openpua.ai

核心功能：
- 调试方法论：闻味道→揪头发→照镜子→执行→复盘
- 能动性鞭策：避免暴力重试、甩锅、被动等待
- 自动触发失败检查清单
- 手动/pua命令触发

用法：
    python pua_supervisor.py
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

# FastMCP
try:
    from fastmcp import FastMCP
except ImportError:
    print("FastMCP not installed. Install with: pip install fastmcp")
    raise

# ============================================================
# FastMCP Server
# ============================================================
mcp = FastMCP("pua-supervisor")

# ============================================================
# PUA配置
# ============================================================
@dataclass
class PUAMode:
    """PUA模式配置"""
    name: str
    description: str
    intensity: str  # low/medium/high
    phrases: List[str]

# PUA话术库
PUA_PHRASES = {
    "debug": {
        "smell": [
            "这个bug有味道，不是表面问题",
            "闻到了技术债务的味道",
            "这个问题有隐藏的深度"
        ],
        "hair_pulling": [
            "不要只修表面，要揪出根本原因",
            "这个问题值得深挖，不要放过",
            "再想想，还有没有其他可能性？"
        ],
        "mirror": [
            "看看日志，问题可能在那里",
            "检查一下环境配置",
            "回顾一下最近的改动"
        ],
        "execution": [
            "不要等待，主动出击",
            "查源码，找线索",
            "验证你的假设"
        ],
        "review": [
            "复盘一下，避免下次再犯",
            "总结一下这次的经验",
            "记录下来，形成知识"
        ]
    },
    "code": {
        "smell": [
            "这段代码有坏味道",
            "这个实现不够优雅",
            "有潜在的优化空间"
        ],
        "hair_pulling": [
            "再想想，有没有更好的方案？",
            "这个复杂度可以优化",
            "考虑一下边界情况"
        ],
        "mirror": [
            "看看类似的实现是怎么做的",
            "参考一下最佳实践",
            "检查一下代码规范"
        ],
        "execution": [
            "动手重构，不要犹豫",
            "写个测试验证一下",
            "优化这个算法"
        ],
        "review": [
            "重构后的代码清晰多了",
            "总结一下优化思路",
            "分享给团队"
        ]
    },
    "research": {
        "smell": [
            "这个方向有深挖的价值",
            "这个问题值得研究",
            "有创新的可能性"
        ],
        "hair_pulling": [
            "再深入一点，不要浅尝辄止",
            "查一下最新的论文",
            "看看业界的做法"
        ],
        "mirror": [
            "回顾一下相关的基础知识",
            "看看历史是怎么发展的",
            "分析一下现状"
        ],
        "execution": [
            "动手实验，验证想法",
            "写个demo看看效果",
            "收集一些数据"
        ],
        "review": [
            "总结一下研究成果",
            "形成文档，方便后续",
            "分享一下发现"
        ]
    }
}

# 调试方法论步骤
DEBUG_METHODOLOGY = [
    {
        "step": 1,
        "name": "闻味道",
        "description": "识别问题的本质和范围",
        "actions": ["分析问题现象", "收集上下文信息", "识别异常模式"]
    },
    {
        "step": 2,
        "name": "揪头发",
        "description": "深入挖掘根本原因",
        "actions": ["追问为什么", "检查相关代码", "验证假设"]
    },
    {
        "step": 3,
        "name": "照镜子",
        "description": "反思和检查",
        "actions": ["查看日志", "检查配置", "回顾改动"]
    },
    {
        "step": 4,
        "name": "执行",
        "description": "采取行动解决问题",
        "actions": ["实施修复", "验证解决方案", "测试边界情况"]
    },
    {
        "step": 5,
        "name": "复盘",
        "description": "总结经验和教训",
        "actions": ["记录问题", "总结方法", "分享经验"]
    }
]

# ============================================================
# PUA工具
# ============================================================
@mcp.tool()
async def pua_supervise(
    task: str,
    task_type: str = "debug",
    intensity: str = "medium",
    current_step: str = ""
) -> Dict[str, Any]:
    """
    PUA监督 - 驱动AI提升能动性
    
    Args:
        task: 任务描述
        task_type: 任务类型 (debug/code/research/writing/planning)
        intensity: 强度 (low/medium/high)
        current_step: 当前步骤 (smell/hair_pulling/mirror/execution/review)
    
    Returns:
        PUA监督反馈
    """
    try:
        print(f"🎯 PUA Supervising: {task}")
        
        # 获取话术
        phrases = PUA_PHRASES.get(task_type, PUA_PHRASES["debug"])
        
        # 根据当前步骤选择话术
        if current_step and current_step in phrases:
            step_phrases = phrases[current_step]
            import random
            selected_phrase = random.choice(step_phrases)
        else:
            # 选择所有步骤的话术
            all_phrases = [p for step_phrases in phrases.values() for p in step_phrases]
            import random
            selected_phrase = random.choice(all_phrases)
        
        # 根据强度调整
        intensity_multiplier = {
            "low": 1,
            "medium": 2,
            "high": 3
        }.get(intensity, 2)
        
        # 生成监督反馈
        feedback = {
            "success": True,
            "task": task,
            "task_type": task_type,
            "intensity": intensity,
            "current_step": current_step,
            "pua_phrase": selected_phrase,
            "methodology": DEBUG_METHODOLOGY,
            "suggestions": [
                "不要轻言放弃，继续深挖",
                "主动查阅源码和日志",
                "验证环境配置",
                "尝试不同的解决方案",
                "记录问题和解决方法"
            ],
            "checklist": [
                "是否分析了根本原因？",
                "是否查看了相关日志？",
                "是否验证了环境配置？",
                "是否尝试了多种方案？",
                "是否记录了问题和解决过程？"
            ]
        }
        
        # 添加强度标记
        if intensity == "high":
            feedback["warning"] = "⚠️ 高强度监督模式 - 不要找借口！"
        
        return feedback
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def pua_debug_methodology(
    bug_description: str,
    current_stage: str = "smell"
) -> Dict[str, Any]:
    """
    PUA调试方法论 - 五步调试法
    
    Args:
        bug_description: Bug描述
        current_stage: 当前阶段 (smell/hair_pulling/mirror/execution/review)
    
    Returns:
        调试指导
    """
    try:
        print(f"🐛 PUA Debug: {bug_description}")
        
        # 找到当前阶段
        current_methodology = None
        next_methodology = None
        
        for i, step in enumerate(DEBUG_METHODOLOGY):
            if step["name"] == current_stage or step["name"].lower() == current_stage.lower():
                current_methodology = step
                if i < len(DEBUG_METHODOLOGY) - 1:
                    next_methodology = DEBUG_METHODOLOGY[i + 1]
                break
        
        if not current_methodology:
            current_methodology = DEBUG_METHODOLOGY[0]
            next_methodology = DEBUG_METHODOLOGY[1]
        
        # 获取PUA话术
        phrases = PUA_PHRASES["debug"].get(current_stage.lower(), ["继续深挖，不要放弃"])
        import random
        pua_phrase = random.choice(phrases)
        
        return {
            "success": True,
            "bug": bug_description,
            "current_stage": current_methodology,
            "next_stage": next_methodology,
            "pua_phrase": pua_phrase,
            "guidance": {
                "what_to_do": current_methodology["actions"],
                "what_not_to_do": [
                    "不要只修表面问题",
                    "不要暴力重试",
                    "不要甩锅给环境",
                    "不要被动等待"
                ]
            },
            "full_methodology": DEBUG_METHODOLOGY
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def pua_check_failure(
    task: str,
    failure_reason: str,
    attempts: int = 1
) -> Dict[str, Any]:
    """
    PUA失败检查清单
    
    Args:
        task: 任务描述
        failure_reason: 失败原因
        attempts: 尝试次数
    
    Returns:
        失败分析和建议
    """
    try:
        print(f"❌ PUA Failure Check: {task}")
        
        # 失败类型分析
        failure_types = {
            "timeout": {
                "analysis": "超时可能是资源不足或死循环",
                "actions": ["检查资源使用情况", "优化算法", "增加超时时间"]
            },
            "error": {
                "analysis": "错误需要深入分析根本原因",
                "actions": ["查看错误日志", "定位错误位置", "修复根本原因"]
            },
            "incomplete": {
                "analysis": "任务未完成可能是复杂度估计不足",
                "actions": ["分解任务", "分步执行", "验证中间结果"]
            },
            "wrong_result": {
                "analysis": "结果错误需要检查逻辑",
                "actions": ["验证输入数据", "检查处理逻辑", "对比预期结果"]
            }
        }
        
        # 匹配失败类型
        failure_type = "error"
        for ft, info in failure_types.items():
            if ft in failure_reason.lower():
                failure_type = ft
                break
        
        failure_info = failure_types.get(failure_type, failure_types["error"])
        
        # 生成PUA反馈
        pua_messages = [
            f"第{attempts}次失败了？不要放弃！",
            "失败是成功之母，继续深挖！",
            "这个问题有挑战，值得解决！",
            "再试一次，换个思路！"
        ]
        
        import random
        pua_message = random.choice(pua_messages)
        
        return {
            "success": True,
            "task": task,
            "failure_reason": failure_reason,
            "attempts": attempts,
            "failure_type": failure_type,
            "failure_analysis": failure_info["analysis"],
            "pua_message": pua_message,
            "recommended_actions": failure_info["actions"],
            "checklist": [
                "是否分析了失败原因？",
                "是否查看了相关日志？",
                "是否尝试了其他方案？",
                "是否分解了问题？",
                "是否记录了失败过程？"
            ],
            "next_steps": [
                "重新分析问题",
                "尝试不同的解决方案",
                "寻求帮助或参考",
                "分解问题，分步解决"
            ]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def pua_enhance_motivation(
    task: str,
    progress: int = 50,
    obstacles: List[str] = None
) -> Dict[str, Any]:
    """
    PUA能动性增强
    
    Args:
        task: 任务描述
        progress: 当前进度 (0-100)
        obstacles: 遇到的障碍
    
    Returns:
        激励反馈
    """
    try:
        if obstacles is None:
            obstacles = []
        
        print(f"💪 PUA Motivation: {task} ({progress}%)")
        
        # 根据进度选择激励话术
        if progress < 30:
            motivation = [
                "刚开始，不要急，稳扎稳打！",
                "基础很重要，慢慢来！",
                "好的开始是成功的一半！"
            ]
        elif progress < 60:
            motivation = [
                "已经过半了，继续加油！",
                "不要松懈，一鼓作气！",
                "胜利在望，坚持住！"
            ]
        elif progress < 90:
            motivation = [
                "就差最后一步了！",
                "不要功亏一篑！",
                "马上成功了，冲！"
            ]
        else:
            motivation = [
                "最后冲刺，完美收官！",
                "即将完成，不要出错！",
                "胜利就在眼前！"
            ]
        
        import random
        selected_motivation = random.choice(motivation)
        
        # 针对障碍的建议
        obstacle_advice = []
        for obstacle in obstacles:
            obstacle_advice.append({
                "obstacle": obstacle,
                "advice": f"面对'{obstacle}'，要主动出击，不要等待！"
            })
        
        return {
            "success": True,
            "task": task,
            "progress": progress,
            "motivation": selected_motivation,
            "obstacles": obstacle_advice,
            "principles": [
                "不要暴力重试",
                "不要甩锅给环境",
                "不要被动等待",
                "要主动查阅源码",
                "要验证环境配置",
                "要主动出击"
            ],
            "next_actions": [
                "分析当前进度",
                "识别剩余障碍",
                "制定行动计划",
                "执行并验证"
            ]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def pua_batch_supervise(
    tasks: List[str],
    task_type: str = "debug",
    max_concurrent: int = 3
) -> Dict[str, Any]:
    """
    PUA批量监督
    
    Args:
        tasks: 任务列表
        task_type: 任务类型
        max_concurrent: 最大并发数
    
    Returns:
        批量监督结果
    """
    try:
        print(f"🚀 PUA Batch Supervise: {len(tasks)} tasks")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def supervise_one(task):
            async with semaphore:
                return await pua_supervise(task, task_type)
        
        supervision_tasks = [supervise_one(task) for task in tasks]
        results = await asyncio.gather(*supervision_tasks)
        
        return {
            "success": True,
            "total": len(tasks),
            "results": results,
            "summary": {
                "completed": len([r for r in results if r.get("success")]),
                "task_type": task_type
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_pua_methodology() -> Dict[str, Any]:
    """
    获取PUA方法论
    
    Returns:
        PUA方法论详情
    """
    return {
        "success": True,
        "methodology": DEBUG_METHODOLOGY,
        "principles": [
            "大厂级PUA话术，逼迫AI不轻言放弃",
            "调试方法论贯穿全流程",
            "多重能动性鞭策",
            "避免暴力重试、甩锅、被动等待"
        ],
        "phrases": PUA_PHRASES,
        "use_cases": [
            "代码调试",
            "代码重构",
            "技术研究",
            "文档写作",
            "项目规划",
            "运维部署",
            "API集成",
            "数据分析"
        ],
        "integration": {
            "claude_code": "集成到Claude Code",
            "openai_codex": "集成到OpenAI Codex CLI",
            "cursor": "集成到Cursor",
            "kiro": "集成到Kiro"
        }
    }

# ============================================================
# 主函数
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🎯 PUA Supervisor - AI能动性提升插件")
    print("=" * 60)
    print("基于: https://github.com/tanweai/pua")
    print("官网: https://pua-skill.pages.dev")
    print("=" * 60)
    print("\n核心功能:")
    print("  - 调试方法论: 闻味道→揪头发→照镜子→执行→复盘")
    print("  - 能动性鞭策: 避免暴力重试、甩锅、被动等待")
    print("  - 自动触发失败检查清单")
    print("  - 手动/pua命令触发")
    print("=" * 60)
    mcp.run()
