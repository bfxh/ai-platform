#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blender 临时文件清理器

功能:
- 检测并清理 .blend1 和 .blend@ 临时文件
- 自动归类到 CC/3_Unused/Blender_Temp/
- 支持定期自动清理

用法:
    python blender_cleaner.py scan      # 扫描临时文件
    python blender_cleaner.py cleanup    # 清理临时文件
    python blender_cleaner.py monitor    # 监控模式
"""

import os
import sys
import shutil
import time
from pathlib import Path
import logging

# 配置
AI_DIR = Path("/python").resolve()
BLENDER_TEMP_DIR = AI_DIR / "CC" / "3_Unused" / "Blender_Temp"
LOG_FILE = AI_DIR / "logs" / "blender_cleaner.log"

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
logger = logging.getLogger("BlenderCleaner")


class BlenderCleaner:
    """Blender 临时文件清理器"""
    
    def __init__(self):
        self.ai_dir = AI_DIR
        self.blender_temp_dir = BLENDER_TEMP_DIR
        self.junk_extensions = [".blend1", ".blend@"]
        
    def scan_blender_junk(self):
        """扫描 Blender 临时文件"""
        try:
            logger.info("扫描 Blender 临时文件...")
            
            junk_files = []
            
            # 扫描整个 AI 目录
            for extension in self.junk_extensions:
                for file in self.ai_dir.rglob(f"*{extension}"):
                    # 排除 CC 目录中的文件
                    if "CC" not in str(file):
                        junk_files.append(file)
            
            if junk_files:
                logger.info(f"发现 {len(junk_files)} 个 Blender 临时文件:")
                for file in junk_files[:10]:  # 只显示前10个
                    logger.info(f"  - {file}")
                if len(junk_files) > 10:
                    logger.info(f"  ... 还有 {len(junk_files) - 10} 个文件")
            else:
                logger.info("未发现 Blender 临时文件")
            
            return junk_files
            
        except Exception as e:
            logger.error(f"扫描失败: {e}")
            return []
    
    def cleanup_blender_junk(self):
        """清理 Blender 临时文件"""
        try:
            junk_files = self.scan_blender_junk()
            
            if not junk_files:
                return True
            
            # 创建临时文件目录
            self.blender_temp_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("清理 Blender 临时文件...")
            
            moved_count = 0
            for file in junk_files:
                try:
                    # 移动到临时目录
                    dest_file = self.blender_temp_dir / file.name
                    shutil.move(file, dest_file)
                    moved_count += 1
                    logger.info(f"已移动: {file.name}")
                except Exception as e:
                    logger.error(f"移动文件失败 {file}: {e}")
            
            logger.info(f"共移动 {moved_count} 个 Blender 临时文件到: {self.blender_temp_dir}")
            
            # 清理超过7天的文件
            self.cleanup_old_files()
            
            return True
            
        except Exception as e:
            logger.error(f"清理失败: {e}")
            return False
    
    def cleanup_old_files(self):
        """清理超过7天的临时文件"""
        try:
            if not self.blender_temp_dir.exists():
                return
            
            logger.info("清理超过7天的 Blender 临时文件...")
            
            current_time = time.time()
            seven_days_ago = current_time - (7 * 24 * 60 * 60)
            
            deleted_count = 0
            for file in self.blender_temp_dir.iterdir():
                if file.is_file():
                    file_mtime = file.stat().st_mtime
                    if file_mtime < seven_days_ago:
                        file.unlink()
                        deleted_count += 1
                        logger.info(f"已删除过期文件: {file.name}")
            
            if deleted_count > 0:
                logger.info(f"共删除 {deleted_count} 个过期的 Blender 临时文件")
            else:
                logger.info("没有过期的 Blender 临时文件")
                
        except Exception as e:
            logger.error(f"清理过期文件失败: {e}")
    
    def safe_clean(self, user_input: str, base_dir: Path):
        """安全清理文件，防止路径注入"""
        target = (base_dir / user_input).resolve()
        # 确保目标仍在 base_dir 内
        if not str(target).startswith(str(base_dir.resolve())):
            raise ValueError("非法路径访问")
        if target.exists():
            target.unlink()
            logger.info(f"已安全删除: {target}")
    
    def monitor(self):
        """监控模式"""
        logger.info("启动 Blender 临时文件监控...")
        
        try:
            while True:
                self.cleanup_blender_junk()
                # 每10分钟检查一次
                time.sleep(600)
                
        except KeyboardInterrupt:
            logger.info("监控被用户中断")
        except Exception as e:
            logger.error(f"监控出错: {e}")


def main():
    """主函数"""
    cleaner = BlenderCleaner()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python blender_cleaner.py scan      # 扫描临时文件")
        print("  python blender_cleaner.py cleanup    # 清理临时文件")
        print("  python blender_cleaner.py monitor    # 监控模式")
        return
    
    command = sys.argv[1].lower()
    
    if command == "scan":
        cleaner.scan_blender_junk()
    elif command == "cleanup":
        cleaner.cleanup_blender_junk()
    elif command == "monitor":
        cleaner.monitor()
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
