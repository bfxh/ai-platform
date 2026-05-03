#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架构强制执行技能

功能:
- 强制执行 GSTACK 架构规则
- 验证任务是否符合目录结构要求
- 阻止违规操作

用法:
    python architect_enforce.py validate <task_description>
    python architect_enforce.py check <file_path>
    python architect_enforce.py enforce
"""

import os
import sys
import json
import re
from pathlib import Path
import logging

# 配置
AI_DIR = Path("/python").resolve()
LOG_FILE = AI_DIR / "logs" / "architect_enforce.log"

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
logger = logging.getLogger("ArchitectEnforce")


class ArchitectEnforcer:
    """架构强制执行器"""
    
    def __init__(self):
        self.ai_dir = AI_DIR
        self.architecture_rules = {
            "mcp_categories": ["JM", "BC", "Tools"],
            "cc_categories": ["1_Raw", "2_Old", "3_Unused"],
            "forbidden_paths": ["C:\\Desktop", "C:\\Downloads", "C:\\Users"],
            "protected_files": ["ai_architecture.json", "index.json", "mcp-config.json"]
        }
    
    def is_safe_path(self, base: str, target: str) -> bool:
        """检查路径是否安全，防止路径遍历"""
        base_real = os.path.realpath(base)
        target_real = os.path.realpath(target)
        common = os.path.commonpath([base_real, target_real])
        return common == base_real
    
    def validate_task(self, task_description):
        """验证任务描述是否符合架构规则"""
        try:
            logger.info(f"验证任务: {task_description}")
            
            violations = []
            
            # 检查是否提议直接修改核心配置文件
            for protected_file in self.architecture_rules["protected_files"]:
                if protected_file in task_description:
                    violations.append(f"禁止直接修改核心配置文件: {protected_file}")
            
            # 检查是否提议使用禁止的路径
            for forbidden_path in self.architecture_rules["forbidden_paths"]:
                if forbidden_path.lower() in task_description.lower():
                    violations.append(f"禁止使用路径: {forbidden_path}")
            
            # 检查是否跳过 GSTACK 工作流
            if "powershell" in task_description.lower() or "cmd" in task_description.lower():
                if "gstack" not in task_description.lower():
                    violations.append("禁止跳过 GSTACK 工作流直接使用命令行")
            
            # 检查 MCP 分类是否正确
            if "mcp" in task_description.lower():
                has_valid_category = False
                for category in self.architecture_rules["mcp_categories"]:
                    if category in task_description.upper():
                        has_valid_category = True
                        break
                if not has_valid_category:
                    violations.append("MCP 文件必须归类到 JM/BC/Tools 目录")
            
            # 检查 CC 分类是否正确
            if "cc" in task_description.lower():
                has_valid_category = False
                for category in self.architecture_rules["cc_categories"]:
                    if category in task_description:
                        has_valid_category = True
                        break
                if not has_valid_category:
                    violations.append("CC 文件必须归类到 1_Raw/2_Old/3_Unused 目录")
            
            if violations:
                logger.warning(f"任务验证失败，发现 {len(violations)} 个违规:")
                for violation in violations:
                    logger.warning(f"  - {violation}")
                return False, violations
            else:
                logger.info("任务验证通过")
                return True, []
                
        except Exception as e:
            logger.error(f"验证任务失败: {e}")
            return False, [f"验证过程出错: {e}"]
    
    def check_file(self, file_path):
        """检查文件是否在正确位置"""
        try:
            file = Path(file_path)
            if not file.exists():
                logger.error(f"文件不存在: {file_path}")
                return False, ["文件不存在"]
            
            logger.info(f"检查文件位置: {file.name}")
            
            # 检查路径是否安全，防止路径遍历
            if not self.is_safe_path(str(self.ai_dir), str(file)):
                return False, ["文件必须放在 /python 目录内，禁止路径遍历"]
            
            # 获取文件相对于 AI 目录的路径
            try:
                relative_path = file.relative_to(self.ai_dir)
                parts = relative_path.parts
                
                # 检查 MCP 文件
                if parts[0] == "MCP":
                    if len(parts) >= 2:
                        category = parts[1]
                        if category not in self.architecture_rules["mcp_categories"]:
                            return False, [f"MCP 文件必须放在 JM/BC/Tools 目录下，当前位置: {category}"]
                
                # 检查 CC 文件
                elif parts[0] == "CC":
                    if len(parts) >= 2:
                        category = parts[1]
                        if category not in self.architecture_rules["cc_categories"]:
                            return False, [f"CC 文件必须放在 1_Raw/2_Old/3_Unused 目录下，当前位置: {category}"]
                
                # 检查是否在 AI 目录外
                else:
                    return False, ["文件必须放在 /python 目录内"]
                
                logger.info("文件位置检查通过")
                return True, []
                
            except ValueError:
                return False, ["文件必须放在 /python 目录内"]
                
        except Exception as e:
            logger.error(f"检查文件失败: {e}")
            return False, [f"检查过程出错: {e}"]
    
    def enforce_architecture(self):
        """强制执行架构规则"""
        try:
            logger.info("强制执行架构规则...")
            
            # 检查 MCP 目录结构
            mcp_dir = self.ai_dir / "MCP"
            if mcp_dir.exists():
                for category in self.architecture_rules["mcp_categories"]:
                    category_dir = mcp_dir / category
                    if not category_dir.exists():
                        logger.warning(f"MCP 分类目录不存在: {category}")
                        category_dir.mkdir(exist_ok=True)
                        logger.info(f"已创建 MCP 分类目录: {category}")
            
            # 检查 CC 目录结构
            cc_dir = self.ai_dir / "CC"
            if cc_dir.exists():
                for category in self.architecture_rules["cc_categories"]:
                    category_dir = cc_dir / category
                    if not category_dir.exists():
                        logger.warning(f"CC 分类目录不存在: {category}")
                        category_dir.mkdir(exist_ok=True)
                        logger.info(f"已创建 CC 分类目录: {category}")
            
            logger.info("架构规则强制执行完成")
            return True
            
        except Exception as e:
            logger.error(f"强制执行架构规则失败: {e}")
            return False


def main():
    """主函数"""
    enforcer = ArchitectEnforcer()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python architect_enforce.py validate <task_description>  # 验证任务")
        print("  python architect_enforce.py check <file_path>          # 检查文件位置")
        print("  python architect_enforce.py enforce                   # 强制执行架构")
        return
    
    command = sys.argv[1].lower()
    
    if command == "validate":
        if len(sys.argv) > 2:
            task_description = " ".join(sys.argv[2:])
            valid, violations = enforcer.validate_task(task_description)
            if valid:
                print("✅ 任务验证通过")
            else:
                print("❌ 任务验证失败:")
                for violation in violations:
                    print(f"  - {violation}")
        else:
            print("请提供任务描述")
    elif command == "check":
        if len(sys.argv) > 2:
            file_path = sys.argv[2]
            valid, violations = enforcer.check_file(file_path)
            if valid:
                print("✅ 文件位置检查通过")
            else:
                print("❌ 文件位置检查失败:")
                for violation in violations:
                    print(f"  - {violation}")
        else:
            print("请提供文件路径")
    elif command == "enforce":
        enforcer.enforce_architecture()
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
