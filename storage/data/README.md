# Models 模型库

> AI/ML 模型收集与整理
> 更新时间：2026-03-24

## 📚 目录结构

```
\python\Models\
├── README.md                    # 本文件
├── 📁 LLM/                      # 大语言模型
├── 📁 Code/                     # 代码模型
├── 📁 Vision/                   # 视觉模型
├── 📁 Audio/                    # 音频模型
├── 📁 Multimodal/               # 多模态模型
├── 📁 Embedding/                # 嵌入模型
├── 📁 Fine-tuning/              # 微调模型
├── 📁 Local/                    # 本地部署模型
└── 📁 APIs/                     # API服务
```

---

## 🧠 LLM - 大语言模型

### 闭源模型 (API)

| 模型 | 提供商 | 上下文 | 特点 | 定价 |
|------|--------|--------|------|------|
| **GPT-4o** | OpenAI | 128K | 多模态、最强性能 | $5/M tokens |
| **GPT-4o-mini** | OpenAI | 128K | 性价比高 | $0.15/M tokens |
| **o1/o3** | OpenAI | 200K | 推理模型 | $15/M tokens |
| **Claude 3.5 Sonnet** | Anthropic | 200K | 编码强、安全 | $3/M tokens |
| **Claude 3.5 Haiku** | Anthropic | 200K | 快速、便宜 | $0.25/M tokens |
| **Claude 3 Opus** | Anthropic | 200K | 最强推理 | $15/M tokens |
| **Gemini 2.0 Pro** | Google | 2M | 超长上下文 | $3.5/M tokens |
| **Gemini 2.0 Flash** | Google | 1M | 快速响应 | $0.35/M tokens |
| **Nova Pro** | Amazon | 300K | AWS集成 | $0.8/M tokens |
| **Command R+** | Cohere | 128K | RAG优化 | $3/M tokens |

### 开源模型 (本地/API)

