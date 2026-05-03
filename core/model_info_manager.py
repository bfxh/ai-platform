#!/usr/bin/env python3
"""
模型信息记录程序
记录不同大模型的上下文长度、能力、性能等信息
"""

import json
import os
from datetime import datetime
from pathlib import Path

import os

_BASE = Path(os.environ.get("AI_BASE_DIR", Path(__file__).resolve().parent.parent))
MODEL_INFO_FILE = str(_BASE / "storage/models/model_info.json")

# 预设模型信息
DEFAULT_MODELS = {
    "gpt-4o": {
        "context_length": 128000,
        "description": "OpenAI GPT-4o，最强通用模型，支持文本、图像、语音",
        "strengths": ["通用推理", "多模态", "代码生成", "长上下文"],
        "weaknesses": ["价格高", "API依赖"],
        "provider": "OpenAI",
        "version": "latest",
        "updated_at": datetime.now().isoformat(),
    },
    "gpt-4-turbo": {
        "context_length": 128000,
        "description": "OpenAI GPT-4 Turbo，平衡版",
        "strengths": ["通用推理", "长上下文"],
        "weaknesses": ["API依赖"],
        "provider": "OpenAI",
        "version": "latest",
        "updated_at": datetime.now().isoformat(),
    },
    "gpt-3.5-turbo": {
        "context_length": 16384,
        "description": "OpenAI GPT-3.5 Turbo，轻量版",
        "strengths": ["速度快", "价格低"],
        "weaknesses": ["能力有限", "上下文短"],
        "provider": "OpenAI",
        "version": "latest",
        "updated_at": datetime.now().isoformat(),
    },
    "claude-3-opus": {
        "context_length": 200000,
        "description": "Anthropic Claude 3 Opus，最强 Claude 模型",
        "strengths": ["长上下文", "安全可靠"],
        "weaknesses": ["API依赖"],
        "provider": "Anthropic",
        "version": "latest",
        "updated_at": datetime.now().isoformat(),
    },
    "claude-3-sonnet": {
        "context_length": 200000,
        "description": "Anthropic Claude 3 Sonnet，平衡版",
        "strengths": ["长上下文", "速度快"],
        "weaknesses": ["API依赖"],
        "provider": "Anthropic",
        "version": "latest",
        "updated_at": datetime.now().isoformat(),
    },
    "gemini-1.5-pro": {
        "context_length": 1000000,
        "description": "Google Gemini 1.5 Pro，超长上下文",
        "strengths": ["超长上下文", "多模态"],
        "weaknesses": ["API依赖"],
        "provider": "Google",
        "version": "latest",
        "updated_at": datetime.now().isoformat(),
    },
    "gemini-1.5-flash": {
        "context_length": 1000000,
        "description": "Google Gemini 1.5 Flash，轻量版",
        "strengths": ["超长上下文", "速度快"],
        "weaknesses": ["能力有限"],
        "provider": "Google",
        "version": "latest",
        "updated_at": datetime.now().isoformat(),
    },
    "llama-3.1-70b": {
        "context_length": 128000,
        "description": "Meta Llama 3.1 70B，开源最强",
        "strengths": ["开源", "能力强"],
        "weaknesses": ["需要本地部署"],
        "provider": "Meta",
        "version": "3.1",
        "updated_at": datetime.now().isoformat(),
    },
    "llama-3.1-8b": {
        "context_length": 128000,
        "description": "Meta Llama 3.1 8B，轻量开源",
        "strengths": ["开源", "速度快"],
        "weaknesses": ["能力有限"],
        "provider": "Meta",
        "version": "3.1",
        "updated_at": datetime.now().isoformat(),
    },
    "mistral-large-2": {
        "context_length": 32000,
        "description": "Mistral AI Large 2，欧洲顶级模型",
        "strengths": ["数学能力", "代码生成"],
        "weaknesses": ["API依赖"],
        "provider": "Mistral AI",
        "version": "2.0",
        "updated_at": datetime.now().isoformat(),
    },
    "qwen2.5-72b": {
        "context_length": 128000,
        "description": "阿里通义千问 2.5 72B，中文强",
        "strengths": ["中文能力", "多模态"],
        "weaknesses": ["API依赖"],
        "provider": "阿里",
        "version": "2.5",
        "updated_at": datetime.now().isoformat(),
    },
    "deepseek-coder-v2": {
        "context_length": 160000,
        "description": "深度求索 DeepSeek Coder V2，代码专用",
        "strengths": ["代码生成", "长上下文"],
        "weaknesses": ["通用性弱"],
        "provider": "深度求索",
        "version": "2.0",
        "updated_at": datetime.now().isoformat(),
    },
}


class ModelInfoManager:
    def __init__(self, file_path=MODEL_INFO_FILE):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.models = self.load()

    def load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_MODELS

    def save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.models, f, ensure_ascii=False, indent=2)

    def get_model(self, model_name):
        return self.models.get(model_name, None)

    def add_model(self, model_name, info):
        info["updated_at"] = datetime.now().isoformat()
        self.models[model_name] = info
        self.save()

    def update_model(self, model_name, info):
        if model_name in self.models:
            self.models[model_name].update(info)
            self.models[model_name]["updated_at"] = datetime.now().isoformat()
            self.save()

    def list_models(self):
        return list(self.models.keys())

    def get_model_summary(self, model_name):
        model = self.get_model(model_name)
        if not model:
            return f"模型 {model_name} 未找到"
        return (
            f"{model_name} (上下文: {model['context_length']} 令牌)\n"
            f"描述: {model['description']}\n"
            f"优势: {', '.join(model['strengths'])}\n"
            f"劣势: {', '.join(model['weaknesses'])}"
        )


def main():
    manager = ModelInfoManager()
    print("模型信息管理程序")
    print("可用模型:", manager.list_models())

    # 示例：获取模型信息
    for model in ["gpt-4o", "llama-3.1-70b", "qwen2.5-72b"]:
        print(f"\n=== {model} ===")
        print(manager.get_model_summary(model))


if __name__ == "__main__":
    main()
