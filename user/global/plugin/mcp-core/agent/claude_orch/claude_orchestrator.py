#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude 编排代理 (Claude Orchestrator Agent)

负责:
1. 接收上层任务请求
2. 用 AI 模型分析任务意图
3. 根据路由规则将任务委派给合适的子代理
4. 汇总子代理返回的结果
5. 处理回退逻辑（主模型不可用时切换到本地 Ollama）

数据流:
  Dispatcher → ClaudeOrchestrator → [意图分析] → 路由匹配 → 子代理执行 → 结果汇总

用法:
    from agent.claude_orch.claude_orchestrator import ClaudeOrchestrator

    orch = ClaudeOrchestrator()
    orch.initialize()
    result = orch.execute({"task": "创建 React Login 组件"})
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.base import Agent, AgentType, AgentStatus, get_agent_manager

# 导入 TRAE IDE Bridge
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "core"))
try:
    from trae_ide_bridge import TRAEIDEBridge, get_bridge
except ImportError:
    TRAEIDEBridge = None
    get_bridge = None


class ClaudeOrchestrator(Agent):
    """Claude 编排代理 — 任务意图分析与路由分发"""

    name = "claude_orchestrator"
    description = "Claude 编排代理 — 分析任务意图，路由到合适的子代理执行"
    version = "1.1.0"
    author = "Multica AI Platform"
    agent_type = AgentType.SPECIALIZED
    skills = ["intent_analysis", "task_routing", "context_injection"]
    abilities = {
        "intent_analysis": 95,
        "task_routing": 90,
        "context_injection": 85,
        "result_aggregation": 80,
        "fallback_handling": 85,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # 路径
        self.orch_dir = Path(__file__).resolve().parent
        self.python_dir = self.orch_dir.parent.parent.parent.parent.parent

        # 配置
        self.primary_model = self.config.get("model", {}).get("primary", {})
        self.fallback_model = self.config.get("model", {}).get("fallback", {})
        self.fallback_threshold = self.config.get("fallback_threshold", 3)
        self.fallback_count = 0

        # 路由
        self.routing_rules: List[dict] = []
        self.default_agent = self.config.get("routing", {}).get(
            "default_agent", "trae_control"
        )
        self.max_analysis_time = self.config.get("routing", {}).get("max_analysis_time", 30)

        # 执行
        self.max_retries = self.config.get("execution", {}).get("max_retries", 2)
        self.sub_agent_timeout = self.config.get("execution", {}).get("sub_agent_timeout", 120)

        # TRAE IDE Bridge
        self._bridge = None

        # 加载路由规则
        self._load_routing_rules()

    @property
    def bridge(self) -> Optional["TRAEIDEBridge"]:
        """延迟初始化 TRAE IDE Bridge"""
        if self._bridge is None and TRAEIDEBridge is not None:
            try:
                self._bridge = TRAEIDEBridge()
            except Exception as e:
                self.logger.warning(f"TRAE IDE Bridge 初始化失败: {e}")
        return self._bridge

    def _load_routing_rules(self):
        """加载路由规则配置"""
        rules_path = self.orch_dir / "routing_rules.yaml"
        try:
            import yaml
            with open(rules_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            self.routing_rules = config.get("rules", [])
            if config.get("default"):
                self.default_agent = config["default"].get("agent", self.default_agent)
            self.logger.info(f"加载路由规则: {len(self.routing_rules)} 条, 默认代理: {self.default_agent}")
        except Exception as e:
            self.logger.error(f"加载路由规则失败: {e}")
            self.routing_rules = []

    # ============================================================
    # 核心方法 — execute (Agent 基类要求实现)
    # ============================================================

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行编排任务

        task 格式:
            {"task": "用户输入的自然语言任务描述",
             "task_type": "orchestrate",
             "context": {...}}  # 可选上下文

        返回:
            {"success": bool,
             "intent": str,           # 识别的意图
             "agent": str,            # 路由到的代理
             "result": dict,          # 子代理执行结果
             "summary": str}          # 汇总说明
        """
        if not self._initialized:
            return {"success": False, "error": "编排代理未初始化"}

        task_text = task.get("task") or task.get("command") or str(task)
        context = task.get("context", {})

        self.logger.info(f"接收任务: {task_text[:100]}")

        # 步骤 1: 分析意图
        intent = self._analyze_intent(task_text)

        # 步骤 2: 路由到目标代理
        target_agent = self._route_intent(intent)

        # 步骤 3: 准备子任务上下文
        sub_task = self._prepare_sub_task(task_text, intent, context)

        # 步骤 4: 执行子代理任务
        agent_result = self._execute_on_agent(target_agent, sub_task)

        # 步骤 5: 汇总结果
        summary = self._summarize_result(intent, target_agent, agent_result)

        return {
            "success": agent_result.get("success", False),
            "intent": intent,
            "agent": target_agent,
            "result": agent_result,
            "summary": summary,
        }

    # ============================================================
    # 意图分析
    # ============================================================

    def _analyze_intent(self, task_text: str) -> str:
        """分析任务意图

        优先使用 LLM 分析，失败时回退到关键词匹配。
        """
        # 方法 1: 关键词快速匹配 (无 LLM 依赖)
        intent = self._keyword_match_intent(task_text)
        if intent:
            self.logger.info(f"关键词匹配意图: {intent}")
            return intent

        # 方法 2: LLM 意图分析
        try:
            intent = self._llm_analyze_intent(task_text)
            if intent:
                return intent
        except Exception as e:
            self.logger.warning(f"LLM 意图分析失败: {e}")
            self.fallback_count += 1

        # 回退: 默认意图
        self.logger.info(f"无法分析意图，使用默认: code_generation")
        return "code_generation"

    def _keyword_match_intent(self, text: str) -> Optional[str]:
        """基于关键词匹配意图"""
        text_lower = text.lower()
        best_match = None
        best_priority = -1

        for rule in self.routing_rules:
            keywords = rule.get("keywords", [])
            for kw in keywords:
                if kw.lower() in text_lower:
                    priority = rule.get("priority", 0)
                    if priority > best_priority:
                        best_priority = priority
                        best_match = rule.get("intent")

        return best_match

    def _llm_analyze_intent(self, task_text: str) -> Optional[str]:
        """使用 LLM 分析意图"""
        # 构建意图列表
        intents_desc = "\n".join([
            f"  - {r['intent']}: {r.get('context', '')[:80]}"
            for r in self.routing_rules
        ])

        prompt = f"""分析以下用户请求的意图。从下面的意图列表中选择最匹配的一个。

用户请求: {task_text}

可用意图:
{intents_desc}

请只回复意图名称，不要加任何其他文字。回复格式:
intent: <意图名>"""

        response = self._call_ai(prompt)

        # 解析响应
        for line in response.strip().split("\n"):
            if "intent:" in line.lower():
                intent = line.split(":", 1)[1].strip().lower()
                # 验证意图有效性
                valid_intents = [r["intent"] for r in self.routing_rules]
                if intent in valid_intents:
                    return intent

        # 尝试直接匹配
        response_lower = response.strip().lower()
        for intent in [r["intent"] for r in self.routing_rules]:
            if intent in response_lower:
                return intent

        return None

    def _call_ai(self, prompt: str) -> str:
        """调用 AI 模型

        优先 Anthropic Claude → 回退 Ollama 本地模型
        """
        # 尝试调用核心 AI 接口
        try:
            sys.path.insert(0, str(self.python_dir))
            from core.ai_new import AI

            # 使用主模型
            if self.fallback_count < self.fallback_threshold:
                try:
                    ai = AI(provider="anthropic")
                    result = ai(prompt, max_tokens=100)
                    return str(result)
                except Exception:
                    self.fallback_count += 1

            # 回退到 Ollama
            if self.fallback_count >= self.fallback_threshold:
                self.logger.info("切换到 Ollama 回退模型")
                try:
                    ai = AI(provider="ollama")
                    result = ai(prompt, max_tokens=100)
                    return str(result)
                except Exception as e:
                    self.logger.warning(f"Ollama 调用失败: {e}")

        except ImportError:
            pass

        # 最终回退: 返回空，让关键词匹配处理
        return ""

    # ============================================================
    # 路由
    # ============================================================

    def _route_intent(self, intent: str) -> str:
        """根据意图路由到目标代理"""
        for rule in self.routing_rules:
            if rule.get("intent") == intent:
                agent = rule.get("agent", self.default_agent)
                self.logger.info(f"路由: {intent} → {agent}")
                return agent

        self.logger.info(f"未匹配意图 {intent}，使用默认代理: {self.default_agent}")
        return self.default_agent

    def _prepare_sub_task(self, task_text: str, intent: str,
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """准备子代理任务"""
        # 查找对应规则以获取上下文
        rule_context = ""
        for rule in self.routing_rules:
            if rule.get("intent") == intent:
                rule_context = rule.get("context", "")
                break

        sub_task = {
            "task_type": "orchestrated",
            "command": task_text,
            "intent": intent,
            "context": rule_context,
            "parent_agent": self.name,
        }

        # 根据意图类型构造子代理可理解的 task
        if intent in ("code_generation", "code_modification"):
            sub_task["task_type"] = "trae_command"
        elif intent == "file_operation":
            sub_task["task_type"] = "file_operation"
        elif intent == "terminal_command":
            sub_task["task_type"] = "execute_command"
        elif intent == "code_analysis":
            sub_task["task_type"] = "code_analysis"
        elif intent == "desktop_automation":
            sub_task["task_type"] = "trae_command"

        # 合并用户上下文
        if context:
            sub_task["context"] = {**({"rule_context": rule_context} if rule_context else {}),
                                   **context}

        return sub_task

    # ============================================================
    # 执行
    # ============================================================

    def _execute_on_agent(self, agent_name: str,
                          task: Dict[str, Any]) -> Dict[str, Any]:
        """在目标代理上执行任务

        根据代理名称，通过不同路径执行:
        - trae_control → TRAEControlAgent.handle_task()
        - 其他 → 尝试通过 AgentManager 查找
        """
        for attempt in range(self.max_retries + 1):
            try:
                # 路径 1: TRAE Control 代理
                if agent_name == "trae_control":
                    return self._execute_trae_control(task)

                # 路径 2: TRAE Agent
                elif agent_name == "trae_agent":
                    return self._execute_trae_agent(task)

                # 路径 3: Qoder (代码分析)
                elif agent_name == "qoder":
                    return self._execute_qoder(task)

                # 路径 4: 通过 AgentManager 查找
                else:
                    return self._execute_generic_agent(agent_name, task)

            except Exception as e:
                self.logger.error(
                    f"代理 {agent_name} 执行失败 (尝试 {attempt+1}/{self.max_retries+1}): {e}"
                )
                if attempt < self.max_retries:
                    time.sleep(1)
                else:
                    return {"success": False, "error": str(e),
                            "agent": agent_name, "attempts": attempt + 1}

        return {"success": False, "error": "已达最大重试次数", "agent": agent_name}

    def _execute_trae_control(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行 TRAE Control 代理任务"""
        try:
            sys.path.insert(0, str(self.orch_dir.parent))
            from trae_control import get_tra_e_agent
            trae = get_tra_e_agent()
            command = task.get("command", task.get("task", ""))
            return trae.handle_task({
                "type": task.get("task_type", "execute_command"),
                "command": command,
                **task
            })
        except Exception as e:
            self.logger.warning(f"TRAE Control 代理失败: {e}")
            return self._execute_via_bridge(task)

    def _execute_trae_agent(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行 TRAE Agent 任务"""
        try:
            sys.path.insert(0, str(self.orch_dir.parent))
            from trae_agent import TRAEAgent
            agent = TRAEAgent()
            return agent.execute(task)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_qoder(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Qoder 代码分析任务"""
        try:
            cmd = task.get("command", task.get("task", ""))
            result = subprocess.run(
                ["python", str(self.python_dir / "user" / "global" / "plugin" /
                               "mcp-core" / "agent" / "trae_agent.py")],
                input=json.dumps(task),
                capture_output=True,
                text=True,
                timeout=self.sub_agent_timeout,
                cwd=str(self.python_dir),
            )
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            return {"success": False, "error": result.stderr[:16384]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_generic_agent(self, agent_name: str,
                               task: Dict[str, Any]) -> Dict[str, Any]:
        """通过 AgentManager 执行通用代理"""
        try:
            manager = get_agent_manager()
            agent = manager.get_agent(agent_name)
            if agent:
                return agent.execute(task)
            return {"success": False, "error": f"代理未找到: {agent_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_via_bridge(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """通过 TRAE IDE Bridge 直接执行 (回退路径)

        当 trae_control 代理不可用时，直接调用 bridge 执行基本操作。
        """
        bridge = self.bridge
        if bridge is None:
            return {"success": False, "error": "TRAE IDE Bridge 不可用"}

        command = task.get("command", task.get("task", ""))
        task_type = task.get("task_type", "")

        if task_type in ("write_file", "code_generation"):
            # 提取文件路径和内容 (简单的启发式提取)
            lines = command.split("\n")
            file_path = task.get("file_path", "generated_code.py")
            content = command
            return bridge.write_code(file_path, content)

        elif task_type in ("read_file", "file_operation"):
            file_path = task.get("file_path", command.split()[-1] if command else "")
            return bridge.read_file(file_path)

        elif task_type in ("execute_command", "terminal_command"):
            return bridge.run_command(command)

        else:
            # 默认尝试在 IDE 中执行
            bridge.focus_ide()
            return {"success": True,
                    "message": f"已聚焦 TRAE IDE，等待进一步指令: {command[:100]}"}

    # ============================================================
    # 结果汇总
    # ============================================================

    def _summarize_result(self, intent: str, agent: str,
                          result: Dict[str, Any]) -> str:
        """汇总执行结果"""
        if result.get("success"):
            output = result.get('message', result.get('result', result.get('output', '')))
            return f"[{intent}] → {agent} 执行成功。{output}"
        else:
            error = result.get('error', result.get('message', '未知错误'))
            return f"[{intent}] → {agent} 执行失败: {error}"

    # ============================================================
    # 生命周期
    # ============================================================

    def _do_initialize(self) -> bool:
        """初始化编排代理"""
        self._load_routing_rules()
        # 预热 TRAE IDE Bridge
        if self.bridge:
            status = self.bridge.get_status()
            self.logger.info(f"TRAE IDE 状态: {status['status']}")
        self.fallback_count = 0
        return True

    def _enhance_abilities(self) -> None:
        """升级时增强能力"""
        self.abilities["intent_analysis"] = min(self.abilities["intent_analysis"] + 2, 100)
        self.abilities["task_routing"] = min(self.abilities["task_routing"] + 2, 100)
        self.abilities["context_injection"] = min(self.abilities["context_injection"] + 1, 100)


# ============================================================
# 模块级便捷函数
# ============================================================

_orchestrator_instance = None


def get_orchestrator() -> ClaudeOrchestrator:
    """获取全局编排代理实例"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = ClaudeOrchestrator()
        _orchestrator_instance.initialize()
    return _orchestrator_instance


# ============================================================
# 自测试
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Claude 编排代理 — 自测试")
    print("=" * 60)

    orch = get_orchestrator()

    test_tasks = [
        "创建 React Login 组件，包含用户名密码输入和提交按钮",
        "分析 /python/core/dispatcher.py 的代码质量",
        "读取 README.md 文件",
        "执行 npm install 安装依赖",
        "搜索 Python asyncio 最佳实践",
    ]

    for task_text in test_tasks:
        print(f"\n--- 任务: {task_text[:60]}...")
        intent = orch._analyze_intent(task_text)
        agent = orch._route_intent(intent)
        print(f"  意图: {intent}")
        print(f"  路由: {agent}")

    print("\n" + "=" * 60)
    print("测试完成 (仅分析+路由，未实际执行子代理)")
