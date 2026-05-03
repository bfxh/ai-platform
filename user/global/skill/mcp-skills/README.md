# MCP 技能包 - 双电脑集群与高速传输

> 为华为电脑与另一台电脑搭建高速传输通道和 EXo AI 集群
> 版本: 2.0 (增加通知与工作流功能)

---

## 技能列表

### 1. network-transfer-skill ⭐
**功能**：高速局域网文件传输
- 自动设备发现
- 多线程传输
- 双网卡负载均衡
- 断点续传

**核心文件**：
- `high_speed_transfer_v2.py` - 发送端 (带通知)
- `high_speed_receive_v2.py` - 接收端 (带通知)
- `scan_network.bat` - 网络扫描

---

### 2. exo-cluster-skill
**功能**：EXo 分布式 AI 集群管理
- 自动节点发现
- 动态模型分区
- 内存聚合
- 集群监控

**核心文件**：
- `install-exo.bat` - 安装脚本
- `start-cluster.bat` - 启动脚本
- `exo-config.json` - 配置文件

---

### 3. system-config-skill
**功能**：Windows 系统自动化配置
- 防火墙规则
- 网络共享
- 服务管理
- 环境配置

**核心文件**：
- `configure_target.py` - 目标电脑配置
- `configure_firewall.bat`
- `setup_shares.bat`

---

### 4. notification-skill 🆕
**功能**：跨设备通知与状态同步
- Windows 桌面通知
- 声音提示
- 传输进度实时通知
- 错误告警

**核心文件**：
- `notification_service.py` - 通知服务
- 支持通知类型:
  - `transfer_start` - 传输开始
  - `transfer_progress` - 传输进度
  - `transfer_complete` - 传输完成
  - `config_complete` - 配置完成
  - `exo_started` - EXo 启动
  - `error` - 错误通知

---

### 5. monitoring-skill 🆕
**功能**：系统监控与性能分析
- 网络速度测试
- 系统资源监控
- 传输性能分析
- 日志记录与分析

**核心文件**：
- `network_speed_test.py`
- `system_monitor.py`
- `analyze_logs.py`

---

### 6. workflow-engine-skill 🆕
**功能**：工作流引擎与自动化编排
- 工作流定义与执行
- 步骤依赖管理
- 条件分支
- 并行执行
- 错误处理与重试

**核心文件**：
- `workflow_runner.py` - 工作流引擎
- `workflows/*.json` - 工作流定义

---

## 工作流列表

| 工作流 | 描述 | 执行时间 |
|--------|------|----------|
| `dual-pc-setup` | 完整集群搭建 | ~15分钟 |
| `file-transfer-only` | 仅文件传输 | 视文件大小 |
| `transfer-with-notify` ⭐ | 带通知的传输 | 视文件大小 |
| `sync-and-config` ⭐ | 同步与配置 | ~20分钟 |
| `monitor-and-optimize` 🆕 | 监控与优化 | ~5分钟 |

---

## 快速开始

### 方式一：使用主控面板 (推荐)

在华为电脑双击运行：
```
\python\一键执行_双电脑集群搭建.bat
```

### 方式二：使用工作流引擎

```bash
# 列出所有工作流
python workflow_runner.py --list

# 执行特定工作流
python workflow_runner.py --workflow transfer-with-notify

# 查看执行状态
python workflow_runner.py --status
```

### 方式三：手动执行

**第一步：在华为电脑（发送端）**
```bash
python high_speed_transfer_v2.py
```

**第二步：在另一台电脑（接收端）**
```bash
python high_speed_receive_v2.py
```

---

## 通知功能使用

### 启动通知服务
```bash
python notification_service.py
```

### 发送自定义通知
```python
from notification_service import NotificationService

notifier = NotificationService("My_PC")
notifier.show_notification("标题", "消息内容")
notifier.play_sound("complete")
```

---

## 网络配置

| 连接 | 华为电脑 | 另一台电脑 | 用途 |
|------|---------|-----------|------|
| 有线 | 192.168.2.3 | 192.168.2.10 | 高速传输 |
| 无线 | 192.168.1.3 | 192.168.1.10 | 备用/控制 |

**端口分配**：
- 50000: 文件传输 (TCP)
- 50001: 通知服务 (UDP)
- 50051: EXo gRPC (TCP)
- 52415: EXo API (TCP)

---

## 目录结构

```
\python\
├── MCP_Skills\
│   ├── README.md                    # 本文件
│   ├── network-transfer-skill\
│   │   └── SKILL.md
│   ├── exo-cluster-skill\
│   │   └── SKILL.md
│   ├── system-config-skill\
│   │   └── SKILL.md
│   ├── notification-skill\          # 🆕
│   │   └── SKILL.md
│   ├── monitoring-skill\            # 🆕
│   │   └── SKILL.md
│   ├── workflow-engine-skill\       # 🆕
│   │   └── SKILL.md
│   └── workflows\
│       ├── dual-pc-setup.json
│       ├── file-transfer-only.json
│       ├── transfer-with-notify.json    # 🆕
│       ├── sync-and-config.json         # 🆕
│       └── monitor-and-optimize.json    # 🆕
├── high_speed_transfer_v2.py        # 🆕 带通知
├── high_speed_receive_v2.py         # 🆕 带通知
├── notification_service.py          # 🆕
├── workflow_runner.py               # 🆕
├── 一键执行_双电脑集群搭建.bat
└── ...
```

---

## 传输速度预期

| 连接方式 | 理论速度 | 实际速度 |
|---------|---------|---------|
| 有线 1Gbps | 125 MB/s | 80-110 MB/s |
| WiFi 5GHz | 100 MB/s | 30-60 MB/s |
| **双网聚合** | **225 MB/s** | **110-170 MB/s** |

---

## 更新日志

### v2.0 (当前版本)
- ✅ 增加通知服务 (notification-skill)
- ✅ 增加工作流引擎 (workflow-engine-skill)
- ✅ 增加监控技能 (monitoring-skill)
- ✅ 传输过程实时通知双方
- ✅ 新增 3 个工作流

### v1.0
- ✅ 基础文件传输
- ✅ EXo 集群配置
- ✅ 系统配置自动化

---

**开始传输吧！使用 `一键执行_双电脑集群搭建.bat` 或工作流引擎！**
