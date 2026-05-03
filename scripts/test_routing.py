#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立路由规则测试 — 绕过 agent/base 依赖链，直接验证规则匹配逻辑

用法:
    python scripts/test_routing.py
    python scripts/test_routing.py "创建 React 组件"
"""

import sys
from pathlib import Path

# 路径
_SCRIPT_DIR = Path(__file__).resolve().parent
_BASE_DIR = _SCRIPT_DIR.parent
_RULES_PATH = (_BASE_DIR / "user" / "global" / "plugin" /
               "mcp-core" / "agent" / "claude_orch" / "routing_rules.yaml")


def load_routing_rules():
    """加载路由规则 — 优先 YAML，回退 JSON 解析"""
    try:
        import yaml
        with open(_RULES_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("rules", []), config.get("default", {}).get("agent", "trae_control")
    except ImportError:
        pass

    # 回退: 手动解析 YAML（极简实现，仅支持我们的固定格式）
    return _parse_rules_manual()


def _parse_rules_manual():
    """手动解析 routing_rules.yaml（不依赖 yaml 模块）"""
    rules = []
    default_agent = "trae_control"
    current = {}
    in_context = False

    with open(_RULES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip()

            # 跳过空行和注释
            if not stripped or stripped.strip().startswith("#"):
                continue

            # intent 行
            if stripped.strip().startswith("- intent:"):
                if current and current.get("intent"):
                    rules.append(current)
                current = {"intent": stripped.split(":", 1)[1].strip(),
                           "keywords": [], "agent": "", "priority": 0}
                in_context = False

            elif stripped.strip().startswith("keywords:") and current is not None:
                # 提取方括号内的关键词列表
                bracket = stripped.strip()
                # keywords: [a, b, c]
                if "[" in bracket and "]" in bracket:
                    inner = bracket[bracket.index("[") + 1:bracket.rindex("]")]
                    current["keywords"] = [
                        k.strip().strip("'").strip('"')
                        for k in inner.split(",") if k.strip()
                    ]
                in_context = False

            elif stripped.strip().startswith("agent:") and current is not None:
                current["agent"] = stripped.split(":", 1)[1].strip()
                in_context = False

            elif stripped.strip().startswith("priority:") and current is not None:
                try:
                    current["priority"] = int(stripped.split(":", 1)[1].strip())
                except ValueError:
                    current["priority"] = 0
                in_context = False

            elif stripped.strip().startswith("default:"):
                # 保存最后一个规则再退出
                if current and current.get("intent"):
                    rules.append(current)
                current = None
                in_context = False

            elif stripped.strip().startswith("agent:") and current is None:
                default_agent = stripped.split(":", 1)[1].strip()

    if current and current.get("intent"):
        rules.append(current)

    return rules, default_agent


def match_intent(text: str, rules: list) -> tuple:
    """关键词匹配意图"""
    text_lower = text.lower()
    best_intent = None
    best_agent = None
    best_priority = -1

    for rule in rules:
        for kw in rule.get("keywords", []):
            if kw.lower() in text_lower:
                if rule.get("priority", 0) > best_priority:
                    best_priority = rule["priority"]
                    best_intent = rule["intent"]
                    best_agent = rule["agent"]

    return best_intent, best_agent


# ============================================================
# 测试
# ============================================================

TEST_CASES = [
    # (输入, 期望意图, 期望代理)
    ("创建 React 登录组件，包含用户名和密码输入框", "code_generation", "trae_control"),
    ("修改 dispatcher.py 的扫描逻辑", "code_modification", "trae_control"),
    ("分析这个项目的代码质量", "code_analysis", "qoder"),
    ("读取 README.md 文件", "file_operation", "trae_control"),
    ("执行 npm install 安装依赖", "terminal_command", "trae_control"),
    ("搜索 Python asyncio 教程", "web_research", "trae_web_search"),
    ("截取当前 IDE 窗口", "desktop_automation", "trae_desktop_automation"),
    ("查看系统进程状态", "system_operation", "trae_desktop_automation"),
    ("生成一个 Python Flask 应用", "code_generation", "trae_control"),
    ("修复 base.py 中的 bug", "code_modification", "trae_control"),
    ("审查 dispatcher.py 的安全性", "code_analysis", "qoder"),
    ("新建一个 utils 目录", "file_operation", "trae_control"),
    ("运行 pytest 测试", "terminal_command", "trae_control"),
    ("查找关于 Docker 的资料", "web_research", "trae_web_search"),
    ("帮我写一个快速排序算法", "code_generation", "trae_control"),
    ("重构 dispatcher._dispatch_agent 方法", "code_modification", "trae_control"),
    ("列出当前目录下的文件", "file_operation", "trae_control"),
    ("检查一下 main.py 的代码", "code_analysis", "qoder"),
    ("点击文件菜单", "desktop_automation", "trae_desktop_automation"),
    ("构建 Docker 镜像", "terminal_command", "trae_control"),
]


def main():
    rules, default_agent = load_routing_rules()

    print("=" * 65)
    print(f"  独立路由规则测试")
    print(f"  规则文件: {_RULES_PATH}")
    print(f"  加载规则: {len(rules)} 条")
    print(f"  默认代理: {default_agent}")
    print("=" * 65)

    # 列出规则
    print(f"\n{'意图':<25} {'代理':<30} {'优先级':<8} {'关键词'}")
    print("-" * 90)
    for rule in rules:
        kws = ", ".join(rule.get("keywords", [])[:4])
        if len(rule.get("keywords", [])) > 4:
            kws += f" ... (+{len(rule['keywords']) - 4})"
        print(f"  {rule['intent']:<23} {rule['agent']:<28} "
              f"{rule.get('priority', 0):<8} {kws}")

    # 如果命令行提供了参数，只测试那个
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        intent, agent = match_intent(query, rules)
        print(f"\n输入: {query}")
        print(f"意图: {intent or '(未匹配)'} → 代理: {agent or default_agent}")
        return

    # 否则跑全量测试
    print(f"\n{'测试用例':<55} {'期望意图':<22} {'实际意图':<22} {'结果'}")
    print("-" * 110)

    passed = 0
    failed = 0

    for text, expected_intent, expected_agent in TEST_CASES:
        intent, agent = match_intent(text, rules)
        # 用实际意图判断——但注意有的意图会 fallback
        ok = (intent == expected_intent) if intent else False
        if ok:
            passed += 1
            status = "OK"
        else:
            failed += 1
            status = f"MISMATCH (got: {intent or '(none)'})"

        print(f"  {text[:52]:<53} {expected_intent:<20} "
              f"{intent or '(none)':<20} {status}")

    print("-" * 110)
    print(f"  通过: {passed}/{passed + failed}  "
          f"({100 * passed / (passed + failed):.0f}%)")

    if failed == 0:
        print(f"\n  所有路由规则工作正常!")
    else:
        print(f"\n  注意: {failed} 个不匹配")
        print(f"  部分不匹配可能是由于中文分词差异（同义词/近义词未覆盖）")


if __name__ == "__main__":
    main()
