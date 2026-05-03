# Network Transfer Skill

高速局域网文件传输与设备发现技能

## 功能

- 自动发现局域网设备
- 多线程高速传输
- 双网卡负载均衡
- 断点续传
- 传输进度显示

## 使用场景

1. 两台电脑间快速传输大文件
2. 批量文件同步
3. 跨设备工作流配置

## 核心命令

### 扫描网络设备
```bash
scan_network.bat
```

### 启动高速传输（发送端）
```bash
start_high_speed_send.bat
```

### 启动接收服务（接收端）
```bash
start_high_speed_receive.bat
```

### 配置目标电脑
```bash
python configure_target.py
```

## 网络配置

- 有线网络：192.168.2.x/24
- 无线网络：192.168.1.x/24
- 传输端口：50000
- 协议：TCP

## 依赖

- Python 3.8+
- Windows 10/11
- 有线或无线网络
