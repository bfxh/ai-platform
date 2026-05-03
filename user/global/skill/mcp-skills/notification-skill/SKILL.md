# Notification Skill

跨设备通知与状态同步技能

## 功能

- Windows 桌面通知
- 声音提示
- 跨设备状态同步
- 传输进度实时通知
- 错误告警

## 通知类型

### transfer_start
传输开始通知
```json
{
  "type": "transfer_start",
  "from": "Huawei_PC",
  "data": {
    "file_count": 100
  }
}
```

### transfer_progress
传输进度通知
```json
{
  "type": "transfer_progress",
  "data": {
    "progress": 50,
    "current_file": "path/to/file.txt"
  }
}
```

### transfer_complete
传输完成通知
```json
{
  "type": "transfer_complete",
  "data": {
    "success": 98,
    "failed": 2,
    "total_bytes": 1073741824
  }
}
```

### config_complete
配置完成通知
```json
{
  "type": "config_complete",
  "data": {
    "node_name": "node_2"
  }
}
```

### exo_started
EXo 启动通知
```json
{
  "type": "exo_started",
  "data": {
    "port": 50051,
    "models": ["llama-3.1-8b"]
  }
}
```

### error
错误通知
```json
{
  "type": "error",
  "data": {
    "message": "连接超时"
  }
}
```

## 使用方式

### 发送通知
```python
from notification_service import NotificationService

notifier = NotificationService("Node_Name")
notifier.send_notification("192.168.1.10", "transfer_start", {"file_count": 100})
```

### 接收通知
```python
notifier = NotificationService("Node_Name")
notifier.start_listener()  # 阻塞监听
```

### 显示本地通知
```python
notifier.show_notification("标题", "消息内容")
notifier.play_sound("complete")  # complete/error/alert
```

## 端口

- 通知端口: 50001 (UDP)
- 传输端口: 50000 (TCP)

## 依赖

- Python 3.8+
- win10toast (可选，用于 Windows 通知)
