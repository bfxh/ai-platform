---
name: "trai-network-bypass"
description: "网络限制突破工具。检测并修复hosts文件中的网络限制，自动配置代理，确保GitHub等外部服务可访问。Invoke when network issues occur, GitHub API fails, or external services are unreachable."
---

# 网络限制突破工具

## 检测机制

### 1. Hosts 文件检测
```python
def detect_hosts_restrictions():
    """检测 hosts 文件中的网络限制"""
    hosts_path = Path("C:/Windows/System32/drivers/etc/hosts")
    
    if not hosts_path.exists():
        return {'restricted': False, 'reason': 'hosts文件不存在'}
    
    content = hosts_path.read_text(encoding='utf-8')
    
    # 检测常见的限制模式
    restricted_domains = []
    github_domains = [
        'github.com', 'api.github.com', 'github.dev',
        'raw.githubusercontent.com', 'avatars.githubusercontent.com'
    ]
    
    for domain in github_domains:
        if f'127.0.0.1 {domain}' in content or f'127.0.0.1	{domain}' in content:
            restricted_domains.append(domain)
    
    return {
        'restricted': len(restricted_domains) > 0,
        'domains': restricted_domains,
        'severity': 'high' if len(restricted_domains) > 5 else 'medium'
    }
```

### 2. 网络连通性测试
```python
def test_network_connectivity():
    """测试网络连通性"""
    import subprocess
    
    tests = {
        'github_api': False,
        'google': False,
        'dns_resolution': False
    }
    
    # 测试 GitHub API
    try:
        result = subprocess.run(
            ['ping', '-n', '1', 'api.github.com'],
            capture_output=True,
            text=True,
            timeout=5
        )
        tests['github_api'] = result.returncode == 0
    except:
        pass
    
    # 测试 DNS 解析
    try:
        result = subprocess.run(
            ['nslookup', 'github.com'],
            capture_output=True,
            text=True,
            timeout=5
        )
        tests['dns_resolution'] = '127.0.0.1' not in result.stdout
    except:
        pass
    
    return tests
```

## 修复机制

### 1. Hosts 文件清理
```python
def clean_hosts_file():
    """清理 hosts 文件中的限制条目"""
    hosts_path = Path("C:/Windows/System32/drivers/etc/hosts")
    backup_path = Path("C:/Windows/System32/drivers/etc/hosts.bak")
    
    # 备份
    if hosts_path.exists():
        import shutil
        shutil.copy2(hosts_path, backup_path)
    
    content = hosts_path.read_text(encoding='utf-8')
    
    # 移除 Steam++ 等工具添加的限制
    import re
    
    # 移除 Steam++ 区块
    content = re.sub(
        r'# Steam\+\+ Start.*?# Steam\+\+ End',
        '',
        content,
        flags=re.DOTALL
    )
    
    # 移除 GitHub 相关的 127.0.0.1 条目
    github_domains = [
        'github.com', 'api.github.com', 'github.dev',
        'github.githubassets.com', 'education.github.com',
        'raw.github.com', 'githubusercontent.com',
        'raw.githubusercontent.com', 'camo.githubusercontent.com',
        'cloud.githubusercontent.com', 'avatars.githubusercontent.com',
        'user-images.githubusercontent.com', 'objects.githubusercontent.com'
    ]
    
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        should_keep = True
        if '127.0.0.1' in line or '0.0.0.0' in line:
            for domain in github_domains:
                if domain in line:
                    should_keep = False
                    break
        if should_keep:
            cleaned_lines.append(line)
    
    # 清理多余空行
    content = '\n'.join(cleaned_lines)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    hosts_path.write_text(content, encoding='utf-8')
    
    # 刷新 DNS
    subprocess.run(['ipconfig', '/flushdns'], capture_output=True)
    
    return {'success': True, 'backup': str(backup_path)}
```

### 2. 代理配置
```python
def configure_proxy():
    """配置系统代理"""
    # 检测常见代理工具
    proxy_tools = [
        "C:/Program Files/Clash for Windows/Clash for Windows.exe",
        "C:/Program Files/v2rayN/v2rayN.exe",
        "C:/Program Files/Shadowsocks/Shadowsocks.exe"
    ]
    
    for tool in proxy_tools:
        if Path(tool).exists():
            return {
                'proxy_available': True,
                'tool': tool,
                'suggestion': '请手动启动代理工具'
            }
    
    return {
        'proxy_available': False,
        'suggestion': '未检测到代理工具，建议安装 Clash 或 v2rayN'
    }
```

## 自动修复流程

```python
def auto_fix_network():
    """自动修复网络问题"""
    results = {
        'hosts_cleaned': False,
        'dns_flushed': False,
        'proxy_configured': False
    }
    
    # 1. 检测限制
    restriction = detect_hosts_restrictions()
    
    if restriction['restricted']:
        # 2. 清理 hosts
        clean_result = clean_hosts_file()
        results['hosts_cleaned'] = clean_result['success']
        
        # 3. 刷新 DNS
        import subprocess
        subprocess.run(['ipconfig', '/flushdns'], capture_output=True)
        results['dns_flushed'] = True
    
    # 4. 检查代理
    proxy = configure_proxy()
    results['proxy_configured'] = proxy['proxy_available']
    
    # 5. 验证修复
    connectivity = test_network_connectivity()
    results['connectivity'] = connectivity
    
    return results
```

## 监控机制

### 定期检测
```python
def monitor_network():
    """定期监控网络状态"""
    restriction = detect_hosts_restrictions()
    connectivity = test_network_connectivity()
    
    status = {
        'restricted': restriction['restricted'],
        'github_accessible': connectivity['github_api'],
        'dns_clean': connectivity['dns_resolution'],
        'timestamp': datetime.now().isoformat()
    }
    
    # 如果检测到限制，自动修复
    if restriction['restricted']:
        auto_fix_network()
        status['auto_fixed'] = True
    
    return status
```