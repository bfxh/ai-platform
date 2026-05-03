#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件自动化升级管理器 - 统一管理所有软件的版本升级

功能特性:
- GitHub仓库版本自动检测
- 支持多种软件类型的版本检测
- 自动下载和安装更新
- 智能版本比较
- 支持升级规则配置
- 备份与回滚机制
- MCP接口支持

支持的升级源:
- GitHub Releases
- 自定义下载链接
- 内置更新检测

使用方式:
    python software_upgrade_manager.py check           # 检查所有软件更新
    python software_upgrade_manager.py upgrade <name>  # 升级指定软件
    python software_upgrade_manager.py list            # 列出所有软件
    python software_upgrade_manager.py mcp             # 启动MCP服务
"""

import json
import sys
import os
import re
import subprocess
import urllib.request
import urllib.error
import zipfile
import tarfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod

# ============================================================
# 配置常量
# ============================================================
AI_PATH = Path("/python")
CONFIG_PATH = AI_PATH / "MCP_Skills"
UPGRADE_DB = CONFIG_PATH / "software_upgrade.db"
CONFIG_FILE = CONFIG_PATH / "upgrade_config.json"
BACKUP_DIR = AI_PATH / "Backup"

# ============================================================
# 数据模型
# ============================================================
@dataclass
class SoftwareInfo:
    """软件信息"""
    name: str
    display_name: str
    current_version: str
    latest_version: str
    upgrade_source: str  # github, url, local
    source_url: str
    install_path: Path
    category: str = "other"
    auto_upgrade: bool = False
    last_check: Optional[str] = None
    upgrade_status: str = "unknown"  # unknown, up_to_date, available, upgrading, error
    
    def needs_upgrade(self) -> bool:
        """检查是否需要升级"""
        if not self.current_version or not self.latest_version:
            return False
        return compare_versions(self.current_version, self.latest_version) < 0

@dataclass
class UpgradeResult:
    """升级结果"""
    success: bool
    software_name: str
    old_version: str
    new_version: str
    message: str
    error: Optional[str] = None
    backup_path: Optional[str] = None

# ============================================================
# 版本比较工具
# ============================================================
def compare_versions(v1: str, v2: str) -> int:
    """
    比较两个版本号
    返回: -1 (v1 < v2), 0 (相等), 1 (v1 > v2)
    
    支持的格式:
    - 标准版本: 1.0.0, 2.1.3
    - 带前缀: v1.0.0, V2.1.3
    - 预发布版本: 1.0-beta, 2.0.0-rc1
    - 稳定后缀: 4.6.2-stable
    """
    # 预发布版本标识符（按优先级排序，越小越优先）
    PRERELEASE_TAGS = {'alpha': 1, 'beta': 2, 'rc': 3, 'pre': 4, 'preview': 5}
    STABLE_TAGS = {'stable': 10, 'final': 10, 'release': 10}
    
    # 移除前缀如 v, V
    v1_clean = re.sub(r'^[vV]', '', v1.strip())
    v2_clean = re.sub(r'^[vV]', '', v2.strip())
    
    # 分割版本号（按 . 和 - 分割）
    parts1 = re.split(r'[.-]', v1_clean)
    parts2 = re.split(r'[.-]', v2_clean)
    
    def parse_part(part: str) -> tuple:
        """解析版本段，返回 (is_numeric, value, is_prerelease)"""
        part_lower = part.lower()
        
        # 检查是否是预发布标签
        if part_lower in PRERELEASE_TAGS:
            return (False, PRERELEASE_TAGS[part_lower], True)
        
        # 检查是否是稳定版本标签
        if part_lower in STABLE_TAGS:
            return (False, STABLE_TAGS[part_lower], False)
        
        # 尝试转换为整数
        try:
            return (True, int(part), False)
        except ValueError:
            # 非数字部分，保持原样比较
            return (False, part, False)
    
    # 解析版本段
    parsed1 = [parse_part(p) for p in parts1]
    parsed2 = [parse_part(p) for p in parts2]
    
    # 逐段比较
    for i, (p1, p2) in enumerate(zip(parsed1, parsed2)):
        is_num1, val1, is_pre1 = p1
        is_num2, val2, is_pre2 = p2
        
        # 数值比较
        if is_num1 and is_num2:
            if val1 < val2:
                return -1
            elif val1 > val2:
                return 1
        else:
            # 非数值比较（标签）
            if val1 < val2:
                return -1
            elif val1 > val2:
                return 1
        
        # 检查预发布版本：预发布版本 < 正式版本
        if is_pre1 and not is_pre2:
            return -1
        elif not is_pre1 and is_pre2:
            return 1
    
    # 处理长度不同的情况
    len1, len2 = len(parsed1), len(parsed2)
    
    # 如果前面的部分都相等，检查剩余部分
    # 规则：
    # 1. 纯数字版本号扩展，如果扩展部分只有零，视为相等（如 2.0 == 2.0.0）
    # 2. 纯数字版本号扩展，如果扩展部分有非零数字，较长的版本更大（如 3.1.4 < 3.1.4.1）
    # 3. 预发布版本 < 正式版本（如 1.0-beta < 1.0）
    # 4. 如果较长版本末尾只有预发布标签，则较短版本更大（如 1.0 > 1.0-beta）
    
    def has_prerelease(parts, start_idx):
        """检查从start_idx开始是否有预发布部分"""
        for p in parts[start_idx:]:
            if p[2]:
                return True
        return False
    
    def all_zeros(parts, start_idx):
        """检查从start_idx开始是否全是零"""
        for p in parts[start_idx:]:
            if p[0] and p[1] != 0:
                return False
            if not p[0] and not p[2]:
                # 非数字且非预发布标签（如 stable）
                return False
        return True
    
    has_pre1 = has_prerelease(parsed1, len2)
    has_pre2 = has_prerelease(parsed2, len1)
    zeros1 = all_zeros(parsed1, len2)
    zeros2 = all_zeros(parsed2, len1)
    
    if len1 < len2:
        # v1更短
        if has_pre2:
            # v2有预发布标签，v1更大（如 1.0 > 1.0-beta）
            return 1
        elif zeros2:
            # v2的扩展部分全是零，视为相等（如 2.0 == 2.0.0）
            return 0
        else:
            # v2是纯数字扩展且有非零数字，v1更小（如 3.1.4 < 3.1.4.1）
            return -1
    elif len1 > len2:
        # v2更短
        if has_pre1:
            # v1有预发布标签，v1更小（如 1.0-beta < 1.0）
            return -1
        elif zeros1:
            # v1的扩展部分全是零，视为相等（如 2.0.0 == 2.0）
            return 0
        else:
            # v1是纯数字扩展且有非零数字，v1更大（如 3.1.4.1 > 3.1.4）
            return 1
    
    return 0

# ============================================================
# 升级源抽象接口
# ============================================================
class UpgradeSource(ABC):
    """升级源抽象基类"""
    
    @abstractmethod
    def get_latest_version(self, source_url: str) -> Optional[str]:
        """获取最新版本号"""
        pass
    
    @abstractmethod
    def download_update(self, source_url: str, version: str, download_dir: Path) -> Optional[Path]:
        """下载更新包"""
        pass

class GitHubSource(UpgradeSource):
    """GitHub Releases升级源"""
    
    def __init__(self):
        self.api_base = "https://api.github.com"
    
    def _parse_repo_url(self, url: str) -> Tuple[str, str]:
        """解析GitHub仓库URL"""
        # 支持多种格式
        patterns = [
            r'https?://github\.com/([^/]+)/([^/]+)/?',
            r'github\.com/([^/]+)/([^/]+)/?',
            r'([^/]+)/([^/]+)'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                return match.group(1), match.group(2)
        return "", ""
    
    def get_latest_version(self, source_url: str) -> Optional[str]:
        """获取GitHub仓库最新Release版本"""
        owner, repo = self._parse_repo_url(source_url)
        if not owner or not repo:
            return None
        
        api_url = f"{self.api_base}/repos/{owner}/{repo}/releases/latest"
        
        try:
            req = urllib.request.Request(api_url, headers={
                'User-Agent': 'SoftwareUpgradeManager/1.0'
            })
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
                return data.get('tag_name')
        except Exception as e:
            print(f"[GitHubSource] 获取版本失败 {source_url}: {e}")
            return None
    
    def download_update(self, source_url: str, version: str, download_dir: Path) -> Optional[Path]:
        """下载GitHub Release包"""
        owner, repo = self._parse_repo_url(source_url)
        if not owner or not repo:
            return None
        
        api_url = f"{self.api_base}/repos/{owner}/{repo}/releases/tags/{version}"
        
        try:
            req = urllib.request.Request(api_url, headers={
                'User-Agent': 'SoftwareUpgradeManager/1.0'
            })
            with urllib.request.urlopen(req, timeout=15) as response:
                release_data = json.loads(response.read().decode())
                
                # 查找合适的下载资产
                assets = release_data.get('assets', [])
                if not assets:
                    # 如果没有资产，检查是否有source code
                    return None
                
                # 优先选择Windows版本
                asset = None
                for a in assets:
                    name = a['name'].lower()
                    if ('windows' in name or 'win' in name) and \
                       (a['name'].endswith('.zip') or a['name'].endswith('.exe')):
                        asset = a
                        break
                
                # 如果没有Windows版本，选择第一个zip或exe
                if not asset:
                    for a in assets:
                        if a['name'].endswith('.zip') or a['name'].endswith('.exe'):
                            asset = a
                            break
                
                if not asset:
                    return None
                
                download_url = asset['browser_download_url']
                filename = asset['name']
                save_path = download_dir / filename
                
                print(f"[GitHubSource] 下载: {download_url}")
                
                # 下载文件
                req = urllib.request.Request(download_url, headers={
                    'User-Agent': 'SoftwareUpgradeManager/1.0'
                })
                with urllib.request.urlopen(req, timeout=60) as resp, \
                     open(save_path, 'wb') as f:
                    shutil.copyfileobj(resp, f)
                
                return save_path
                
        except Exception as e:
            print(f"[GitHubSource] 下载失败 {source_url}: {e}")
            return None

class URLSource(UpgradeSource):
    """自定义URL升级源"""
    
    def get_latest_version(self, source_url: str) -> Optional[str]:
        """从URL获取版本（需要在URL中包含版本信息）"""
        # 尝试从URL中提取版本号
        # 支持格式: http://example.com/app_v1.2.3.zip
        match = re.search(r'v?(\d+\.\d+\.?\d*)', source_url)
        if match:
            return match.group(1)
        return None
    
    def download_update(self, source_url: str, version: str, download_dir: Path) -> Optional[Path]:
        """下载指定URL的文件"""
        try:
            filename = source_url.split('/')[-1]
            save_path = download_dir / filename
            
            print(f"[URLSource] 下载: {source_url}")
            
            req = urllib.request.Request(source_url, headers={
                'User-Agent': 'SoftwareUpgradeManager/1.0'
            })
            with urllib.request.urlopen(req, timeout=60) as resp, \
                 open(save_path, 'wb') as f:
                shutil.copyfileobj(resp, f)
            
            return save_path
        except Exception as e:
            print(f"[URLSource] 下载失败 {source_url}: {e}")
            return None

# ============================================================
# 安装器接口
# ============================================================
class Installer(ABC):
    """安装器抽象基类"""
    
    @abstractmethod
    def install(self, package_path: Path, install_dir: Path) -> bool:
        """安装软件"""
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        pass

class ZipInstaller(Installer):
    """ZIP包安装器"""
    
    def install(self, package_path: Path, install_dir: Path) -> bool:
        """解压ZIP包到安装目录"""
        try:
            with zipfile.ZipFile(package_path, 'r') as zip_ref:
                # 获取根目录
                root_dirs = set()
                for name in zip_ref.namelist():
                    parts = name.split('/')
                    if parts and parts[0]:
                        root_dirs.add(parts[0])
                
                if len(root_dirs) == 1:
                    # 解压整个目录
                    zip_ref.extractall(install_dir.parent)
                else:
                    # 创建子目录并解压
                    install_dir.mkdir(parents=True, exist_ok=True)
                    zip_ref.extractall(install_dir)
                
                print(f"[ZipInstaller] 已解压到: {install_dir}")
                return True
        except Exception as e:
            print(f"[ZipInstaller] 解压失败: {e}")
            return False
    
    def get_supported_extensions(self) -> List[str]:
        return ['.zip']

class ExeInstaller(Installer):
    """EXE安装器"""
    
    def install(self, package_path: Path, install_dir: Path) -> bool:
        """静默安装EXE"""
        try:
            # 构建静默安装命令
            cmd = [str(package_path), '/S', '/VERYSILENT', '/NORESTART']
            
            print(f"[ExeInstaller] 执行安装: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"[ExeInstaller] 安装成功")
                return True
            else:
                print(f"[ExeInstaller] 安装失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"[ExeInstaller] 安装失败: {e}")
            return False
    
    def get_supported_extensions(self) -> List[str]:
        return ['.exe']

class TarInstaller(Installer):
    """TAR包安装器"""
    
    def install(self, package_path: Path, install_dir: Path) -> bool:
        """解压TAR包"""
        try:
            with tarfile.open(package_path, 'r:*') as tar_ref:
                tar_ref.extractall(install_dir.parent)
            print(f"[TarInstaller] 已解压到: {install_dir}")
            return True
        except Exception as e:
            print(f"[TarInstaller] 解压失败: {e}")
            return False
    
    def get_supported_extensions(self) -> List[str]:
        return ['.tar', '.tar.gz', '.tgz']

# ============================================================
# 软件升级管理器核心
# ============================================================
class SoftwareUpgradeManager:
    """软件升级管理器"""
    
    def __init__(self):
        self._sources: Dict[str, UpgradeSource] = {
            'github': GitHubSource(),
            'url': URLSource()
        }
        
        self._installers: List[Installer] = [
            ZipInstaller(),
            ExeInstaller(),
            TarInstaller()
        ]
        
        self._software_list: Dict[str, SoftwareInfo] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        CONFIG_PATH.mkdir(parents=True, exist_ok=True)
        
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                for name, data in config.get('software', {}).items():
                    self._software_list[name] = SoftwareInfo(
                        name=name,
                        display_name=data.get('display_name', name),
                        current_version=data.get('current_version', ''),
                        latest_version=data.get('latest_version', ''),
                        upgrade_source=data.get('upgrade_source', 'github'),
                        source_url=data.get('source_url', ''),
                        install_path=Path(data.get('install_path', '')),
                        category=data.get('category', 'other'),
                        auto_upgrade=data.get('auto_upgrade', False),
                        last_check=data.get('last_check'),
                        upgrade_status=data.get('upgrade_status', 'unknown')
                    )
            except Exception as e:
                print(f"[UpgradeManager] 加载配置失败: {e}")
    
    def _save_config(self):
        """保存配置文件"""
        config = {
            'software': {
                name: {
                    'display_name': info.display_name,
                    'current_version': info.current_version,
                    'latest_version': info.latest_version,
                    'upgrade_source': info.upgrade_source,
                    'source_url': info.source_url,
                    'install_path': str(info.install_path),
                    'category': info.category,
                    'auto_upgrade': info.auto_upgrade,
                    'last_check': info.last_check,
                    'upgrade_status': info.upgrade_status
                }
                for name, info in self._software_list.items()
            }
        }
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def add_software(self, info: SoftwareInfo):
        """添加软件到管理列表"""
        self._software_list[info.name] = info
        self._save_config()
    
    def remove_software(self, name: str):
        """从管理列表移除软件"""
        if name in self._software_list:
            del self._software_list[name]
            self._save_config()
    
    def get_software(self, name: str) -> Optional[SoftwareInfo]:
        """获取软件信息"""
        return self._software_list.get(name)
    
    def list_software(self) -> List[SoftwareInfo]:
        """列出所有管理的软件"""
        return list(self._software_list.values())
    
    def check_updates(self, software_name: str = None) -> List[SoftwareInfo]:
        """检查软件更新"""
        if software_name:
            targets = [self._software_list.get(software_name)]
        else:
            targets = list(self._software_list.values())
        
        results = []
        for software in targets:
            if not software:
                continue
            
            print(f"[UpgradeManager] 检查更新: {software.display_name}")
            
            source = self._sources.get(software.upgrade_source)
            if not source:
                software.upgrade_status = "error"
                continue
            
            latest_version = source.get_latest_version(software.source_url)
            if latest_version:
                software.latest_version = latest_version
                software.last_check = datetime.now().isoformat()
                
                if software.needs_upgrade():
                    software.upgrade_status = "available"
                else:
                    software.upgrade_status = "up_to_date"
            else:
                software.upgrade_status = "error"
            
            results.append(software)
        
        self._save_config()
        return results
    
    def _create_backup(self, install_path: Path) -> Optional[Path]:
        """创建软件备份"""
        if not install_path.exists():
            return None
        
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_name = f"{install_path.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            if install_path.is_file():
                backup_path = BACKUP_DIR / install_path.name
                shutil.copy(install_path, backup_path)
            else:
                backup_path = BACKUP_DIR / backup_name
                shutil.copytree(install_path, backup_path)
            
            print(f"[UpgradeManager] 已备份到: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"[UpgradeManager] 备份失败: {e}")
            return None
    
    def upgrade_software(self, name: str) -> UpgradeResult:
        """升级指定软件"""
        software = self._software_list.get(name)
        if not software:
            return UpgradeResult(
                success=False,
                software_name=name,
                old_version="",
                new_version="",
                message="软件不存在",
                error="软件未在管理列表中"
            )
        
        # 先检查更新
        self.check_updates(name)
        
        if not software.needs_upgrade():
            return UpgradeResult(
                success=True,
                software_name=software.display_name,
                old_version=software.current_version,
                new_version=software.latest_version,
                message="当前已是最新版本"
            )
        
        print(f"[UpgradeManager] 开始升级: {software.display_name}")
        software.upgrade_status = "upgrading"
        self._save_config()
        
        # 创建临时下载目录
        temp_dir = AI_PATH / "Temp" / "upgrade"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建备份
        backup_path = self._create_backup(software.install_path)
        
        try:
            # 获取升级源
            source = self._sources.get(software.upgrade_source)
            if not source:
                return UpgradeResult(
                    success=False,
                    software_name=software.display_name,
                    old_version=software.current_version,
                    new_version=software.latest_version,
                    message="不支持的升级源",
                    error=f"未知升级源: {software.upgrade_source}"
                )
            
            # 下载更新包
            package_path = source.download_update(
                software.source_url,
                software.latest_version,
                temp_dir
            )
            
            if not package_path:
                software.upgrade_status = "error"
                self._save_config()
                return UpgradeResult(
                    success=False,
                    software_name=software.display_name,
                    old_version=software.current_version,
                    new_version=software.latest_version,
                    message="下载失败",
                    error="无法下载更新包"
                )
            
            # 选择安装器
            installer = None
            ext = package_path.suffix.lower()
            for inst in self._installers:
                if ext in inst.get_supported_extensions():
                    installer = inst
                    break
            
            if not installer:
                software.upgrade_status = "error"
                self._save_config()
                return UpgradeResult(
                    success=False,
                    software_name=software.display_name,
                    old_version=software.current_version,
                    new_version=software.latest_version,
                    message="无法安装",
                    error=f"不支持的文件格式: {ext}"
                )
            
            # 执行安装
            success = installer.install(package_path, software.install_path)
            
            if success:
                software.current_version = software.latest_version
                software.upgrade_status = "up_to_date"
                self._save_config()
                
                # 清理临时文件
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                return UpgradeResult(
                    success=True,
                    software_name=software.display_name,
                    old_version=software.current_version,
                    new_version=software.latest_version,
                    message="升级成功",
                    backup_path=str(backup_path) if backup_path else None
                )
            else:
                # 尝试回滚
                if backup_path:
                    self._restore_from_backup(backup_path, software.install_path)
                
                software.upgrade_status = "error"
                self._save_config()
                
                return UpgradeResult(
                    success=False,
                    software_name=software.display_name,
                    old_version=software.current_version,
                    new_version=software.latest_version,
                    message="安装失败",
                    error="安装过程出错"
                )
        
        except Exception as e:
            # 尝试回滚
            if backup_path:
                self._restore_from_backup(backup_path, software.install_path)
            
            software.upgrade_status = "error"
            self._save_config()
            
            return UpgradeResult(
                success=False,
                software_name=software.display_name,
                old_version=software.current_version,
                new_version=software.latest_version,
                message="升级失败",
                error=str(e)
            )
    
    def _restore_from_backup(self, backup_path: Path, install_path: Path):
        """从备份恢复"""
        try:
            if install_path.exists():
                if install_path.is_file():
                    install_path.unlink()
                else:
                    shutil.rmtree(install_path)
            
            if backup_path.is_file():
                shutil.copy(backup_path, install_path)
            else:
                shutil.copytree(backup_path, install_path)
            
            print(f"[UpgradeManager] 已从备份恢复: {install_path}")
        except Exception as e:
            print(f"[UpgradeManager] 恢复失败: {e}")
    
    def auto_upgrade_all(self) -> List[UpgradeResult]:
        """自动升级所有启用自动升级的软件"""
        results = []
        
        for software in self._software_list.values():
            if software.auto_upgrade:
                result = self.upgrade_software(software.name)
                results.append(result)
        
        return results
    
    def get_upgrade_summary(self) -> Dict[str, Any]:
        """获取升级摘要"""
        total = len(self._software_list)
        up_to_date = sum(1 for s in self._software_list.values() if s.upgrade_status == "up_to_date")
        available = sum(1 for s in self._software_list.values() if s.upgrade_status == "available")
        upgrading = sum(1 for s in self._software_list.values() if s.upgrade_status == "upgrading")
        error = sum(1 for s in self._software_list.values() if s.upgrade_status == "error")
        
        return {
            'total': total,
            'up_to_date': up_to_date,
            'available': available,
            'upgrading': upgrading,
            'error': error,
            'software': [
                {
                    'name': s.name,
                    'display_name': s.display_name,
                    'current_version': s.current_version,
                    'latest_version': s.latest_version,
                    'status': s.upgrade_status,
                    'auto_upgrade': s.auto_upgrade
                }
                for s in self._software_list.values()
            ]
        }

# ============================================================
# MCP接口
# ============================================================
class MCPInterface:
    """MCP接口"""
    
    def __init__(self):
        self.manager = SoftwareUpgradeManager()
    
    def handle(self, request: Dict) -> Dict:
        """处理MCP请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        try:
            if action == "check_updates":
                software_name = params.get("name")
                results = self.manager.check_updates(software_name)
                
                return {
                    "success": True,
                    "results": [
                        {
                            "name": s.name,
                            "display_name": s.display_name,
                            "current_version": s.current_version,
                            "latest_version": s.latest_version,
                            "upgrade_status": s.upgrade_status,
                            "needs_upgrade": s.needs_upgrade()
                        }
                        for s in results
                    ]
                }
            
            elif action == "upgrade":
                name = params.get("name")
                result = self.manager.upgrade_software(name)
                
                return {
                    "success": result.success,
                    "software_name": result.software_name,
                    "old_version": result.old_version,
                    "new_version": result.new_version,
                    "message": result.message,
                    "error": result.error,
                    "backup_path": result.backup_path
                }
            
            elif action == "list":
                software_list = self.manager.list_software()
                
                return {
                    "success": True,
                    "count": len(software_list),
                    "software": [
                        {
                            "name": s.name,
                            "display_name": s.display_name,
                            "current_version": s.current_version,
                            "latest_version": s.latest_version,
                            "upgrade_source": s.upgrade_source,
                            "source_url": s.source_url,
                            "install_path": str(s.install_path),
                            "category": s.category,
                            "auto_upgrade": s.auto_upgrade,
                            "upgrade_status": s.upgrade_status
                        }
                        for s in software_list
                    ]
                }
            
            elif action == "add":
                software_info = SoftwareInfo(
                    name=params.get("name", ""),
                    display_name=params.get("display_name", ""),
                    current_version=params.get("current_version", ""),
                    latest_version="",
                    upgrade_source=params.get("upgrade_source", "github"),
                    source_url=params.get("source_url", ""),
                    install_path=Path(params.get("install_path", "")),
                    category=params.get("category", "other"),
                    auto_upgrade=params.get("auto_upgrade", False)
                )
                
                self.manager.add_software(software_info)
                
                return {"success": True, "message": "软件添加成功"}
            
            elif action == "remove":
                name = params.get("name")
                self.manager.remove_software(name)
                
                return {"success": True, "message": "软件已移除"}
            
            elif action == "summary":
                summary = self.manager.get_upgrade_summary()
                
                return {"success": True, "summary": summary}
            
            elif action == "auto_upgrade_all":
                results = self.manager.auto_upgrade_all()
                
                return {
                    "success": True,
                    "results": [
                        {
                            "success": r.success,
                            "software_name": r.software_name,
                            "old_version": r.old_version,
                            "new_version": r.new_version,
                            "message": r.message,
                            "error": r.error
                        }
                        for r in results
                    ]
                }
            
            else:
                return {"success": False, "error": f"未知操作: {action}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}

# ============================================================
# 命令行接口
# ============================================================
def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    manager = SoftwareUpgradeManager()
    
    if cmd == "check":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        results = manager.check_updates(name)
        
        print(f"\n=== 更新检查结果 ===")
        for s in results:
            status_icon = {
                "up_to_date": "✓",
                "available": "⟳",
                "upgrading": "⚡",
                "error": "✗",
                "unknown": "?"
            }.get(s.upgrade_status, "?")
            
            print(f"\n{status_icon} {s.display_name}")
            print(f"  当前版本: {s.current_version}")
            print(f"  最新版本: {s.latest_version}")
            print(f"  状态: {s.upgrade_status}")
            print(f"  源: {s.upgrade_source}")
    
    elif cmd == "upgrade":
        if len(sys.argv) < 3:
            print("用法: software_upgrade_manager.py upgrade <name>")
            return
        
        name = sys.argv[2]
        result = manager.upgrade_software(name)
        
        if result.success:
            print(f"\n✓ 升级成功")
            print(f"  软件: {result.software_name}")
            print(f"  版本: {result.old_version} → {result.new_version}")
            print(f"  消息: {result.message}")
            if result.backup_path:
                print(f"  备份: {result.backup_path}")
        else:
            print(f"\n✗ 升级失败")
            print(f"  软件: {result.software_name}")
            print(f"  消息: {result.message}")
            if result.error:
                print(f"  错误: {result.error}")
    
    elif cmd == "list":
        software_list = manager.list_software()
        
        print(f"\n=== 软件列表 ({len(software_list)} 个) ===")
        print(f"{'名称':<20} {'当前版本':<15} {'最新版本':<15} {'状态':<12} {'自动升级'}")
        print("-" * 80)
        
        for s in software_list:
            auto_icon = "✓" if s.auto_upgrade else ""
            print(f"{s.display_name:<20} {s.current_version:<15} {s.latest_version:<15} {s.upgrade_status:<12} {auto_icon}")
    
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("用法: software_upgrade_manager.py add <name> <display_name> <source_url> <install_path> [category]")
            return
        
        name = sys.argv[2]
        display_name = sys.argv[3]
        source_url = sys.argv[4]
        install_path = sys.argv[5]
        category = sys.argv[6] if len(sys.argv) > 6 else "other"
        
        # 检测升级源类型
        if 'github.com' in source_url.lower():
            upgrade_source = 'github'
        else:
            upgrade_source = 'url'
        
        software_info = SoftwareInfo(
            name=name,
            display_name=display_name,
            current_version="",
            latest_version="",
            upgrade_source=upgrade_source,
            source_url=source_url,
            install_path=Path(install_path),
            category=category,
            auto_upgrade=False
        )
        
        manager.add_software(software_info)
        print(f"✓ 已添加软件: {display_name}")
    
    elif cmd == "remove":
        if len(sys.argv) < 3:
            print("用法: software_upgrade_manager.py remove <name>")
            return
        
        name = sys.argv[2]
        manager.remove_software(name)
        print(f"✓ 已移除软件: {name}")
    
    elif cmd == "summary":
        summary = manager.get_upgrade_summary()
        
        print(f"\n=== 升级摘要 ===")
        print(f"总软件数: {summary['total']}")
        print(f"  ✓ 已是最新: {summary['up_to_date']}")
        print(f"  ⟳ 有更新: {summary['available']}")
        print(f"  ⚡ 升级中: {summary['upgrading']}")
        print(f"  ✗ 错误: {summary['error']}")
    
    elif cmd == "auto_upgrade":
        results = manager.auto_upgrade_all()
        
        print(f"\n=== 自动升级结果 ===")
        for result in results:
            if result.success:
                print(f"✓ {result.software_name}: {result.old_version} → {result.new_version}")
            else:
                print(f"✗ {result.software_name}: {result.message}")
    
    elif cmd == "mcp":
        print("软件升级管理器 MCP 服务器已启动")
        print("支持操作: check_updates, upgrade, list, add, remove, summary, auto_upgrade_all")
        
        mcp = MCPInterface()
        
        import select
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line)
                    response = mcp.handle(request)
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print(json.dumps({"success": False, "error": "无效的JSON"}))
                    sys.stdout.flush()
    
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
