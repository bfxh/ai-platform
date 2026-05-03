# EXo Cluster Skill

EXo 分布式 AI 集群配置与管理技能

## 功能

- 自动集群节点发现
- 动态模型分区
- 内存聚合计算
- 跨设备算力调度
- 集群状态监控

## 快速开始

### 1. 安装 EXo
```bash
install-exo.bat
```

### 2. 启动集群节点
```bash
start-cluster.bat
```

### 3. 查看集群状态
访问 http://localhost:52415

## 集群配置

### 节点 1（华为电脑）
- IP: 192.168.1.3 / 192.168.2.3
- 端口: 50051
- 角色: 主节点

### 节点 2（另一台电脑）
- IP: 192.168.1.10 / 192.168.2.10
- 端口: 50051
- 角色: 工作节点

## 支持的模型

- LLaMA 3.1 (8B, 70B)
- Mistral
- Qwen
- DeepSeek
- LlaVA

## API 使用

```python
import requests

response = requests.post(
    "http://localhost:52415/v1/chat/completions",
    json={
        "model": "llama-3.1-8b",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)
```

## 故障排除

### 节点无法发现
- 检查防火墙设置
- 确认同一网络
- 尝试手动指定节点

### 内存不足
- 使用量化模型 (q4_k_m)
- 减少并发请求
- 增加虚拟内存

## 工作流

1. 设备发现 → 2. 集群组建 → 3. 模型加载 → 4. 推理服务
