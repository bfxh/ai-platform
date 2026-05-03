#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一AI适配层 - 多平台兼容架构
支持: 阶跃AI、OpenAI、Claude、Gemini、Ollama等
"""

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Generator, List, Optional, Union


class AIProvider(Enum):
    """支持的AI提供商"""

    STEPFUN = "stepfun"  # 阶跃AI
    OPENAI = "openai"  # OpenAI
    ANTHROPIC = "anthropic"  # Claude
    GEMINI = "gemini"  # Google Gemini
    OLLAMA = "ollama"  # 本地Ollama
    DEEPSEEK = "deepseek"  # DeepSeek
    QWEN = "qwen"  # 通义千问
    DOUBAO = "doubao"  # 豆包
    XIAOLONGXIA = "xiaolongxia"  # 小龙虾AI (Crawdad/ crayfish AI)
    LOCAL_CLAUDE = "local_claude"  # 本地Claude


@dataclass
class Message:
    """标准消息格式"""

    role: str  # system, user, assistant, tool
    content: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class ChatRequest:
    """标准聊天请求"""

    messages: List[Message]
    model: str = None
    temperature: float = 0.7
    max_tokens: int = 2000
    stream: bool = False
    tools: Optional[List[Dict]] = None
    extra_params: Dict = field(default_factory=dict)


@dataclass
class ChatResponse:
    """标准聊天响应"""

    content: str
    model: str
    usage: Dict = field(default_factory=dict)
    finish_reason: str = "stop"
    raw_response: Dict = field(default_factory=dict)


class BaseAIClient(ABC):
    """AI客户端基类"""

    def __init__(self, api_key: str = None, base_url: str = None, **kwargs):
        self.api_key = api_key or self._get_api_key_from_env()
        self.base_url = base_url or self._get_default_base_url()
        self.default_model = kwargs.get("default_model", self._get_default_model())
        self.messages: List[Message] = []
        self.system_prompt = kwargs.get("system_prompt", "You are a helpful assistant.")

    @abstractmethod
    def _get_api_key_from_env(self) -> str:
        """从环境变量获取API Key"""
        pass

    @abstractmethod
    def _get_default_base_url(self) -> str:
        """获取默认Base URL"""
        pass

    @abstractmethod
    def _get_default_model(self) -> str:
        """获取默认模型"""
        pass

    @abstractmethod
    def chat(self, request: ChatRequest) -> ChatResponse:
        """发送聊天请求"""
        pass

    def _make_http_request(self, url: str, headers: Dict, data: Dict) -> Dict:
        """发送HTTP请求"""
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"API错误 {e.code}: {error_body}")
        except Exception as e:
            raise Exception(f"请求错误: {e}")

    def add_message(self, role: str, content: str, **metadata):
        """添加消息到历史"""
        self.messages.append(Message(role=role, content=content, metadata=metadata))
        # 限制历史长度
        if len(self.messages) > 20:
            self.messages = self.messages[-20:]

    def clear_history(self):
        """清空历史"""
        self.messages = []

    def get_history(self) -> List[Message]:
        """获取历史"""
        return self.messages.copy()


class StepFunClient(BaseAIClient):
    """阶跃AI客户端"""

    def _get_api_key_from_env(self) -> str:
        return os.getenv("STEPFUN_API_KEY", "")

    def _get_default_base_url(self) -> str:
        return "https://api.stepfun.com/v1"

    def _get_default_model(self) -> str:
        return "step-1-8k"

    def chat(self, request: ChatRequest) -> ChatResponse:
        """阶跃AI聊天"""
        model = request.model or self.default_model

        # 构建消息
        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        data = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        response = self._make_http_request(f"{self.base_url}/chat/completions", headers, data)

        choice = response["choices"][0]
        return ChatResponse(
            content=choice["message"]["content"],
            model=response.get("model", model),
            usage=response.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=response,
        )


class OpenAIClient(BaseAIClient):
    """OpenAI客户端"""

    def _get_api_key_from_env(self) -> str:
        return os.getenv("OPENAI_API_KEY", "")

    def _get_default_base_url(self) -> str:
        return os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def _get_default_model(self) -> str:
        return "gpt-4o-mini"

    def chat(self, request: ChatRequest) -> ChatResponse:
        """OpenAI聊天"""
        model = request.model or self.default_model

        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        data = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if request.tools:
            data["tools"] = request.tools

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        response = self._make_http_request(f"{self.base_url}/chat/completions", headers, data)

        choice = response["choices"][0]
        message = choice["message"]
        content = message.get("content", "")
        if not content and "tool_calls" in message:
            content = json.dumps(message["tool_calls"])

        return ChatResponse(
            content=content,
            model=response.get("model", model),
            usage=response.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=response,
        )


class AnthropicClient(BaseAIClient):
    """Claude客户端"""

    def _get_api_key_from_env(self) -> str:
        return os.getenv("ANTHROPIC_API_KEY", "")

    def _get_default_base_url(self) -> str:
        return "https://api.anthropic.com/v1"

    def _get_default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Claude聊天"""
        model = request.model or self.default_model

        # Claude使用不同的消息格式
        messages = []
        system = self.system_prompt

        for msg in request.messages:
            if msg.role == "system":
                system = msg.content
            else:
                messages.append({"role": msg.role, "content": msg.content})

        data = {
            "model": model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "system": system,
            "messages": messages,
        }

        if request.tools:
            data["tools"] = request.tools

        headers = {"Content-Type": "application/json", "x-api-key": self.api_key, "anthropic-version": "2023-06-01"}

        response = self._make_http_request(f"{self.base_url}/messages", headers, data)

        content = ""
        if response.get("content"):
            for block in response["content"]:
                if block.get("type") == "text":
                    content += block.get("text", "")

        return ChatResponse(
            content=content,
            model=response.get("model", model),
            usage=response.get("usage", {}),
            finish_reason=response.get("stop_reason", "stop"),
            raw_response=response,
        )


