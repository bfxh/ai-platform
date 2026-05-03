# Monitoring Skill

系统监控与性能分析技能

## 功能

- 网络速度测试
- 系统资源监控
- 传输性能分析
- 日志记录与分析
- 实时状态看板

## 核心命令

### 网络速度测试
```bash
python network_speed_test.py --target 192.168.1.10
```

### 系统资源监控
```bash
python system_monitor.py --interval 5
```

### 传输日志分析
```bash
python analyze_logs.py --log \python\transfer.log
```

## 监控指标

### 网络指标
- 延迟 (Ping)
- 带宽 (Speedtest)
- 丢包率
- 连接稳定性

### 系统指标
- CPU 使用率
- 内存使用率
- 磁盘 I/O
- 网络 I/O

### 传输指标
- 传输速度 (MB/s)
- 文件成功率
- 平均文件大小
- 传输耗时

## 使用场景

1. 传输前网络质量检测
2. 传输中性能监控
3. 传输后数据分析
4. 长期性能趋势分析

## 输出示例

```
网络状态:
  延迟: 2ms ✓
  带宽: 945 Mbps ✓
  丢包: 0% ✓

系统状态:
  CPU: 15%
  内存: 45%
  磁盘: 120 MB/s 读取

传输性能:
  速度: 85 MB/s
  进度: 67%
  预计剩余: 3分20秒
```
