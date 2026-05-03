#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多AI工具兼容管理器
Multi-AI Toolkit Compatibility Manager

功能:
- 多AI工具兼容性检测
- 工具版本管理
- 配置适配
- 冲突解决
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

AI_ROOT = Path("/python")
CONFIG_DIR = AI_ROOT / "Config"


class AIToolkitManager:
    """AI工具包管理器"""

    # pip package name → Python import name 映射
    PACKAGE_IMPORT_MAP = {
        "openai": "openai",
        "anthropic": "anthropic",
        "google-generativeai": "google.ai.generativelanguage",
        "ollama": "ollama",
        "huggingface_hub": "huggingface_hub",
        "cohere": "cohere",
        "mistralai": "mistralai",
    }

    SUPPORTED_TOOLS = {
        "openai": {
            "name": "OpenAI",
            "package": "openai",
            "min_version": "1.0.0",
            "env": "OPENAI_API_KEY",
            "features": ["chat", "completion", "embedding"],
        },
        "anthropic": {
            "name": "Anthropic Claude",
            "package": "anthropic",
            "min_version": "0.18.0",
            "env": "ANTHROPIC_API_KEY",
            "features": ["chat", "vision"],
        },
        "google": {
            "name": "Google Gemini",
            "package": "google-generativeai",
            "min_version": "0.3.0",
            "env": "GOOGLE_API_KEY",
            "features": ["chat", "vision"],
        },
        "ollama": {
            "name": "Ollama",
            "package": "ollama",
            "min_version": "0.1.0",
            "env": "",
            "features": ["local", "offline"],
        },
        "azure": {
            "name": "Azure OpenAI",
            "package": "openai",
            "min_version": "1.0.0",
            "env": "AZURE_OPENAI_API_KEY",
            "features": ["enterprise"],
        },
        "huggingface": {
            "name": "Hugging Face",
            "package": "huggingface_hub",
            "min_version": "0.19.0",
            "env": "HUGGINGFACE_API_KEY",
            "features": ["models", "local"],
        },
        "cohere": {
            "name": "Cohere",
            "package": "cohere",
            "min_version": "4.0.0",
            "env": "COHERE_API_KEY",
            "features": ["chat", "embedding"],
        },
        "mistral": {
            "name": "Mistral AI",
            "package": "mistralai",
            "min_version": "0.0.8",
            "env": "MISTRAL_API_KEY",
            "features": ["chat", "function_calling"],
        },
    }

    def __init__(self):
        self.results = {
            "checked": [],
            "installed": [],
            "missing": [],
            "configured": [],
            "errors": [],
        }
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def check_compatibility(self) -> Dict:
        """检查所有AI工具的兼容性"""
        print("\n" + "=" * 60)
        print("多AI工具兼容性检测")
        print("=" * 60 + "\n")

        for tool_id, tool in self.SUPPORTED_TOOLS.items():
            print(f"\n检查: {tool['name']}")
            installed, version = self._check_package(tool["package"])

            if installed:
                print(f"  状态: 已安装 (v{version})")
                self.results["installed"].append(
                    {"id": tool_id, "name": tool["name"], "version": version}
                )
            else:
                print(f"  状态: 未安装")
                self.results["missing"].append({"id": tool_id, "name": tool["name"]})

            # 检查API密钥
            if tool["env"]:
                api_key = os.getenv(tool["env"], "")
                if api_key:
                    print(f"  API密钥: 已配置")
                else:
                    print(f"  API密钥: 未配置 (环境变量: {tool['env']})")

            self.results["checked"].append(tool_id)

        print("\n" + "=" * 60)
        print(
            f"检测完成: {len(self.results['installed'])} 个已安装, {len(self.results['missing'])} 个未安装"
        )
        print("=" * 60 + "\n")

        return self.results

    def _check_package(self, package_name: str) -> tuple:
        """检查Python包是否安装（使用 PACKAGE_IMPORT_MAP 获取正确的 import 名）"""
        import_name = self.PACKAGE_IMPORT_MAP.get(package_name, package_name.replace("-", "_"))
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {import_name}; print({import_name}.__version__)"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
        except:
            pass

        # 尝试用pip检查
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        return True, line.split(":")[1].strip()
        except:
            pass

        return False, ""

    def list_tools(self) -> List[Dict]:
        """列出所有支持的AI工具"""
        print("\n" + "=" * 60)
        print("支持的AI工具列表")
        print("=" * 60 + "\n")

        tools = []
        for tool_id, tool in self.SUPPORTED_TOOLS.items():
            tool_info = {
                "id": tool_id,
                "name": tool["name"],
                "package": tool["package"],
                "features": tool["features"],
                "env_var": tool["env"],
            }
            tools.append(tool_info)
            print(f"{tool_id:15} - {tool['name']}")
            print(f"  包: {tool['package']}")
            print(f"  功能: {', '.join(tool['features'])}")
            if tool["env"]:
                print(f"  环境变量: {tool['env']}")
            print()

        return tools

    def configure_tool(self, tool_id: str, config: Dict) -> bool:
        """配置指定的AI工具"""
        if tool_id not in self.SUPPORTED_TOOLS:
            print(f"错误: 未知工具 {tool_id}")
            return False

        tool = self.SUPPORTED_TOOLS[tool_id]
        print(f"\n配置: {tool['name']}")

        # 保存配置
        config_file = CONFIG_DIR / f"{tool_id}_config.json"
        config_data = {
            "tool_id": tool_id,
            "tool_name": tool["name"],
            "configured_at": datetime.now().isoformat(),
            "config": config,
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        print(f"配置已保存: {config_file}")
        self.results["configured"].append(tool_id)
        return True

    def get_unified_interface(self) -> Dict:
        """获取统一接口配置"""
        return {
            "version": "1.0.0",
            "description": "多AI工具统一接口",
            "supported_tools": list(self.SUPPORTED_TOOLS.keys()),
            "default_tool": "openai",
            "interface": {
                "chat": {
                    "method": "chat",
                    "params": ["model", "messages", "temperature", "max_tokens"],
                },
                "completion": {
                    "method": "complete",
                    "params": ["model", "prompt", "temperature", "max_tokens"],
                },
                "embedding": {"method": "embed", "params": ["model", "text"]},
            },
        }

    def generate_adapter_code(self, output_dir: str = None) -> str:
        """生成适配器代码"""
        if output_dir is None:
            output_dir = AI_ROOT / "MCP_Core" / "adapters"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        adapter_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多AI工具统一适配器
Unified AI Toolkit Adapter

自动适配不同的AI工具，提供统一接口
"""

import os
import json
from typing import Dict, List, Optional, Generator
from pathlib import Path


class UnifiedAIAdapter:
    """统一AI适配器"""
    
    def __init__(self, tool_id: str = None, config: Dict = None):
        self.tool_id = tool_id or os.getenv("DEFAULT_AI_TOOL", "openai")
        self.config = config or {}
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化客户端"""
        if self.tool_id == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.tool_id == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif self.tool_id == "ollama":
            import ollama
            self.client = ollama
        # 其他工具...
    
    def chat(self, messages: List[Dict], model: str = None, **kwargs) -> str:
        """统一聊天接口"""
        if self.tool_id == "openai":
            response = self.client.chat.completions.create(
                model=model or "gpt-4",
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        elif self.tool_id == "anthropic":
            response = self.client.messages.create(
                model=model or "claude-3-sonnet",
                messages=messages,
                **kwargs
            )
            return response.content[0].text
        elif self.tool_id == "ollama":
            response = self.client.chat(model=model or "llama3", messages=messages)
            return response['message']['content']
        else:
            raise ValueError(f"不支持的工具: {self.tool_id}")
    
    def complete(self, prompt: str, model: str = None, **kwargs) -> str:
        """统一补全接口"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, model, **kwargs)
    
    def embed(self, text: str, model: str = None) -> List[float]:
        """统一嵌入接口"""
        if self.tool_id == "openai":
            response = self.client.embeddings.create(
                model=model or "text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        else:
            raise ValueError(f"{self.tool_id} 不支持嵌入功能")


# 便捷函数
def chat(messages: List[Dict], tool: str = None, **kwargs) -> str:
    """快速聊天"""
    adapter = UnifiedAIAdapter(tool_id=tool)
    return adapter.chat(messages, **kwargs)


def complete(prompt: str, tool: str = None, **kwargs) -> str:
    """快速补全"""
    adapter = UnifiedAIAdapter(tool_id=tool)
    return adapter.complete(prompt, **kwargs)
'''

        adapter_file = output_path / "unified_adapter.py"
        with open(adapter_file, "w", encoding="utf-8") as f:
            f.write(adapter_code)

        print(f"适配器代码已生成: {adapter_file}")
        return str(adapter_file)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python ai_toolkit_manager.py <命令>")
        print("命令:")
        print("  check_compat          检查兼容性")
        print("  list_tools            列出工具")
        print("  configure <tool_id>   配置工具")
        print("  generate_adapter      生成适配器代码")
        return

    manager = AIToolkitManager()
    command = sys.argv[1]

    if command == "check_compat":
        manager.check_compatibility()
    elif command == "list_tools":
        manager.list_tools()
    elif command == "configure" and len(sys.argv) >= 3:
        tool_id = sys.argv[2]
        config = json.loads(sys.argv[3]) if len(sys.argv) >= 4 else {}
        manager.configure_tool(tool_id, config)
    elif command == "generate_adapter":
        manager.generate_adapter_code()
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
