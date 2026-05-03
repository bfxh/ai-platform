#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSTACK 徽章管理器

功能:
- 为缓存文件添加元数据标记
- 支持文件验证状态跟踪
- 提供徽章查询和管理功能

用法:
    python badge_manager.py add <file> <status> [source]  # 添加徽章
    python badge_manager.py check <file>                # 检查徽章
    python badge_manager.py verify <dir>                # 验证目录文件
    python badge_manager.py list <dir>                 # 列出徽章
"""

import os
import sys
import json
from pathlib import Path
import logging

# 配置
AI_DIR = Path("/python").resolve()
LOG_FILE = AI_DIR / "logs" / "badge_manager.log"

# 确保日志目录存在
(LOG_FILE.parent).mkdir(parents=True, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE)),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GSTACKBadge")


class BadgeManager:
    """GSTACK 徽章管理器"""
    
    def __init__(self):
        self.ai_dir = AI_DIR
        
    def _get_meta_file(self, file_path):
        """获取元数据文件路径"""
        return Path(str(file_path) + ".gstack.meta")
    
    def add_badge(self, file_path, status, source=None):
        """添加徽章"""
        try:
            file = Path(file_path)
            if not file.exists():
                logger.error(f"文件不存在: {file_path}")
                return False
            
            logger.info(f"为文件添加徽章: {file.name}")
            
            # 创建元数据
            meta = {
                "status": status,
                "source": source,
                "last_test": self._get_current_time(),
                "file_size": file.stat().st_size,
                "file_mtime": file.stat().st_mtime
            }
            
            # 保存元数据
            meta_file = self._get_meta_file(file)
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            
            logger.info(f"徽章添加成功: {status}")
            return True
            
        except Exception as e:
            logger.error(f"添加徽章失败: {e}")
            return False
    
    def check_badge(self, file_path):
        """检查徽章"""
        try:
            file = Path(file_path)
            meta_file = self._get_meta_file(file)
            
            if not meta_file.exists():
                logger.info(f"文件没有徽章: {file.name}")
                return None
            
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            logger.info(f"文件徽章: {file.name}")
            logger.info(f"  状态: {meta.get('status')}")
            logger.info(f"  来源: {meta.get('source')}")
            logger.info(f"  最后测试: {meta.get('last_test')}")
            
            return meta
            
        except Exception as e:
            logger.error(f"检查徽章失败: {e}")
            return None
    
    def verify_directory(self, dir_path):
        """验证目录文件"""
        try:
            directory = Path(dir_path)
            if not directory.exists() or not directory.is_dir():
                logger.error(f"目录不存在: {dir_path}")
                return False
            
            logger.info(f"验证目录: {directory}")
            
            verified_count = 0
            for file in directory.rglob("*"):
                if file.is_file() and not file.name.endswith(".gstack.meta"):
                    # 检查是否有徽章
                    meta = self.check_badge(file)
                    if not meta:
                        # 添加默认徽章
                        self.add_badge(file, "unverified")
                    else:
                        verified_count += 1
            
            logger.info(f"验证完成，已验证 {verified_count} 个文件")
            return True
            
        except Exception as e:
            logger.error(f"验证目录失败: {e}")
            return False
    
    def list_badges(self, dir_path):
        """列出目录中的徽章"""
        try:
            directory = Path(dir_path)
            if not directory.exists() or not directory.is_dir():
                logger.error(f"目录不存在: {dir_path}")
                return False
            
            logger.info(f"列出目录徽章: {directory}")
            
            badges = []
            for meta_file in directory.rglob("*.gstack.meta"):
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    
                    original_file = Path(str(meta_file).replace(".gstack.meta", ""))
                    if original_file.exists():
                        badges.append({
                            "file": original_file.name,
                            "path": str(original_file),
                            "status": meta.get("status"),
                            "last_test": meta.get("last_test")
                        })
                except Exception as e:
                    logger.error(f"读取徽章失败 {meta_file}: {e}")
            
            if badges:
                logger.info(f"找到 {len(badges)} 个徽章:")
                for badge in badges:
                    logger.info(f"  - {badge['file']} ({badge['status']}) - {badge['last_test']}")
            else:
                logger.info("没有找到徽章")
            
            return badges
            
        except Exception as e:
            logger.error(f"列徽章失败: {e}")
            return []
    
    def _get_current_time(self):
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """主函数"""
    manager = BadgeManager()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python badge_manager.py add <file> <status> [source]  # 添加徽章")
        print("  python badge_manager.py check <file>                # 检查徽章")
        print("  python badge_manager.py verify <dir>                # 验证目录文件")
        print("  python badge_manager.py list <dir>                 # 列出徽章")
        return
    
    command = sys.argv[1].lower()
    
    if command == "add":
        if len(sys.argv) >= 4:
            file_path = sys.argv[2]
            status = sys.argv[3]
            source = sys.argv[4] if len(sys.argv) > 4 else None
            manager.add_badge(file_path, status, source)
        else:
            print("请提供文件路径和状态")
    elif command == "check":
        if len(sys.argv) > 2:
            manager.check_badge(sys.argv[2])
        else:
            print("请提供文件路径")
    elif command == "verify":
        if len(sys.argv) > 2:
            manager.verify_directory(sys.argv[2])
        else:
            print("请提供目录路径")
    elif command == "list":
        if len(sys.argv) > 2:
            manager.list_badges(sys.argv[2])
        else:
            print("请提供目录路径")
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