class GeminiClient(BaseAIClient):
    """Google Gemini客户端"""

    def _get_api_key_from_env(self) -> str:
        return os.getenv("GEMINI_API_KEY", "")

    def _get_default_base_url(self) -> str:
        return "https://generativelanguage.googleapis.com/v1beta"

    def _get_default_model(self) -> str:
        return "gemini-2.0-flash"

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Gemini聊天"""
        model = request.model or self.default_model

        # Gemini使用不同的格式
        contents = []
        for msg in request.messages:
            role = "user" if msg.role in ["user", "system"] else "model"
            contents.append({"role": role, "parts": [{"text": msg.content}]})

        data = {
            "contents": contents,
            "generationConfig": {"temperature": request.temperature, "maxOutputTokens": request.max_tokens},
        }

        headers = {"Content-Type": "application/json"}

        response = self._make_http_request(
            f"{self.base_url}/models/{model}:generateContent?key={self.api_key}", headers, data
        )

        content = ""
        if response.get("candidates"):
            for part in response["candidates"][0].get("content", {}).get("parts", []):
                content += part.get("text", "")

        usage = {}
        if response.get("usageMetadata"):
            usage = {
                "prompt_tokens": response["usageMetadata"].get("promptTokenCount", 0),
                "completion_tokens": response["usageMetadata"].get("candidatesTokenCount", 0),
                "total_tokens": response["usageMetadata"].get("totalTokenCount", 0),
            }

        return ChatResponse(content=content, model=model, usage=usage, finish_reason="stop", raw_response=response)


class OllamaClient(BaseAIClient):
    """Ollama本地模型客户端"""

    def _get_api_key_from_env(self) -> str:
        return ""  # Ollama不需要API Key

    def _get_default_base_url(self) -> str:
        return os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def _get_default_model(self) -> str:
        return "llama3.2"

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Ollama聊天"""
        model = request.model or self.default_model

        messages = []
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        data = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": request.temperature, "num_predict": request.max_tokens},
        }

        headers = {"Content-Type": "application/json"}

        response = self._make_http_request(f"{self.base_url}/api/chat", headers, data)

        return ChatResponse(
            content=response.get("message", {}).get("content", ""),
            model=model,
            usage={},
            finish_reason="stop",
            raw_response=response,
        )


