#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多AI工具生态系统
Multi-AI Toolkit Ecosystem

功能:
- AI工具市场管理
- 插件系统
- 工具发现与推荐
- 生态统计分析

用法:
    python ai_toolkit_ecosystem.py list
    python ai_toolkit_ecosystem.py install <tool_id>
    python ai_toolkit_ecosystem.py stats
    python ai_toolkit_ecosystem.py recommend <task>
"""

import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base import Skill, handle_errors

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

AI_ROOT = Path(os.environ.get("AI_ROOT", "/python"))
ECOSYSTEM_DIR = AI_ROOT / "MCP_Core" / "ecosystem"
PLUGINS_DIR = ECOSYSTEM_DIR / "plugins"
STATS_FILE = ECOSYSTEM_DIR / "stats.json"


class AIToolkitEcosystem(Skill):
    """AI工具生态系统"""

    # 技能元数据
    name = "ai_toolkit_ecosystem"
    description = "多AI工具生态系统 - 工具市场管理、插件系统、工具发现与推荐、生态统计分析"
    version = "1.0.0"
    author = "MCP Core"
    config_prefix = "ai_toolkit_ecosystem"

    # tool_id → Python import name 映射（避免 pip 名 / import 名不一致导致的误判）
    TOOL_IMPORT_MAP = {
        "openai": "openai",
        "anthropic": "anthropic",
        "google": "google.ai.generativelanguage",  # google-generativeai 主模块
        "ollama": "ollama",
        "llamacpp": "llama_cpp",  # llama-cpp-python → llama_cpp
        "transformers": "transformers",
        "langchain": "langchain",
        "llamaindex": "llama_index",  # llama-index → llama_index
        "autogen": "autogen",  # pyautogen → autogen
        "huggingface": "huggingface_hub",
        "cohere": "cohere",
        "mistral": "mistralai",
        "azure": "openai",
    }

    # 工具市场
    TOOL_MARKET = {
        "core": {
            "openai": {
                "name": "OpenAI",
                "description": "GPT-4, GPT-3.5 等模型",
                "category": "core",
                "install_cmd": "pip install openai",
                "popularity": 95,
                "rating": 4.8,
            },
            "anthropic": {
                "name": "Anthropic Claude",
                "description": "Claude 3 系列模型",
                "category": "core",
                "install_cmd": "pip install anthropic",
                "popularity": 90,
                "rating": 4.9,
            },
            "google": {
                "name": "Google Gemini",
                "description": "Google Gemini Pro 模型",
                "category": "core",
                "install_cmd": "pip install google-generativeai",
                "popularity": 85,
                "rating": 4.6,
            },
        },
        "local": {
            "ollama": {
                "name": "Ollama",
                "description": "本地运行开源模型",
                "category": "local",
                "install_cmd": "pip install ollama",
                "popularity": 88,
                "rating": 4.7,
            },
            "llamacpp": {
                "name": "llama.cpp",
                "description": "高性能本地推理",
                "category": "local",
                "install_cmd": "pip install llama-cpp-python",
                "popularity": 82,
                "rating": 4.5,
            },
            "transformers": {
                "name": "Hugging Face Transformers",
                "description": "丰富的预训练模型",
                "category": "local",
                "install_cmd": "pip install transformers",
                "popularity": 92,
                "rating": 4.8,
            },
        },
        "specialized": {
            "langchain": {
                "name": "LangChain",
                "description": "LLM应用开发框架",
                "category": "framework",
                "install_cmd": "pip install langchain",
                "popularity": 93,
                "rating": 4.7,
            },
            "llamaindex": {
                "name": "LlamaIndex",
                "description": "数据索引和检索",
                "category": "framework",
                "install_cmd": "pip install llama-index",
                "popularity": 87,
                "rating": 4.6,
            },
            "autogen": {
                "name": "AutoGen",
                "description": "多智能体对话框架",
                "category": "framework",
                "install_cmd": "pip install pyautogen",
                "popularity": 80,
                "rating": 4.5,
            },
        },
    }

    # 任务-工具映射
    TASK_RECOMMENDATIONS = {
        "文本生成": ["openai", "anthropic", "google"],
        "代码辅助": ["openai", "anthropic", "ollama"],
        "数据分析": ["anthropic", "openai", "llamaindex"],
        "文档处理": ["llamaindex", "langchain", "anthropic"],
        "本地部署": ["ollama", "llamacpp", "transformers"],
        "多智能体": ["autogen", "langchain", "openai"],
        "知识库": ["llamaindex", "langchain", "anthropic"],
        "图像理解": ["openai", "google", "anthropic"],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.installed_tools: List[str] = []
        self.usage_stats: Dict[str, int] = defaultdict(int)
        ECOSYSTEM_DIR.mkdir(parents=True, exist_ok=True)
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_stats()

    def _load_stats(self) -> None:
        """加载统计数据"""
        if STATS_FILE.exists():
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.usage_stats = defaultdict(int, data.get("usage", {}))

    def _save_stats(self) -> None:
        """保存统计数据"""
        data = {
            "last_updated": datetime.now().isoformat(),
            "usage": dict(self.usage_stats),
            "installed": self._get_installed_tools(),
        }
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_installed_tools(self) -> List[str]:
        """获取已安装的工具"""
        installed = []
        for category in self.TOOL_MARKET.values():
            for tool_id, tool in category.items():
                if self._check_package_installed(tool_id):
                    installed.append(tool_id)
        return installed

    def _check_package_installed(self, tool_id: str) -> bool:
        """检查包是否安装（使用 tool_id→import_name 映射）"""
        import_name = self.TOOL_IMPORT_MAP.get(tool_id, tool_id.replace("-", "_"))
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {import_name}"], capture_output=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def list_market(self, category: str = None) -> List[Dict[str, Any]]:
        """列出工具市场"""
        self.logger.info("开始列出工具市场")

        tools = []

        for cat_name, cat_tools in self.TOOL_MARKET.items():
            if category and cat_name != category:
                continue

            self.logger.info(f"列出分类: {cat_name}")

            for tool_id, tool in cat_tools.items():
                installed = self._check_package_installed(tool_id)
                status = "已安装" if installed else "未安装"

                tool_info = {
                    "id": tool_id,
                    "name": tool["name"],
                    "category": tool["category"],
                    "description": tool["description"],
                    "installed": installed,
                    "popularity": tool["popularity"],
                    "rating": tool["rating"],
                }
                tools.append(tool_info)

                self.logger.info(f"工具: {tool_id} - {tool['name']}, 状态: {status}")

        self.logger.info(f"工具市场列出完成，共 {len(tools)} 个工具")
        return tools

    def install_tool(self, tool_id: str) -> bool:
        """安装工具"""
        self.logger.info(f"开始安装工具: {tool_id}")

        # 查找工具
        install_cmd = None
        for category in self.TOOL_MARKET.values():
            if tool_id in category:
                install_cmd = category[tool_id]["install_cmd"]
                break

        if not install_cmd:
            self.logger.error(f"未知工具: {tool_id}")
            return False

        self.logger.info(f"执行安装命令: {install_cmd}")

        try:
            result = subprocess.run(
                install_cmd.split(), capture_output=True, text=True, timeout=300
            )

            if result.returncode == 0:
                self.logger.info(f"工具 {tool_id} 安装成功")
                self.usage_stats[f"install_{tool_id}"] += 1
                self._save_stats()
                return True
            else:
                self.logger.error(f"工具 {tool_id} 安装失败: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"工具 {tool_id} 安装错误: {e}")
            return False

    def recommend_tools(self, task_description: str) -> List[Dict]:
        """根据任务推荐工具"""
        print("\n" + "=" * 60)
        print("工具推荐")
        print("=" * 60 + "\n")

        print(f"任务: {task_description}\n")

        # 关键词匹配
        task_lower = task_description.lower()
        recommendations = []

        for task_type, tools in self.TASK_RECOMMENDATIONS.items():
            if any(keyword in task_lower for keyword in task_type.lower().split()):
                print(f"【{task_type}】推荐工具:")
                for i, tool_id in enumerate(tools[:3], 1):
                    # 查找工具信息
                    tool_info = None
                    for category in self.TOOL_MARKET.values():
                        if tool_id in category:
                            tool_info = category[tool_id]
                            break

                    if tool_info:
                        installed = self._check_package_installed(tool_id)
                        status = "✅ 已安装" if installed else "⬜ 未安装"
                        print(f"  {i}. {tool_info['name']} ({tool_id})")
                        print(f"     {tool_info['description']}")
                        print(f"     {status}")
                        recommendations.append(
                            {
                                "rank": i,
                                "tool_id": tool_id,
                                "name": tool_info["name"],
                                "description": tool_info["description"],
                                "installed": installed,
                            }
                        )
                print()
                break
        else:
            # 默认推荐
            print("通用推荐:")
            print("  1. OpenAI - 强大的通用AI能力")
            print("  2. Anthropic Claude - 优秀的推理和分析")
            print("  3. LangChain - 应用开发框架")
            recommendations = [
                {
                    "rank": 1,
                    "tool_id": "openai",
                    "name": "OpenAI",
                    "installed": self._check_package_installed("openai"),
                },
                {
                    "rank": 2,
                    "tool_id": "anthropic",
                    "name": "Anthropic Claude",
                    "installed": self._check_package_installed("anthropic"),
                },
                {
                    "rank": 3,
                    "tool_id": "langchain",
                    "name": "LangChain",
                    "installed": self._check_package_installed("langchain"),
                },
            ]

        return recommendations

    def get_stats(self) -> Dict:
        """获取生态统计"""
        print("\n" + "=" * 60)
        print("AI工具生态统计")
        print("=" * 60 + "\n")

        # 已安装工具统计
        installed = self._get_installed_tools()
        total_tools = sum(len(cat) for cat in self.TOOL_MARKET.values())

        print(f"工具总数: {total_tools}")
        print(f"已安装: {len(installed)}")
        print(f"安装率: {len(installed) / total_tools * 100:.1f}%\n")

        # 分类统计
        print("分类统计:")
        for cat_name, cat_tools in self.TOOL_MARKET.items():
            cat_installed = [t for t in cat_tools.keys() if t in installed]
            print(f"  {cat_name:12}: {len(cat_installed)}/{len(cat_tools)} 已安装")

        # 使用统计
        if self.usage_stats:
            print("\n使用统计:")
            for key, count in sorted(self.usage_stats.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]:
                print(f"  {key}: {count} 次")

        stats = {
            "total_tools": total_tools,
            "installed_count": len(installed),
            "install_rate": len(installed) / total_tools,
            "installed_tools": installed,
            "usage_stats": dict(self.usage_stats),
            "last_updated": datetime.now().isoformat(),
        }

        return stats

    def search_tools(self, query: str) -> List[Dict]:
        """搜索工具"""
        print(f"\n搜索: {query}\n")

        results = []
        query_lower = query.lower()

        for category in self.TOOL_MARKET.values():
            for tool_id, tool in category.items():
                if (
                    query_lower in tool_id.lower()
                    or query_lower in tool["name"].lower()
                    or query_lower in tool["description"].lower()
                ):
                    results.append(
                        {
                            "id": tool_id,
                            "name": tool["name"],
                            "description": tool["description"],
                            "category": tool["category"],
                        }
                    )

        if results:
            print(f"找到 {len(results)} 个工具:")
            for tool in results:
                print(f"  - {tool['name']} ({tool['id']})")
                print(f"    {tool['description']}")
        else:
            print("未找到匹配的工具")

        return results

    def create_plugin_template(self, plugin_name: str) -> str:
        """创建插件模板"""
        plugin_dir = PLUGINS_DIR / plugin_name
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # 创建插件主文件
        plugin_code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{plugin_name} 插件
"""

