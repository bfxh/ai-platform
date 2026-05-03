# MCP Core 智能体系统

## 系统概述

MCP Core 智能体系统是一个基于竞争和融合机制的智能体管理框架，支持：

- **智能体竞争**：不同智能体之间通过执行任务进行竞争
- **智能体融合**：获胜的智能体可以融合失败智能体的能力
- **智能体进化**：通过经验值和升级机制，智能体可以不断进化
- **GitHub项目集成**：自动搜索和集成GitHub上的智能体相关项目

## 目录结构

```
agent/
├── base.py          # 智能体基类和竞争管理器
├── examples.py      # 智能体示例实现
├── github_integration.py  # GitHub项目集成模块
├── main.py          # 智能体系统主入口
├── README.md        # 本文档
└── external/        # 从GitHub集成的项目
```

## 核心功能

### 1. 智能体基类

`Agent` 基类定义了智能体的基本结构和行为：

- **元数据**：名称、描述、版本、类型等
- **能力系统**：定义智能体的各项能力值
- **技能系统**：集成MCP技能系统
- **生命周期管理**：初始化、执行、关闭
- **经验值和升级**：通过执行任务获得经验值，达到一定经验值后升级
- **融合机制**：与其他智能体融合，吸收其能力
- **大模型集成**：使用本地大模型进行自我学习和进化
- **内存优化**：自动优化内存使用，减少系统资源消耗

### 2. 智能体管理器

`AgentManager` 负责管理智能体的生命周期和竞争过程：

- **智能体注册**：注册和管理智能体实例
- **任务执行**：分配任务给智能体并执行
- **竞争机制**：组织智能体之间的竞争
- **评估系统**：评估智能体的执行结果
- **排名系统**：根据竞争结果生成排名
- **进化管理**：记录智能体的融合和进化历史

### 3. 智能体类型

系统支持三种类型的智能体：

- **通用智能体**：各方面能力均衡
- **专业智能体**：在特定领域有专长
- **混合智能体**：结合多种能力

### 4. GitHub项目集成

`GitHubIntegrator` 模块用于搜索和集成GitHub上的智能体相关项目：

- **项目搜索**：搜索与智能体、竞争系统相关的项目
- **项目分析**：分析项目的结构和质量
- **集成建议**：根据项目分析结果提供集成建议
- **自动集成**：自动克隆和集成项目到系统中

### 5. 大模型集成

`LLMIntegrator` 模块用于集成和管理本地大模型：

- **模型发现**：自动发现本地存储的大模型
- **模型加载**：根据内存情况加载合适的大模型
- **模型推理**：使用大模型进行推理和学习
- **内存优化**：智能管理内存使用，避免内存溢出
- **智能体增强**：使用大模型增强智能体的能力
- **自我学习**：智能体通过大模型不断学习和进化

## 快速开始

### 1. 运行智能体竞争

```bash
# 运行智能体竞争，默认5轮
python agent/main.py --competition

# 运行指定轮数的竞争
python agent/main.py --competition --rounds 10
```

### 2. 搜索GitHub项目

```bash
# 搜索智能体相关项目
python agent/main.py --github

# 搜索并集成前3个项目
python agent/main.py --github --integrate --max-results 5
```

### 3. 大模型管理

```bash
# 发现本地大模型
python agent/main.py --models

# 为智能体加载大模型
python agent/main.py --load-model data_analyst:model_name

# 训练智能体
python agent/main.py --train data_analyst

# 优化内存使用
python agent/main.py --optimize-memory
```

### 3. 自定义智能体

```python
from agent.base import Agent, AgentType

class MyAgent(Agent):
    name = "my_agent"
    description = "我的自定义智能体"
    version = "1.0.0"
    agent_type = AgentType.SPECIALIZED
    skills = ["github_opensource"]  # 集成的技能
    abilities = {
        "intelligence": 85,
        "speed": 75
    }

    def execute(self, task):
        # 执行任务的逻辑
        return {
            "success": True,
            "result": "任务完成",
            "execution_time": 5.0
        }

# 注册智能体
from agent.base import get_agent_manager
manager = get_agent_manager()
manager.register(MyAgent())

# 执行任务
result = manager.execute_task("my_agent", {"task_type": "data_analysis"})
```

## 智能体示例

系统内置了以下智能体示例：

1. **DataAnalystAgent**：数据分析智能体，擅长处理和分析数据
2. **CreativeWriterAgent**：创意写作智能体，擅长生成创意内容
3. **CodeGeneratorAgent**：代码生成智能体，擅长生成和优化代码
4. **GeneralPurposeAgent**：通用智能体，各方面能力均衡

