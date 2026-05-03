#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude 本地集成模块 - 将解压的 Claude 系统作为免费模型集成到 TRAE
"""

import json
import os
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional

# 添加路径
sys.path.insert(0, r"\python\core")
from ai_adapter import AIClientFactory, AIProvider, BaseAIClient, ChatRequest, ChatResponse, Message


class LocalClaudeClient(BaseAIClient):
    """本地 Claude 客户端 - 使用解压的 Claude 系统作为免费模型"""

    def __init__(self, api_key: str = None, base_url: str = None, **kwargs):
        super().__init__(api_key=api_key, base_url=base_url, **kwargs)
        self.claude_path = kwargs.get("claude_path", r"D:\Claude_Extracted")
        self.claude_executable = self._find_claude_executable()
        self.default_model = "claude-local"

    def _get_api_key_from_env(self) -> str:
        return ""  # 本地 Claude 不需要 API Key

    def _get_default_base_url(self) -> str:
        return self.claude_path

    def _get_default_model(self) -> str:
        return "claude-local"

    def _find_claude_executable(self) -> str:
        """查找 Claude 可执行文件"""
        # 检查主要路径
        possible_paths = [
            os.path.join(self.claude_path, "bin", "claude-code-tudou"),
            os.path.join(self.claude_path, "bin", "claude-code-tudou.exe"),
            os.path.join(self.claude_path, "claude-code-tudou"),
            os.path.join(self.claude_path, "claude-code-tudou.exe"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 如果找不到可执行文件，尝试使用 Node.js 运行
        package_json = os.path.join(self.claude_path, "package.json")
        if os.path.exists(package_json):
            return "node"

        raise FileNotFoundError("无法找到 Claude 可执行文件")

    def chat(self, request: ChatRequest) -> ChatResponse:
        """使用本地 Claude 进行聊天"""
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
            # 执行 Claude 命令
            if self.claude_executable.endswith(".exe") or self.claude_executable == "claude-code-tudou":
                # 使用 Claude 可执行文件
                result = subprocess.run(
                    [self.claude_executable, "--chat", request_file],
                    capture_output=True,
                    text=True,
                    cwd=self.claude_path,
                    timeout=60,
                )
            else:
                # 使用 Node.js 运行
                result = subprocess.run(
                    ["node", "main.js", "--chat", request_file],
                    capture_output=True,
                    text=True,
                    cwd=os.path.join(self.claude_path, "嗷嗷的", "SRC"),
                    timeout=60,
                )

            # 解析响应
            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    content = response_data.get("content", "")
                except json.JSONDecodeError:
                    # 如果输出不是 JSON，直接使用 stdout
                    content = result.stdout
            else:
                # 如果执行失败，使用错误信息
                content = f"[错误] Claude 执行失败: {result.stderr or result.stdout}"

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


def register_local_claude():
    """注册本地 Claude 客户端到 AIClientFactory"""
    # 添加新的 AI 提供商
    try:
        # 检查是否已经注册
        if hasattr(AIProvider, "LOCAL_CLAUDE"):
            print("本地 Claude 已经注册")
            return

        # 动态添加新的提供商
        AIProvider.LOCAL_CLAUDE = "local_claude"
        AIProvider._value2member_map_["local_claude"] = AIProvider.LOCAL_CLAUDE

        # 注册客户端
        AIClientFactory.register(AIProvider.LOCAL_CLAUDE, LocalClaudeClient)
        print("✅ 本地 Claude 客户端注册成功")
    except Exception as e:
        print(f"❌ 注册本地 Claude 失败: {e}")


def test_local_claude():
    """测试本地 Claude 客户端"""
    try:
        # 创建本地 Claude 客户端
        client = AIClientFactory.create("local_claude")

        # 构建测试请求
        request = ChatRequest(
            messages=[Message(role="user", content="你好，请用一句话介绍自己")],
            model="claude-local",
            temperature=0.7,
            max_tokens=500,
        )

        # 发送请求
        response = client.chat(request)
        print(f"📝 测试结果:")
        print(f"提供商: local_claude")
        print(f"模型: {response.model}")
        print(f"回复: {response.content}")
        print("✅ 本地 Claude 测试成功")
        return True
    except Exception as e:
        print(f"❌ 本地 Claude 测试失败: {e}")
        return False


def integrate_claude_into_traef():
    """将本地 Claude 集成到 TRAE 系统"""
    print("🔧 开始集成本地 Claude 到 TRAE...")

    # 1. 注册本地 Claude 客户端
    register_local_claude()

    # 2. 测试本地 Claude
    test_local_claude()

    # 3. 更新配置文件
    update_config_file()

    print("🎉 本地 Claude 集成完成!")
    print("\n使用方法:")
    print("1. 导入统一接口: from ai_unified import AI")
    print("2. 创建 Claude 实例: ai = AI(provider='local_claude')")
    print("3. 开始使用: result = ai('你好')")


def update_config_file():
    """更新配置文件，添加本地 Claude"""
    config_path = r"\python\core\ai_config.py"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_content = f.read()

        # 检查是否已经添加本地 Claude
        if "local_claude" not in config_content:
            # 添加本地 Claude 到配置
            updated_content = config_content.replace(
                "SUPPORTED_PROVIDERS = [", "SUPPORTED_PROVIDERS = [\n    'local_claude',"
            )

            with open(config_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            print("✅ 配置文件已更新")
        else:
            print("ℹ️ 配置文件已经包含本地 Claude")
    else:
        print("⚠️ 配置文件不存在，跳过更新")


if __name__ == "__main__":
    integrate_claude_into_traef()
