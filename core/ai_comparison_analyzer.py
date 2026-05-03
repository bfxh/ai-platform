#!/usr/bin/env python3
"""
AI 工具对比分析器
每次提供建议时，自动对比所有相关 AI 框架、插件、模型
"""

import json
import os
from datetime import datetime
from pathlib import Path

import os

_BASE = Path(os.environ.get("AI_BASE_DIR", Path(__file__).resolve().parent.parent))
AI_TOOLS_FILE = str(_BASE / "storage/models/ai_tools_comparison.json")
MODEL_INFO_FILE = str(_BASE / "storage/models/model_info.json")


class AIComparisonAnalyzer:
    def __init__(self):
        self.tools = self.load_tools()
        self.models = self.tools.get("models", {})
        self.frameworks = self.tools.get("ai_frameworks", {})
        self.mcp_servers = self.tools.get("mcp_servers", {})
        self.local_deploy = self.tools.get("local_deployment", {})

    def load_tools(self):
        if os.path.exists(AI_TOOLS_FILE):
            try:
                with open(AI_TOOLS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"models": {}, "ai_frameworks": {}, "mcp_servers": {}, "local_deployment": {}}

    def get_model_info(self, model_name):
        return self.models.get(model_name, None)

    def compare_models(self, model_names):
        """对比多个模型的性能"""
        comparison = []
        for name in model_names:
            model = self.models.get(name)
            if model:
                comparison.append(
                    {
                        "name": name,
                        "provider": model.get("provider", "Unknown"),
                        "context_length": model.get("context_length", 0),
                        "pricing": model.get("pricing_per_1m_tokens", {}),
                        "strengths": model.get("strengths", []),
                        "supports_functions": model.get("supports_functions", False),
                        "supports_vision": model.get("supports_vision", False),
                        "supports_reasoning": model.get("supports_reasoning", False),
                        "local_only": model.get("local_only", False),
                    }
                )
        return comparison

    def rank_models_by_context(self, purpose=None):
        """按上下文长度排名模型"""
        ranked = []
        for name, model in self.models.items():
            if purpose:
                if purpose in model.get("strengths", []):
                    ranked.append(
                        {
                            "name": name,
                            "provider": model.get("provider"),
                            "context_length": model.get("context_length", 0),
                            "description": model.get("description", ""),
                            "pricing": model.get("pricing_per_1m_tokens", {}),
                        }
                    )
            else:
                ranked.append(
                    {
                        "name": name,
                        "provider": model.get("provider"),
                        "context_length": model.get("context_length", 0),
                        "description": model.get("description", ""),
                        "pricing": model.get("pricing_per_1m_tokens", {}),
                    }
                )
        ranked.sort(key=lambda x: x["context_length"], reverse=True)
        return ranked

    def get_best_model(self, requirements):
        """根据需求推荐最佳模型"""
        requirements = {k.lower(): v for k, v in requirements.items()}
        candidates = []

        for name, model in self.models.items():
            score = 0
            reasons = []

            if requirements.get("context_length"):
                if model.get("context_length", 0) >= requirements["context_length"]:
                    score += 10
                    reasons.append(f"上下文{model['context_length']}K")
                else:
                    continue

            if requirements.get("vision") and model.get("supports_vision"):
                score += 5
                reasons.append("支持视觉")

            if requirements.get("functions") and model.get("supports_functions"):
                score += 5
                reasons.append("支持函数调用")

            if requirements.get("local") and model.get("local_only"):
                score += 10
                reasons.append("可本地部署")

            if requirements.get("reasoning") and model.get("supports_reasoning"):
                score += 5
                reasons.append("推理模式")

            if requirements.get("free") and model.get("pricing_per_1m_tokens", {}).get("input", 999) == 0:
                score += 8
                reasons.append("免费使用")

            if requirements.get("chinese") and model.get("provider") in ["阿里", "零一万物", "深度求索"]:
                score += 5
                reasons.append("中文优化")

            if requirements.get("code") and "代码" in " ".join(model.get("strengths", [])):
                score += 5
                reasons.append("代码能力强")

            if score > 0:
                candidates.append(
                    {
                        "name": name,
                        "provider": model.get("provider"),
                        "description": model.get("description"),
                        "score": score,
                        "reasons": reasons,
                        "pricing": model.get("pricing_per_1m_tokens", {}),
                        "context_length": model.get("context_length", 0),
                    }
                )

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    def compare_frameworks(self, framework_names=None):
        """对比 AI 框架"""
        if framework_names:
            return {name: self.frameworks.get(name) for name in framework_names if name in self.frameworks}
        return self.frameworks

    def rank_frameworks(self, criteria="features"):
        """排名 AI 框架"""
        ranked = []
        for name, fw in self.frameworks.items():
            score = 0
            if criteria == "features":
                if fw.get("supports_mcp"):
                    score += 3
                if fw.get("supports_plugins"):
                    score += 2
                if fw.get("supports_local_models"):
                    score += 3
                if fw.get("supports_cloud_models"):
                    score += 1
                if fw.get("is_open_source"):
                    score += 3
            elif criteria == "ease_of_use":
                if "CLI" not in fw.get("type", ""):
                    score += 2
                if fw.get("setup_difficulty", "困难") in ["简单", "非常简单"]:
                    score += 3
            elif criteria == "privacy":
                if fw.get("supports_local_models"):
                    score += 5
                if fw.get("is_open_source"):
                    score += 3

            ranked.append(
                {
                    "name": name,
                    "display_name": fw.get("name", name),
                    "type": fw.get("type", "unknown"),
                    "score": score,
                    "strengths": fw.get("strengths", []),
                    "weaknesses": fw.get("weaknesses", []),
                    "is_open_source": fw.get("is_open_source", False),
                    "supports_mcp": fw.get("supports_mcp", False),
                    "license": fw.get("license", "Proprietary"),
                }
            )

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked

    def get_framework_comparison_table(self):
        """生成框架对比表格"""
        headers = ["框架", "类型", "MCP", "插件", "本地模型", "云模型", "开源", "许可证"]
        rows = []
        for name, fw in self.frameworks.items():
            rows.append(
                [
                    fw.get("name", name),
                    fw.get("type", "-"),
                    "✅" if fw.get("supports_mcp") else "❌",
                    "✅" if fw.get("supports_plugins") else "❌",
                    "✅" if fw.get("supports_local_models") else "❌",
                    "✅" if fw.get("supports_cloud_models") else "❌",
                    "✅" if fw.get("is_open_source") else "❌",
                    fw.get("license", "Proprietary"),
                ]
            )
        return {"headers": headers, "rows": rows}

    def get_model_comparison_table(self, purpose=None):
        """生成模型对比表格"""
        headers = ["模型", "提供商", "上下文", "输入价格", "输出价格", "函数", "视觉", "推理", "本地"]
        rows = []
        models = (
            self.get_best_model({"context_length": 0})
            if purpose
            else sorted(self.models.items(), key=lambda x: x[1].get("context_length", 0), reverse=True)
        )
        for name, model in models[:15]:
            rows.append(
                [
                    name,
                    model.get("provider", "-"),
                    f"{model.get('context_length', 0)}K",
                    f"${model.get('pricing_per_1m_tokens', {}).get('input', '-')}",
                    f"${model.get('pricing_per_1m_tokens', {}).get('output', '-')}",
                    "✅" if model.get("supports_functions") else "❌",
                    "✅" if model.get("supports_vision") else "❌",
                    "✅" if model.get("supports_reasoning") else "❌",
                    "✅" if model.get("local_only") else "❌",
                ]
            )
        return {"headers": headers, "rows": rows}

    def generate_full_comparison_report(self, task_description):
        """生成完整的对比报告"""
        report = {
            "task": task_description,
            "generated_at": datetime.now().isoformat(),
            "model_comparison": self.get_model_comparison_table(),
            "framework_comparison": self.get_framework_comparison_table(),
        }

        # 任务特定推荐
        task_lower = task_description.lower()
        requirements = {}
        if "代码" in task_description or "code" in task_lower:
            requirements["code"] = True
        if "视觉" in task_description or "image" in task_lower or "图" in task_description:
            requirements["vision"] = True
        if "函数" in task_description or "function" in task_lower:
            requirements["functions"] = True
        if "推理" in task_description or "reasoning" in task_lower:
            requirements["reasoning"] = True
        if "本地" in task_description or "local" in task_lower:
            requirements["local"] = True
        if "免费" in task_description or "free" in task_lower:
            requirements["free"] = True
        if "中文" in task_description:
            requirements["chinese"] = True
        if "长上下文" in task_description or "long context" in task_lower:
            requirements["context_length"] = 128000

        if requirements:
            best_models = self.get_best_model(requirements)
            report["recommended_models"] = best_models[:5]

        return report

    def print_comparison_report(self, report):
        """打印对比报告"""
        print("\n" + "=" * 80)
        print(f"📊 AI 工具对比分析报告")
        print(f"   任务: {report['task']}")
        print(f"   生成时间: {report['generated_at']}")
        print("=" * 80)

        # 模型对比表
        print("\n📌 模型对比 (Top 15)")
        headers = report["model_comparison"]["headers"]
        rows = report["model_comparison"]["rows"]
        col_widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(len(headers))]

        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        print(f"  {header_line}")
        print(f"  {'-' * len(header_line)}")
        for row in rows[:10]:
            print(f"  {' | '.join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))}")

        # 框架对比表
        print("\n📌 框架对比")
        headers = report["framework_comparison"]["headers"]
        rows = report["framework_comparison"]["rows"]
        col_widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(len(headers))]

        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        print(f"  {header_line}")
        print(f"  {'-' * len(header_line)}")
        for row in rows:
            print(f"  {' | '.join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))}")

        # 推荐模型
        if "recommended_models" in report:
            print("\n🎯 推荐模型 (按匹配度排序)")
            for i, model in enumerate(report["recommended_models"], 1):
                print(f"  {i}. {model['name']} ({model['provider']})")
                print(f"     {model['description']}")
                print(f"     匹配原因: {', '.join(model['reasons'])}")
                print(
                    f"     上下文: {model['context_length']}K | 价格: ${model['pricing'].get('input', '-')}/${model['pricing'].get('output', '-')}/1M"
                )

        print("\n" + "=" * 80)


def main():
    analyzer = AIComparisonAnalyzer()

    # 示例：对比代码生成任务
    report = analyzer.generate_full_comparison_report("代码生成 + 长上下文 + 本地部署")
    analyzer.print_comparison_report(report)

    # 示例：对比通用任务
    report2 = analyzer.generate_full_comparison_report("通用推理 + 中文 + 免费")
    analyzer.print_comparison_report(report2)


if __name__ == "__main__":
    main()