## 配置和依赖

### 依赖

- Python 3.9+
- requests (用于GitHub API调用)
- git (用于克隆GitHub项目)
- llama-cpp-python (用于加载LLaMA模型)
- transformers (用于加载其他类型的模型)
- psutil (用于内存管理)

### 配置

- **GITHUB_TOKEN**：环境变量，用于GitHub API认证（可选，无token时API调用频率会受限）
- **AI_ROOT**：环境变量，指定AI系统的根目录

## 日志

系统会在 `logs/` 目录下生成以下日志文件：

- `agent.log`：智能体系统日志
- `github_integration.log`：GitHub集成日志
- `agent_main.log`：主入口日志

## 集成报告

系统会在 `reports/` 目录下生成GitHub项目集成报告：

- `github_projects_report.md`：GitHub项目搜索报告
- `github_integration_report.md`：GitHub项目集成报告

## 扩展和定制

### 1. 创建自定义智能体

继承 `Agent` 基类，实现 `execute` 方法即可创建自定义智能体。

### 2. 扩展竞争机制

可以修改 `AgentManager` 中的 `_evaluate_winner` 方法来调整竞争评估逻辑。

### 3. 扩展融合机制

可以重写 `Agent` 类中的 `fuse_with` 方法来实现自定义的融合逻辑。

### 4. 集成外部项目

系统会自动搜索和集成GitHub上的智能体相关项目，集成到 `agent/external/` 目录。

## 示例输出

### 智能体竞争输出

```
2024-01-01 12:00:00 - AgentManager - INFO - 开始智能体竞争，共 5 轮
2024-01-01 12:00:00 - AgentManager - INFO - 注册了 4 个智能体:
2024-01-01 12:00:00 - AgentManager - INFO -   - data_analyst: 数据分析智能体 - 擅长处理和分析数据 (等级: 1, 类型: specialized)
2024-01-01 12:00:00 - AgentManager - INFO -   - creative_writer: 创意写作智能体 - 擅长创意内容生成 (等级: 1, 类型: specialized)
2024-01-01 12:00:00 - AgentManager - INFO -   - code_generator: 代码生成智能体 - 擅长生成和优化代码 (等级: 1, 类型: specialized)
2024-01-01 12:00:00 - AgentManager - INFO -   - general_purpose: 通用智能体 - 各方面能力均衡 (等级: 1, 类型: general)
2024-01-01 12:00:00 - AgentManager - INFO - data_analyst vs creative_writer
2024-01-01 12:00:05 - AgentManager - INFO - data_analyst vs code_generator
2024-01-01 12:00:10 - AgentManager - INFO - data_analyst vs general_purpose
2024-01-01 12:00:15 - AgentManager - INFO - creative_writer vs code_generator
2024-01-01 12:00:20 - AgentManager - INFO - creative_writer vs general_purpose
2024-01-01 12:00:25 - AgentManager - INFO - code_generator vs general_purpose
2024-01-01 12:00:30 - AgentManager - INFO - 智能体竞争结束
2024-01-01 12:00:30 - AgentManager - INFO - 智能体竞争结果:
2024-01-01 12:00:30 - AgentManager - INFO - 排名:
2024-01-01 12:00:30 - AgentManager - INFO -   1. code_generator - 胜率: 83.33%, 等级: 2
2024-01-01 12:00:30 - AgentManager - INFO -   2. general_purpose - 胜率: 66.67%, 等级: 2
2024-01-01 12:00:30 - AgentManager - INFO -   3. data_analyst - 胜率: 33.33%, 等级: 1
2024-01-01 12:00:30 - AgentManager - INFO -   4. creative_writer - 胜率: 0.00%, 等级: 1
2024-01-01 12:00:30 - AgentManager - INFO - 进化历史:
2024-01-01 12:00:30 - AgentManager - INFO -   - code_generator 融合了 creative_writer
2024-01-01 12:00:30 - AgentManager - INFO -   - general_purpose 融合了 data_analyst
```

### 大模型管理输出

