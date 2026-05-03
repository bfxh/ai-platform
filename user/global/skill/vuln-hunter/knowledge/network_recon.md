# 网络侦察方法论

## 阶段 1: 主机发现

### Nmap 命令
```bash
# Ping 扫描 (快速)
nmap -sn 192.168.1.0/24

# ARP 扫描 (局域网最可靠)
nmap -PR -sn 192.168.1.0/24

# TCP SYN Ping
nmap -PS22,80,443,3389 192.168.1.0/24
```

### 分析要点
- 存活主机 IP 列表
- MAC 地址 → 厂商识别 (前3字节)
- 响应时间 → 大致的网络拓扑距离

---

## 阶段 2: 端口扫描

### Nmap 命令
```bash
# 快速 1000 端口
nmap -T4 -F 192.168.1.100

# 全端口
nmap -T4 -p- 192.168.1.100

# 服务版本检测
nmap -sV -p 22,80,443,3306,8080 192.168.1.100
```

### 关键端口关注
| 端口 | 服务 | 攻击面 |
|------|------|--------|
| 21 | FTP | 匿名登录、明文传输 |
| 22 | SSH | 弱密码、老旧版本 |
| 23 | Telnet | 明文传输 |
| 25 | SMTP | 邮件伪造 |
| 53 | DNS | 区域传输 |
| 80/443 | HTTP/S | Web 应用漏洞 |
| 445 | SMB | EternalBlue 等 |
| 1433 | MSSQL | 弱密码 |
| 1521 | Oracle | 弱密码 |
| 27017 | MongoDB | 无认证访问 |
| 3306 | MySQL | 弱密码 |
| 3389 | RDP | BlueKeep |
| 5432 | PostgreSQL | 弱密码 |
| 6379 | Redis | 无认证访问 |
| 8080 | HTTP-Alt | Web 应用 |
| 9200 | Elasticsearch | 数据泄露 |

---

## 阶段 3: OS 检测

### Nmap 命令
```bash
nmap -O 192.168.1.100
nmap -O --osscan-guess 192.168.1.100  # 激进模式
```

### 分析
- TTL 值推判: Windows=128, Linux=64, 网络设备=255
- TCP 窗口大小
- TCP 选项顺序

---

## 阶段 4: 漏洞扫描

### 工具
```bash
# Nmap NSE 脚本
nmap --script vuln 192.168.1.100
nmap --script "smb-vuln*" 192.168.1.100

# 知名漏洞扫描
nmap --script http-sql-injection -p 80 192.168.1.100
nmap --script ssl-heartbleed -p 443 192.168.1.100
```

---

## 阶段 5: Web 应用指纹

```bash
# 技术栈检测
whatweb https://target.com

# WAF 检测
wafw00f https://target.com

# 目录扫描
dirb https://target.com
gobuster dir -u https://target.com -w /usr/share/wordlists/dirb/common.txt
```

---

## 阶段 6: 报告要点

对于发现的每个服务, 记录:
1. **IP:端口** — 服务名 + 版本
2. **Banner** — 原始 banner 信息
3. **已知漏洞** — CVE 编号 + CVSS 评分
4. **攻击向量** — 可行的攻击路径
5. **修复建议** — 升级/配置/禁用
