# System Config Skill

Windows 系统自动化配置技能

## 功能

- 防火墙规则配置
- 网络共享设置
- 服务管理
- 环境变量配置
- 软件安装自动化

## 核心命令

### 配置防火墙
```powershell
netsh advfirewall firewall add rule name="RuleName" dir=in action=allow protocol=tcp localport=50051
```

### 启用网络发现
```powershell
netsh advfirewall firewall set rule group="网络发现" new enable=Yes
netsh advfirewall firewall set rule group="文件和打印机共享" new enable=Yes
```

### 创建共享文件夹
```cmd
net share ShareName=D:\Folder /grant:Everyone,FULL
```

### 配置静态 IP
```powershell
New-NetIPAddress -InterfaceAlias "以太网" -IPAddress 192.168.2.10 -PrefixLength 24
```

## 配置模板

### EXo 集群节点
```json
{
  "firewall": {
    "ports": ["50051", "8080", "52415", "50000"],
    "protocol": "TCP"
  },
  "shares": [
    {"name": "AI", "path": "/python"}
  ],
  "services": ["fdrespub", "fdhost"]
}
```

## 自动化脚本

- `configure_firewall.bat` - 防火墙配置
- `setup_shares.bat` - 共享设置
- `optimize_network.bat` - 网络优化
- `install_dependencies.bat` - 依赖安装

## 使用场景

1. 新电脑初始化配置
2. 集群节点标准化
3. 网络环境快速搭建
4. 安全策略批量应用