class DeepSeekClient(BaseAIClient):
    """DeepSeek客户端"""

    def _get_api_key_from_env(self) -> str:
        return os.getenv("DEEPSEEK_API_KEY", "")

    def _get_default_base_url(self) -> str:
        return "https://api.deepseek.com/v1"

    def _get_default_model(self) -> str:
        return "deepseek-chat"

    def chat(self, request: ChatRequest) -> ChatResponse:
        """DeepSeek聊天 - 兼容OpenAI格式"""
        model = request.model or self.default_model

        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        data = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        response = self._make_http_request(f"{self.base_url}/chat/completions", headers, data)

        choice = response["choices"][0]
        return ChatResponse(
            content=choice["message"]["content"],
            model=response.get("model", model),
            usage=response.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=response,
        )


class QwenClient(BaseAIClient):
    """通义千问客户端"""

    def _get_api_key_from_env(self) -> str:
        return os.getenv("QWEN_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))

    def _get_default_base_url(self) -> str:
        return os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")

    def _get_default_model(self) -> str:
        return "qwen-max"

    def chat(self, request: ChatRequest) -> ChatResponse:
        """通义千问聊天"""
        model = request.model or self.default_model

        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        data = {
            "model": model,
            "input": {"messages": messages},
            "parameters": {
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "result_format": "message",
            },
        }

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        response = self._make_http_request(f"{self.base_url}/services/aigc/text-generation/generation", headers, data)

        # 解析通义千问响应格式
        output = response.get("output", {})
        choices = output.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
        else:
            content = output.get("text", "")

        usage = response.get("usage", {})

        return ChatResponse(
            content=content,
            model=model,
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            finish_reason="stop",
            raw_response=response,
        )


class DoubaoClient(BaseAIClient):
    """豆包客户端 (字节跳动)"""

    def _get_api_key_from_env(self) -> str:
        return os.getenv("DOUBAO_API_KEY", os.getenv("ARK_API_KEY", ""))

    def _get_default_base_url(self) -> str:
        return os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

    def _get_default_model(self) -> str:
        return "doubao-pro-32k"

    def chat(self, request: ChatRequest) -> ChatResponse:
        """豆包聊天 - 兼容OpenAI格式"""
        model = request.model or self.default_model

        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        data = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        response = self._make_http_request(f"{self.base_url}/chat/completions", headers, data)

        choice = response["choices"][0]
        return ChatResponse(
            content=choice["message"]["content"],
            model=response.get("model", model),
            usage=response.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=response,
        )


class XiaolongxiaClient(BaseAIClient):
    """小龙虾AI客户端 (Crawdad AI)"""

    def _get_api_key_from_env(self) -> str:
        return os.getenv("XIAOLONGXIA_API_KEY", os.getenv("CRAWDAD_API_KEY", ""))

    def _get_default_base_url(self) -> str:
        return os.getenv("XIAOLONGXIA_BASE_URL", "https://api.crawdad.ai/v1")

    def _get_default_model(self) -> str:
        return os.getenv("XIAOLONGXIA_MODEL", "crawdad-chat")

    def chat(self, request: ChatRequest) -> ChatResponse:
        """小龙虾AI聊天 - 兼容OpenAI格式"""
        model = request.model or self.default_model

        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        data = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        response = self._make_http_request(f"{self.base_url}/chat/completions", headers, data)

        choice = response["choices"][0]
        return ChatResponse(
            content=choice["message"]["content"],
            model=response.get("model", model),
            usage=response.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=response,
        )


class LocalClaudeClient(BaseAIClient):
    """本地Claude客户端 - 使用解压的Claude系统"""

    def _get_api_key_from_env(self) -> str:
        return ""  # 本地Claude不需要API Key

    def _get_default_base_url(self) -> str:
        return r"D:\Claude_Extracted"

    def _get_default_model(self) -> str:
        return "claude-local"

    def chat(self, request: ChatRequest) -> ChatResponse:
        """使用本地Claude进行聊天"""
        import json
        import subprocess
        import tempfile

        # 构建消息
        messages = []
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        # 创建临时文件存储请求
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "messages": messages,
                    "model": request.model or self.default_model,
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                },
                f,
            )
            request_file = f.name

        try:
            # 尝试使用Claude可执行文件
            claude_executable = r"D:\Claude_Extracted\bin\claude-code-tudou"
            if not os.path.exists(claude_executable):
                claude_executable = r"D:\Claude_Extracted\bin\claude-code-tudou.exe"

            if os.path.exists(claude_executable):
                # 使用Claude可执行文件
                result = subprocess.run(
                    [claude_executable, "--chat", request_file],
                    capture_output=True,
                    text=True,
                    cwd=r"D:\Claude_Extracted",
                    timeout=60,
                )
            else:
                # 尝试使用Node.js运行
                result = subprocess.run(
                    ["node", "main.js", "--chat", request_file],
                    capture_output=True,
                    text=True,
                    cwd=os.path.join(r"D:\Claude_Extracted", "嗷嗷的", "SRC"),
                    timeout=60,
                )

            # 解析响应
            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    content = response_data.get("content", "")
                except json.JSONDecodeError:
                    # 如果输出不是JSON，直接使用stdout
                    content = result.stdout
            else:
                # 如果执行失败，使用错误信息
                content = f"[错误] Claude执行失败: {result.stderr or result.stdout}"

            return ChatResponse(
                content=content,
                model=request.model or self.default_model,
                usage={},
                finish_reason="stop",
                raw_response={"stdout": result.stdout, "stderr": result.stderr},
            )
        finally:
            # 清理临时文件
            if os.path.exists(request_file):
                os.unlink(request_file)