| 模型 | 参数 | 上下文 | 特点 | 下载 |
|------|------|--------|------|------|
| **Llama 3.3** | 70B/405B | 128K | Meta最强 | [HuggingFace](https://huggingface.co/meta-llama) |
| **Llama 3.2** | 1B/3B/11B/90B | 128K | 多模态 | [HuggingFace](https://huggingface.co/meta-llama) |
| **Qwen 2.5** | 0.5B-72B | 128K | 阿里、中文强 | [HuggingFace](https://huggingface.co/Qwen) |
| **DeepSeek V3** | 671B | 64K | 推理强、便宜 | [HuggingFace](https://huggingface.co/deepseek-ai) |
| **DeepSeek R1** | 671B | 64K | 推理模型 | [HuggingFace](https://huggingface.co/deepseek-ai) |
| **Mixtral 8x22B** | 141B | 64K | MoE架构 | [HuggingFace](https://huggingface.co/mistralai) |
| **Mistral Large 2** | 123B | 128K | 欧洲最强 | [HuggingFace](https://huggingface.co/mistralai) |
| **Yi-34B** | 34B | 200K | 零一万物 | [HuggingFace](https://huggingface.co/01-ai) |
| **GLM-4** | 9B | 128K | 清华智谱 | [HuggingFace](https://huggingface.co/THUDM) |
| **Phi-4** | 14B | 16K | 微软小模型 | [HuggingFace](https://huggingface.co/microsoft) |

---

## 💻 Code - 代码模型

### 代码生成

| 模型 | 提供商 | 特点 | 支持语言 |
|------|--------|------|----------|
| **Claude 3.5 Sonnet** | Anthropic | 最强编码 | 全语言 |
| **GPT-4o** | OpenAI | 代码能力强 | 全语言 |
| **o1** | OpenAI | 复杂推理 | 全语言 |
| **CodeLlama** | Meta | 开源代码 | Python/C++/JS |
| **DeepSeek Coder** | DeepSeek | 开源最强 | 全语言 |
| **StarCoder 2** | BigCode | 开源 | 80+语言 |
| **Codestral** | Mistral | 开源 | 80+语言 |
| **CodeQwen** | Alibaba | 中文支持 | 全语言 |

### 代码补全

| 模型 | 提供商 | 特点 |
|------|--------|------|
| **GitHub Copilot** | GitHub/OpenAI | IDE集成 |
| **Codeium** | Codeium | 免费替代 |
| **TabNine** | TabNine | 本地支持 |
| **Cursor** | Cursor | AI编辑器 |
| **Continue** | Continue | 开源助手 |

---

## 👁️ Vision - 视觉模型

### 图像理解

| 模型 | 提供商 | 特点 |
|------|--------|------|
| **GPT-4o Vision** | OpenAI | 最强多模态 |
| **Claude 3.5 Sonnet** | Anthropic | 视觉推理强 |
| **Gemini 2.0** | Google | 原生多模态 |
| **Qwen-VL** | Alibaba | 中文视觉 |
| **LLaVA** | 开源 | 开源视觉 |
| **InternVL** | OpenGVLab | 开源强 |

### 图像生成

| 模型 | 提供商 | 特点 |
|------|--------|------|
| **DALL-E 3** | OpenAI | 文本到图像 |
| **Midjourney** | Midjourney | 艺术风格 |
| **Stable Diffusion 3** | Stability AI | 开源 |
| **FLUX** | Black Forest Labs | 开源强 |
| **Imagen 3** | Google | 真实感强 |
| **Kling** | 快手 | 视频生成 |

### OCR/文档理解

| 模型 | 提供商 | 特点 |
|------|--------|------|
| **PaddleOCR** | Baidu | 中文OCR强 |
| **EasyOCR** | 开源 | 多语言 |
| **Tesseract** | Google | 经典OCR |
| **Qwen-VL** | Alibaba | 文档理解 |
| **GPT-4o** | OpenAI | 通用文档 |

---

## 🔊 Audio - 音频模型

### 语音识别 (ASR)

| 模型 | 提供商 | 特点 |
|------|--------|------|
| **Whisper v3** | OpenAI | 最强通用 |
| **Whisper Large v3** | OpenAI | 多语言 |
| **SenseVoice** | Alibaba | 中文强 |
| **Paraformer** | Alibaba | 中文实时 |
| **Conformer** | Google | 云端 |

### 语音合成 (TTS)

| 模型 | 提供商 | 特点 |
|------|--------|------|
| **GPT-4o TTS** | OpenAI | 自然度高 |
| **ElevenLabs** | ElevenLabs | 情感丰富 |
| **CosyVoice** | Alibaba | 中文自然 |
| **ChatTTS** | 开源 | 开源强 |
| **Fish Speech** | 开源 | 实时合成 |

### 音乐生成

| 模型 | 提供商 | 特点 |
|------|--------|------|
| **Suno** | Suno | 歌曲生成 |
| **Udio** | Udio | 音乐创作 |
| **MusicGen** | Meta | 开源 |
| **AudioCraft** | Meta | 开源套件 |

---

## 🌐 Multimodal - 多模态模型

| 模型 | 提供商 | 能力 | 特点 |
|------|--------|------|------|
| **GPT-4o** | OpenAI | 文本+图像+音频 | 端到端多模态 |
| **Claude 3.5 Sonnet** | Anthropic | 文本+图像 | 视觉推理强 |
| **Gemini 2.0** | Google | 文本+图像+音频+视频 | 原生多模态 |
| **Qwen2-VL** | Alibaba | 文本+图像+视频 | 中文支持 |
| **LLaVA-1.6** | 开源 | 文本+图像 | 开源视觉 |
| **InternVL2** | OpenGVLab | 文本+图像 | 开源强 |

---

## 📊 Embedding - 嵌入模型

### 文本嵌入

| 模型 | 维度 | 特点 | 适用场景 |
|------|------|------|----------|
| **text-embedding-3-large** | 3072 | OpenAI最强 | 通用 |
| **text-embedding-3-small** | 1536 | OpenAI经济 | 通用 |
| **BGE-M3** | 1024 | 开源最强 | RAG |
| **GTE-large** | 1024 | 阿里开源 | RAG |
| **E5-mistral** | 4096 | 长文本 | 文档 |
| **Jina-Embeddings** | 768 | 多语言 | 多语言 |
| **Cohere Embed** | 1024 | 商业 | 通用 |

### 多模态嵌入

| 模型 | 提供商 | 特点 |
|------|--------|------|
| **CLIP** | OpenAI | 图文对齐 |
| **OpenCLIP** | 开源 | 开源CLIP |
| **Jina-CLIP** | Jina AI | 多语言CLIP |

---

## 🔧 Fine-tuning - 微调模型

### 微调方法

| 方法 | 描述 | 显存需求 | 适用场景 |
|------|------|----------|----------|
| **Full Fine-tuning** | 全参数微调 | 高 | 数据充足 |
| **LoRA** | 低秩适配 | 低 | 大多数场景 |
| **QLoRA** | 量化LoRA | 极低 | 消费级显卡 |
| **Prefix Tuning** | 前缀微调 | 中 | 特定任务 |
| **P-Tuning** | 提示微调 | 低 | 中文场景 |
| **Adapter** | 适配器 | 低 | 多任务 |

### 微调框架

| 框架 | 特点 | 链接 |
|------|------|------|
| **LLaMA-Factory** | 一站式微调 | [GitHub](https://github.com/hiyouga/LLaMA-Factory) |
| **Axolotl** | YAML配置 | [GitHub](https://github.com/OpenAccess-AI-Collective/axolotl) |
| **Unsloth** | 2倍速微调 | [GitHub](https://github.com/unslothai/unsloth) |
| **LitGPT** | Lightning | [GitHub](https://github.com/Lightning-AI/litgpt) |
| **TRL** | HuggingFace | [GitHub](https://github.com/huggingface/trl) |

---

## 🖥️ Local - 本地部署

### 本地推理框架

| 框架 | 特点 | 支持平台 |
|------|------|----------|
| **Ollama** | 最简单 | Win/Mac/Linux |
| **LM Studio** | GUI界面 | Win/Mac/Linux |
| **llama.cpp** | 最高效 | 全平台 |
| **vLLM** | 高吞吐 | Linux |
| **Text Generation Inference** | HF官方 | Linux |
| **KoboldCPP** | 游戏向 | Win/Mac/Linux |

### 本地模型推荐配置

| 模型大小 | 显存需求 | 推荐显卡 | 量化 |
|----------|----------|----------|------|
| 7B | 8GB | RTX 3060 12G | Q4 |
| 13B | 16GB | RTX 4080 16G | Q4 |
| 34B | 24GB | RTX 4090 24G | Q4 |
| 70B | 48GB | 2x RTX 4090 | Q4 |
| 405B | 300GB+ | 8x A100 80G | Q4 |

---

## 🔌 APIs - API服务

### 国内API平台

| 平台 | 特点 | 支持模型 |
|------|------|----------|
| **硅基流动** | 便宜、快 | 全系列 |
| **阿里云百炼** | 稳定 | Qwen/通义 |
| **百度千帆** | 文心 | 文心系列 |
| **智谱AI** | GLM | GLM系列 |
| **DeepSeek** | 便宜 | DeepSeek |
| **MiniMax** | 海螺 | MiniMax |
| **月之暗面** | Kimi | Moonshot |

### 国际API平台

| 平台 | 特点 | 支持模型 |
|------|------|----------|
| **OpenAI** | 官方 | GPT系列 |
| **Anthropic** | 官方 | Claude系列 |
| **Google AI** | 官方 | Gemini系列 |
| **Groq** | 极速 | 多种 |
| **Together AI** | 开源 | 开源模型 |
| **Fireworks** | 快速 | 多种 |

---

## 🛠️ 模型选型指南

### 按任务选择

| 任务 | 推荐模型 | 备选 |
|------|----------|------|
| 通用对话 | Claude 3.5 Sonnet | GPT-4o |
| 代码生成 | Claude 3.5 Sonnet | o1 |
| 长文档处理 | Gemini 2.0 Pro | Claude 3.5 |
| 中文任务 | Qwen 2.5 | DeepSeek |
| 本地部署 | Llama 3.3 | Qwen 2.5 |
| 成本敏感 | GPT-4o-mini | Claude Haiku |
| 复杂推理 | o1 | DeepSeek R1 |

### 按场景选择

| 场景 | 推荐方案 |
|------|----------|
| 企业应用 | Claude 3.5 Sonnet API |
| 个人开发 | GPT-4o-mini API |
| 离线环境 | Llama 3.3 70B 本地 |
| 移动端 | Qwen 2.5 7B 量化 |
| RAG应用 | BGE-M3 + Claude 3.5 |
| 代码助手 | Claude 3.5 + Copilot |

---

## 📚 参考资料

- [HuggingFace](https://huggingface.co/) - 模型仓库
- [LMSYS Chatbot Arena](https://chat.lmsys.org/) - 模型评测
- [Artificial Analysis](https://artificialanalysis.ai/) - 模型对比
- [OpenRouter](https://openrouter.ai/) - 统一API

---

*持续更新中...*
