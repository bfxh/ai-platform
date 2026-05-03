# 网络突破下载系统 (network_bypass)

突破各种网络限制，支持 GitHub 多镜像、pip/npm 镜像自动切换。

## 原理

### GitHub 下载多层策略
1. 直连 `https://github.com/` — 优先尝试，速度最快
2. `ghproxy.cn` — 国内镜像，覆盖率最高
3. `gitclone.com` — GitClone 镜像
4. `ghdl.feishu.cn` — 飞书镜像
5. `mirror.ghproxy.com` — 备用代理

### jsDelivr CDN 转换
将 GitHub raw URL 自动转为 CDN URL：
```
https://raw.githubusercontent.com/user/repo/branch/file
  → https://cdn.jsdelivr.net/gh/user/repo@branch/file
  → https://cdn.statically.io/gh/user/repo/branch/file
```

## 命令

```bash
# 探测 GitHub 各策略可用性
python skill.py probe-github [owner] [repo]

# 克隆仓库（自动尝试所有策略）
python skill.py clone <repo_url> [--dest <path>] [--depth 1] [--branch <name>]

# 分析仓库（默认分支 + 所有分支 + 最新提交）
python skill.py analyze <repo_url>

# 下载单个文件（自动多策略）
python skill.py download <url> [--dest <path>]

# pip 安装（自动镜像）
python skill.py pip <package> [--mirror tuna|ali|netease|tencent]

# npm 安装（自动镜像）
python skill.py npm <package> [--mirror taobao|npm]
```

## 使用场景

- GitHub 仓库下载慢/超时 → 自动切换镜像
- pip install 超时 → 自动换清华/阿里源
- 只想分析仓库结构不下载 → `analyze` 命令查看分支
- 下载单个文件（SKILL.md）→ `download` 命令