class AIClientFactory:
    """AI客户端工厂 - 统一管理所有AI提供商"""

    _clients: Dict[AIProvider, type] = {
        AIProvider.STEPFUN: StepFunClient,
        AIProvider.OPENAI: OpenAIClient,
        AIProvider.ANTHROPIC: AnthropicClient,
        AIProvider.GEMINI: GeminiClient,
        AIProvider.OLLAMA: OllamaClient,
        AIProvider.DEEPSEEK: DeepSeekClient,
        AIProvider.QWEN: QwenClient,
        AIProvider.DOUBAO: DoubaoClient,
        AIProvider.XIAOLONGXIA: XiaolongxiaClient,
        AIProvider.LOCAL_CLAUDE: LocalClaudeClient,
    }

    _instances: Dict[AIProvider, BaseAIClient] = {}

    @classmethod
    def create(cls, provider: Union[AIProvider, str], **kwargs) -> BaseAIClient:
        """创建客户端实例"""
        if isinstance(provider, str):
            provider = AIProvider(provider.lower())

        if provider not in cls._clients:
            raise ValueError(f"不支持的AI提供商: {provider}")

        return cls._clients[provider](**kwargs)

    @classmethod
    def get_instance(cls, provider: Union[AIProvider, str] = None, **kwargs) -> BaseAIClient:
        """获取单例实例"""
        if provider is None:
            # 从环境变量获取默认提供商
            provider_str = os.getenv("AI_PROVIDER", "stepfun")
            provider = AIProvider(provider_str.lower())

        if isinstance(provider, str):
            provider = AIProvider(provider.lower())

        if provider not in cls._instances:
            cls._instances[provider] = cls.create(provider, **kwargs)

        return cls._instances[provider]

    @classmethod
    def list_providers(cls) -> List[str]:
        """列出所有支持的提供商"""
        return [p.value for p in cls._clients.keys()]

    @classmethod
    def register(cls, provider: AIProvider, client_class: type):
        """注册新的客户端"""
        cls._clients[provider] = client_class


