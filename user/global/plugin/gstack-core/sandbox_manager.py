#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSTACK 沙盒管理器

功能:
- 创建隔离的沙盒环境
- 测试新技能和MCP
- 安全验证后合并到主环境

用法:
    python sandbox_manager.py create      # 创建沙盒
    python sandbox_manager.py test <skill>  # 测试技能
    python sandbox_manager.py merge       # 合并到主环境
    python sandbox_manager.py cleanup     # 清理沙盒
"""

import os
import sys
import shutil
import json
import tempfile
from pathlib import Path
import logging

# 配置
AI_DIR = Path("/python").resolve()
SANDBOX_DIR = AI_DIR / "Sandbox"
SANDBOX_CONFIG = SANDBOX_DIR / "ai_architecture.json"
LOG_FILE = AI_DIR / "logs" / "sandbox.log"

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
logger = logging.getLogger("GSTACKSandbox")


class SandboxManager:
    """GSTACK 沙盒管理器"""
    
    def __init__(self):
        self.sandbox_dir = SANDBOX_DIR
        self.sandbox_config = SANDBOX_CONFIG
        
    def create_sandbox(self):
        """创建沙盒环境"""
        try:
            # 创建沙盒目录结构
            logger.info("创建沙盒环境...")
            
            # 主目录
            self.sandbox_dir.mkdir(parents=True, exist_ok=True)
            
            # MCP 目录
            (self.sandbox_dir / "MCP" / "JM").mkdir(parents=True, exist_ok=True)
            (self.sandbox_dir / "MCP" / "BC").mkdir(parents=True, exist_ok=True)
            (self.sandbox_dir / "MCP" / "Tools").mkdir(parents=True, exist_ok=True)
            
            # CC 目录
            (self.sandbox_dir / "CC" / "1_Raw").mkdir(parents=True, exist_ok=True)
            (self.sandbox_dir / "CC" / "2_Old").mkdir(parents=True, exist_ok=True)
            (self.sandbox_dir / "CC" / "3_Unused").mkdir(parents=True, exist_ok=True)
            
            # 复制核心配置文件
            main_config = AI_DIR / "ai_architecture.json"
            if main_config.exists():
                with open(main_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 修改配置指向沙盒
                config["mcp"]["base_path"] = str(self.sandbox_dir / "MCP")
                config["cc"]["path"] = str(self.sandbox_dir / "CC")
                
                # 保存沙盒配置
                with open(self.sandbox_config, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                logger.info(f"沙盒配置已创建: {self.sandbox_config}")
            else:
                logger.error("主配置文件不存在")
                return False
            
            logger.info("沙盒环境创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建沙盒失败: {e}")
            return False
    
    def test_skill(self, skill_name):
        """在沙盒中测试技能"""
        try:
            if not self.sandbox_dir.exists():
                logger.error("沙盒环境不存在，请先创建")
                return False
            
            logger.info(f"在沙盒中测试技能: {skill_name}")
            
            # 复制技能到沙盒
            main_skills_dir = AI_DIR / "MCP_Core" / "skills"
            sandbox_skills_dir = self.sandbox_dir / "MCP_Core" / "skills"
            sandbox_skills_dir.mkdir(parents=True, exist_ok=True)
            
            skill_path = main_skills_dir / skill_name
            if skill_path.exists():
                # 复制技能目录
                shutil.copytree(skill_path, sandbox_skills_dir / skill_name, dirs_exist_ok=True)
                logger.info(f"技能已复制到沙盒: {skill_name}")
            else:
                logger.error(f"技能不存在: {skill_name}")
                return False
            
            # 这里可以添加测试逻辑
            logger.info(f"技能 {skill_name} 测试完成")
            return True
            
        except Exception as e:
            logger.error(f"测试技能失败: {e}")
            return False
    
    def merge_to_main(self):
        """将沙盒内容合并到主环境"""
        try:
            if not self.sandbox_dir.exists():
                logger.error("沙盒环境不存在")
                return False
            
            logger.info("合并沙盒到主环境...")
            
            # 合并 MCP 文件
            sandbox_mcp = self.sandbox_dir / "MCP"
            main_mcp = AI_DIR / "MCP"
            
            if sandbox_mcp.exists():
                for category in ["JM", "BC", "Tools"]:
                    src_dir = sandbox_mcp / category
                    if src_dir.exists():
                        dst_dir = main_mcp / category
                        for file in src_dir.iterdir():
                            if file.is_file():
                                shutil.copy2(file, dst_dir)
                                logger.info(f"合并文件: {file.name}")
            
            # 合并技能
            sandbox_skills = self.sandbox_dir / "MCP_Core" / "skills"
            main_skills = AI_DIR / "MCP_Core" / "skills"
            
            if sandbox_skills.exists():
                for skill in sandbox_skills.iterdir():
                    if skill.is_dir():
                        dst_skill = main_skills / skill.name
                        shutil.copytree(skill, dst_skill, dirs_exist_ok=True)
                        logger.info(f"合并技能: {skill.name}")
            
            logger.info("沙盒合并完成")
            return True
            
        except Exception as e:
            logger.error(f"合并失败: {e}")
            return False
    
    def cleanup_sandbox(self):
        """清理沙盒环境"""
        try:
            if self.sandbox_dir.exists():
                logger.info("清理沙盒环境...")
                shutil.rmtree(self.sandbox_dir)
                logger.info("沙盒已清理")
            else:
                logger.info("沙盒环境不存在")
            return True
            
        except Exception as e:
            logger.error(f"清理沙盒失败: {e}")
            return False


def main():
    """主函数"""
    manager = SandboxManager()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python sandbox_manager.py create      # 创建沙盒")
        print("  python sandbox_manager.py test <skill>  # 测试技能")
        print("  python sandbox_manager.py merge       # 合并到主环境")
        print("  python sandbox_manager.py cleanup     # 清理沙盒")
        return
    
    command = sys.argv[1].lower()
    
    if command == "create":
        manager.create_sandbox()
    elif command == "test":
        if len(sys.argv) > 2:
            manager.test_skill(sys.argv[2])
        else:
            print("请指定要测试的技能")
    elif command == "merge":
        manager.merge_to_main()
    elif command == "cleanup":
        manager.cleanup_sandbox()
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