from typing import Dict, List, Any


class {plugin_name.title()}Plugin:
    """{plugin_name} 插件类"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {{}}
        self.name = "{plugin_name}"
    
    def initialize(self) -> bool:
        """初始化插件"""
        print(f"初始化 {{self.name}} 插件")
        return True
    
    @handle_errors

    
    def execute(self, input_data: Any) -> Any:
        """执行插件功能"""
        return {{"result": "success", "data": input_data}}
    
    def get_info(self) -> Dict:
        """获取插件信息"""
        return {{
            "name": self.name,
            "version": "1.0.0",
            "author": "",
            "description": ""
        }}


# 插件入口点
def create_plugin(config: Dict = None):
    """创建插件实例"""
    return {plugin_name.title()}Plugin(config)
'''

        plugin_file = plugin_dir / "__init__.py"
        with open(plugin_file, "w", encoding="utf-8") as f:
            f.write(plugin_code)

        # 创建插件配置
        config_data = {
            "name": plugin_name,
            "version": "1.0.0",
            "entry_point": f"{plugin_name}.__init__",
            "dependencies": [],
            "enabled": True,
        }

        config_file = plugin_dir / "plugin.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"插件模板已创建: {plugin_dir}")
        return str(plugin_dir)

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义"""
        return {
            "action": {
                "type": "string",
                "required": True,
                "enum": ["list", "install", "stats", "recommend", "search", "create_plugin"],
                "description": "操作类型",
            },
            "category": {"type": "string", "required": False, "description": "工具分类"},
            "tool_id": {"type": "string", "required": False, "description": "工具ID"},
            "task_description": {"type": "string", "required": False, "description": "任务描述"},
            "query": {"type": "string", "required": False, "description": "搜索查询"},
            "plugin_name": {"type": "string", "required": False, "description": "插件名称"},
        }

    @handle_errors
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        action = params.get("action")

        if action == "list":
            category = params.get("category")
            tools = self.list_market(category)
            return {"success": True, "result": tools}
        elif action == "install":
            tool_id = params.get("tool_id")
            if not tool_id:
                return {"success": False, "error": "缺少工具ID"}
            success = self.install_tool(tool_id)
            return {"success": success, "result": {"tool_id": tool_id, "installed": success}}
        elif action == "stats":
            stats = self.get_stats()
            return {"success": True, "result": stats}
        elif action == "recommend":
            task_description = params.get("task_description", "")
            recommendations = self.recommend_tools(task_description)
            return {"success": True, "result": recommendations}
        elif action == "search":
            query = params.get("query", "")
            results = self.search_tools(query)
            return {"success": True, "result": results}
        elif action == "create_plugin":
            plugin_name = params.get("plugin_name")
            if not plugin_name:
                return {"success": False, "error": "缺少插件名称"}
            plugin_path = self.create_plugin_template(plugin_name)
            return {"success": True, "result": {"plugin_path": plugin_path}}
        else:
            return {"success": False, "error": "无效的操作"}


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python ai_toolkit_ecosystem.py <命令>")
        print("命令:")
        print("  list [category]     列出工具市场")
        print("  install <tool_id>   安装工具")
        print("  stats               显示统计")
        print("  recommend <task>    推荐工具")
        print("  search <query>      搜索工具")
        print("  create_plugin <name> 创建插件模板")
        return

    ecosystem = AIToolkitEcosystem()
    command = sys.argv[1]

    if command == "list":
        category = sys.argv[2] if len(sys.argv) >= 3 else None
        ecosystem.list_market(category)

    elif command == "install" and len(sys.argv) >= 3:
        tool_id = sys.argv[2]
        ecosystem.install_tool(tool_id)

    elif command == "stats":
        ecosystem.get_stats()

    elif command == "recommend" and len(sys.argv) >= 3:
        task = " ".join(sys.argv[2:])
        ecosystem.recommend_tools(task)

    elif command == "search" and len(sys.argv) >= 3:
        query = " ".join(sys.argv[2:])
        ecosystem.search_tools(query)

    elif command == "create_plugin" and len(sys.argv) >= 3:
        plugin_name = sys.argv[2]
        ecosystem.create_plugin_template(plugin_name)

    else:
        print(f"未知命令或参数不足: {command}")


if __name__ == "__main__":
    main()