```
2024-01-01 12:00:00 - AgentSystem - INFO - 发现本地大模型
2024-01-01 12:00:00 - LLMIntegrator - INFO - 开始发现本地大模型
2024-01-01 12:00:01 - LLMIntegrator - INFO - 搜索路径: C:\Users\User\Models
2024-01-01 12:00:01 - LLMIntegrator - INFO - 发现 3 个大模型
2024-01-01 12:00:01 - AgentSystem - INFO - 发现 3 个本地大模型:
2024-01-01 12:00:01 - AgentSystem - INFO -   1. llama-2-7b-chat.Q4_K_M (llama, 3500.00 MB)
2024-01-01 12:00:01 - AgentSystem - INFO -      路径: C:\Users\User\Models\llama-2-7b-chat.Q4_K_M.gguf
2024-01-01 12:00:01 - AgentSystem - INFO -   2. mistral-7b-v0.1.Q5_K_M (llama, 4000.00 MB)
2024-01-01 12:00:01 - AgentSystem - INFO -      路径: C:\Users\User\Models\mistral-7b-v0.1.Q5_K_M.gguf
2024-01-01 12:00:01 - AgentSystem - INFO -   3. gemma-7b-it.Q4_K_M (llama, 3800.00 MB)
2024-01-01 12:00:01 - AgentSystem - INFO -      路径: C:\Users\User\Models\gemma-7b-it.Q4_K_M.gguf
```

### 智能体训练输出

```
2024-01-01 12:00:00 - AgentSystem - INFO - 训练智能体 data_analyst
2024-01-01 12:00:00 - data_analyst - INFO - data_analyst 开始训练
2024-01-01 12:00:01 - LLMAgentEnhancer - INFO - 增强智能体: data_analyst
2024-01-01 12:00:01 - data_analyst - INFO - 智能体当前能力: {'data_analysis': 90, 'problem_solving': 85, 'speed': 70}
2024-01-01 12:00:05 - data_analyst - INFO - 应用改进: 提高数据分析能力到 95
2024-01-01 12:00:05 - data_analyst - INFO - 应用改进: 提高问题解决能力到 90
2024-01-01 12:00:05 - data_analyst - INFO - 智能体增强成功: data_analyst
2024-01-01 12:00:05 - data_analyst - INFO - data_analyst 获得 200 经验值
2024-01-01 12:00:05 - data_analyst - INFO - data_analyst 训练成功
```

### GitHub项目搜索输出

```
2024-01-01 12:00:00 - GitHubIntegrator - INFO - 搜索GitHub项目: agent competition
2024-01-01 12:00:01 - GitHubIntegrator - INFO - 找到 10 个相关项目
2024-01-01 12:00:01 - AgentSystem - INFO - 找到 10 个智能体相关项目:
2024-01-01 12:00:01 - AgentSystem - INFO -   1. openai/gym (★15000, 📁3000)
2024-01-01 12:00:01 - AgentSystem - INFO -      描述: A toolkit for developing and comparing reinforcement learning algorithms.
2024-01-01 12:00:01 - AgentSystem - INFO -      URL: https://github.com/openai/gym
2024-01-01 12:00:01 - AgentSystem - INFO -   2. huggingface/transformers (★100000, 📁20000)
2024-01-01 12:00:01 - AgentSystem - INFO -      描述: State-of-the-art Machine Learning for PyTorch and TensorFlow 2.0.
2024-01-01 12:00:01 - AgentSystem - INFO -      URL: https://github.com/huggingface/transformers
```

## 总结

MCP Core 智能体系统提供了一个完整的框架，用于创建、管理和竞争智能体。通过融合机制和大模型集成，智能体可以不断进化，吸收其他智能体的优势，同时利用大模型进行自我学习和能力提升。

### 系统特点

1. **真正的智能进化**：智能体通过竞争、融合和大模型学习不断进化，能力持续提升
2. **自我学习能力**：利用本地大模型进行自我学习和优化
3. **内存优化**：智能管理内存使用，确保系统稳定运行
4. **GitHub集成**：自动搜索和集成外部智能体项目
5. **跨平台兼容**：支持在不同操作系统上运行

### 应用场景

- **自动化任务处理**：智能体可以自动处理各种任务，提高效率
- **多智能体协作**：不同类型的智能体可以协作完成复杂任务
- **智能体进化研究**：研究智能体的进化过程和规律
- **机器学习模型训练**：利用大模型加速智能体的学习和进化
- **AI助手开发**：构建更智能、更高效的AI助手

### 未来发展

- **更高级的大模型集成**：支持更多类型的大模型和更复杂的学习策略
- **智能体社区**：建立智能体共享和交流的社区
- **实时学习**：智能体可以在执行任务的同时实时学习和优化
- **多模态能力**：支持处理和生成多种类型的数据

通过不断的竞争、融合和学习，MCP Core 智能体系统可以持续进化，为各种任务提供更智能、更高效的解决方案。