class UnifiedAI:
    """
    统一AI接口 - 一行代码切换任意AI
    用法:
        ai = UnifiedAI()  # 使用默认配置
        ai = UnifiedAI(provider="openai")  # 指定OpenAI
        ai = UnifiedAI(provider="claude", model="claude-3-opus")  # 指定Claude

        # 聊天
        response = ai.chat("你好")

        # 带历史
        response = ai.chat("继续", keep_history=True)
    """

    def __init__(self, provider: str = None, model: str = None, **kwargs):
        """
        初始化统一AI接口

        Args:
            provider: AI提供商 (stepfun/openai/anthropic/gemini/ollama/deepseek/qwen/doubao/xiaolongxia)
            model: 模型名称
            **kwargs: 其他配置参数
        """
        self.provider = provider or os.getenv("AI_PROVIDER", "stepfun")
        self.model = model
        self.client = AIClientFactory.get_instance(self.provider, **kwargs)
        if model:
            self.client.default_model = model
        self._history: List[Message] = []

    def chat(
        self, message: str, keep_history: bool = True, temperature: float = 0.7, max_tokens: int = 2000, **kwargs
    ) -> str:
        """
        发送聊天消息

        Args:
            message: 用户消息
            keep_history: 是否保持对话历史
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 额外参数

        Returns:
            AI回复内容
        """
        # 构建请求
        messages = []
        if keep_history:
            messages.extend(self._history)
        messages.append(Message(role="user", content=message))

        request = ChatRequest(
            messages=messages, model=self.model, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

        # 发送请求
        response = self.client.chat(request)

        # 更新历史
        if keep_history:
            self._history.append(Message(role="user", content=message))
            self._history.append(Message(role="assistant", content=response.content))
            # 限制历史长度
            if len(self._history) > 20:
                self._history = self._history[-20:]

        return response.content

    def clear_history(self):
        """清空对话历史"""
        self._history = []
        self.client.clear_history()

    def get_history(self) -> List[Dict]:
        """获取对话历史"""
        return [{"role": m.role, "content": m.content} for m in self._history]

    def switch_provider(self, provider: str, model: str = None):
        """切换AI提供商"""
        self.provider = provider
        self.model = model or self.model
        self.client = AIClientFactory.get_instance(provider)
        if model:
            self.client.default_model = model
        self._history = []

    def __call__(self, message: str, **kwargs) -> str:
        """使实例可调用"""
        return self.chat(message, **kwargs)


# ============ 便捷函数 ============


def ask(message: str, provider: str = None, **kwargs) -> str:
    """快速提问 - 无历史"""
    ai = UnifiedAI(provider=provider)
    return ai.chat(message, keep_history=False, **kwargs)


def chat_session(provider: str = None, model: str = None):
    """启动对话会话"""
    ai = UnifiedAI(provider=provider, model=model)
    provider_name = provider or os.getenv("AI_PROVIDER", "stepfun")

    print(f"🤖 {provider_name.upper()} 对话模式 (输入 'exit' 退出, 'clear' 清空历史)")
    print("-" * 50)

    while True:
        try:
            user_input = input("\n你: ").strip()

            if user_input.lower() == "exit":
                print("👋 再见!")
                break
            elif user_input.lower() == "clear":
                ai.clear_history()
                print("✅ 历史已清空")
                continue
            elif not user_input:
                continue

            print("\n🤖 思考中...")
            response = ai.chat(user_input)
            print(f"\nAI: {response}")

        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")


# ============ 向后兼容 ============


class StepFunClientLegacy(StepFunClient):
    """向后兼容的阶跃AI客户端"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key)
        self.messages: List[Dict] = []

    def chat(self, message: str, model: str = None, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """兼容旧版接口"""
        request = ChatRequest(
            messages=[Message(role="user", content=message)],
            model=model or self.default_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # 添加历史
        for msg in self.messages[-10:]:
            request.messages.insert(0, Message(role=msg["role"], content=msg["content"]))

        response = super().chat(request)

        # 保存历史
        self.messages.append({"role": "user", "content": message})
        self.messages.append({"role": "assistant", "content": response.content})

        if len(self.messages) > 20:
            self.messages = self.messages[-20:]

        return response.content


# 保持旧版导入兼容
StepFunClientOld = StepFunClientLegacy


if __name__ == "__main__":
    # 测试
    print("支持的AI提供商:", AIClientFactory.list_providers())

    # 测试统一接口
    print("\n=== 测试统一接口 ===")
    ai = UnifiedAI(provider="stepfun")
    print(f"当前提供商: {ai.provider}")

    # 测试快速提问
    print("\n=== 测试快速提问 ===")
    result = ask("你好，请用一句话介绍自己", provider="stepfun")
    print(f"回复: {result}")
