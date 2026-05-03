#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统优化技能
System Optimization Skill

功能:
- 清理备份文件
- 清理临时文件
- 统一日志管理
- 统一配置管理
- 依赖检查和更新

用法:
    python system_optimizer_skill.py clean_backups
    python system_optimizer_skill.py clean_temp
    python system_optimizer_skill.py unify_logs
    python system_optimizer_skill.py unify_config
    python system_optimizer_skill.py check_dependencies
    python system_optimizer_skill.py full_optimize
"""

import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base import Skill, handle_errors

# 跨平台路径处理
import platform

# 获取用户主目录作为默认根目录
if platform.system() == "Windows":
    AI_ROOT = Path(os.environ.get("AI_ROOT", os.path.expanduser("~")))
else:
    AI_ROOT = Path(os.environ.get("AI_ROOT", os.path.expanduser("~")))

# 确保路径格式正确
AI_ROOT = AI_ROOT / "AI" if "AI" not in str(AI_ROOT) else AI_ROOT
BACKUPS_DIR = AI_ROOT / "backups"
TEMP_DIR = AI_ROOT / "temp"  # 使用小写temp，更符合跨平台规范
LOGS_DIR = AI_ROOT / "logs"  # 使用小写logs，更符合跨平台规范
CONFIG_DIR = AI_ROOT / "config"  # 使用小写config，更符合跨平台规范


class SystemOptimizerSkill(Skill):
    """系统优化技能"""

    # 技能元数据
    name = "system_optimizer"
    description = "系统优化 - 清理备份文件、临时文件、统一日志和配置管理"
    version = "1.0.0"
    author = "MCP Core"
    config_prefix = "system_optimizer"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.results: Dict[str, Any] = {
            "cleaned_files": [],
            "cleaned_size": 0,
            "errors": [],
            "warnings": [],
            "updated_configs": [],
        }

    def clean_backups(self, max_age_days: int = 30, keep_count: int = 5) -> Dict[str, Any]:
        """
        清理旧备份文件

        Args:
            max_age_days: 保留最大天数
            keep_count: 最少保留数量
        """
        print("\n" + "=" * 60)
        print("清理备份文件")
        print("=" * 60 + "\n")

        if not BACKUPS_DIR.exists():
            print("备份目录不存在")
            return self.results

        backup_folders = sorted(
            BACKUPS_DIR.iterdir(),
            key=lambda x: x.stat().st_mtime if x.exists() else 0,
            reverse=True,
        )

        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        for i, folder in enumerate(backup_folders):
            if not folder.is_dir():
                continue

            folder_mtime = datetime.fromtimestamp(folder.stat().st_mtime)

            if i >= keep_count and folder_mtime < cutoff_date:
                try:
                    size = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())
                    shutil.rmtree(folder)
                    self.results["cleaned_files"].append(str(folder))
                    self.results["cleaned_size"] += size
                    print(f"删除旧备份: {folder.name} ({size / 1024 / 1024:.2f} MB)")
                except Exception as e:
                    self.results["errors"].append(f"删除失败 {folder}: {e}")
                    print(f"删除失败: {e}")
            else:
                print(f"保留备份: {folder.name}")

        print(
            f"\n清理完成: {len(self.results['cleaned_files'])} 个文件夹, {self.results['cleaned_size'] / 1024 / 1024:.2f} MB"
        )
        return self.results

    def clean_temp(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        清理临时文件

        Args:
            max_age_hours: 保留最大小时数
        """
        print("\n" + "=" * 60)
        print("清理临时文件")
        print("=" * 60 + "\n")

        if not TEMP_DIR.exists():
            print("临时目录不存在")
            return self.results

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        for item in TEMP_DIR.iterdir():
            try:
                item_mtime = datetime.fromtimestamp(item.stat().st_mtime)

                if item_mtime < cutoff_time:
                    if item.is_file():
                        size = item.stat().st_size
                        item.unlink()
                        self.results["cleaned_files"].append(str(item))
                        self.results["cleaned_size"] += size
                        print(f"删除文件: {item.name}")
                    elif item.is_dir():
                        size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                        shutil.rmtree(item)
                        self.results["cleaned_files"].append(str(item))
                        self.results["cleaned_size"] += size
                        print(f"删除目录: {item.name} ({size / 1024 / 1024:.2f} MB)")
            except Exception as e:
                self.results["errors"].append(f"清理失败 {item}: {e}")
                print(f"清理失败: {e}")

        print(
            f"\n清理完成: {len(self.results['cleaned_files'])} 项, {self.results['cleaned_size'] / 1024 / 1024:.2f} MB"
        )
        return self.results

    def unify_logs(self) -> Dict:
        """
        统一日志管理
        """
        print("\n" + "=" * 60)
        print("统一日志管理")
        print("=" * 60 + "\n")

        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        log_locations = [
            AI_ROOT / "logs",
            AI_ROOT / "MCP_Core" / "logs",
            AI_ROOT / ".stepclaw" / "logs",
        ]

        unified_log_config = {
            "version": "1.0",
            "unified_log_dir": str(LOGS_DIR),
            "log_rotation": {"max_size": "10MB", "backup_count": 5},
            "log_levels": {"default": "INFO", "mcp_core": "DEBUG", "workflow": "INFO"},
            "log_files": {
                "system": "system.log",
                "mcp": "mcp.log",
                "workflow": "workflow.log",
                "error": "error.log",
            },
        }

        config_file = LOGS_DIR / "log_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(unified_log_config, f, indent=2, ensure_ascii=False)

        print(f"创建统一日志配置: {config_file}")

        for log_dir in log_locations:
            if log_dir.exists() and log_dir != LOGS_DIR:
                print(f"发现日志目录: {log_dir}")

                for log_file in log_dir.glob("*.log"):
                    try:
                        dest = LOGS_DIR / f"{log_dir.parent.name}_{log_file.name}"
                        if not dest.exists():
                            shutil.copy2(log_file, dest)
                            print(f"  复制日志: {log_file.name} -> {dest.name}")
                    except Exception as e:
                        self.results["warnings"].append(f"复制日志失败 {log_file}: {e}")

        self.results["updated_configs"].append(str(config_file))
        print(f"\n日志统一完成")
        return self.results

    def unify_config(self) -> Dict:
        """
        统一配置管理
        """
        print("\n" + "=" * 60)
        print("统一配置管理")
        print("=" * 60 + "\n")

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        config_files = [
            AI_ROOT / "MCP" / "mcp-config.json",
            AI_ROOT / "MCP_Core" / "unified_config.json",
            AI_ROOT / "stepfun-config.json",
            AI_ROOT / "claude-mcp-config.json",
            AI_ROOT / "langfuse-mcp-config.json",
        ]

        master_config = {
            "version": "2.0.0",
            "name": "AI Unified Configuration",
            "last_updated": datetime.now().isoformat(),
            "config_sources": [],
            "server": {},
            "models": {},
            "skills": {},
            "workflows": {},
            "paths": {},
        }

        for config_file in config_files:
            if config_file.exists():
                print(f"发现配置文件: {config_file.name}")
                master_config["config_sources"].append(str(config_file))

                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        config_data = json.load(f)

                    if "server" in config_data:
                        master_config["server"].update(config_data["server"])
                    if "models" in config_data:
                        master_config["models"].update(config_data["models"])
                    if "skills" in config_data:
                        master_config["skills"].update(config_data["skills"])
                    if "workflows" in config_data:
                        master_config["workflows"].update(config_data["workflows"])
                    if "paths" in config_data:
                        master_config["paths"].update(config_data["paths"])

                except Exception as e:
                    self.results["warnings"].append(f"读取配置失败 {config_file}: {e}")

        master_config_file = CONFIG_DIR / "master_config.json"
        with open(master_config_file, "w", encoding="utf-8") as f:
            json.dump(master_config, f, indent=2, ensure_ascii=False)

        print(f"\n创建主配置文件: {master_config_file}")
        self.results["updated_configs"].append(str(master_config_file))

        self._update_config_references(master_config_file)

        print(f"\n配置统一完成")
        return self.results

    def _update_config_references(self, master_config: Path):
        """
        更新配置引用
        """
        print("\n更新配置引用...")

        files_to_update = [
            AI_ROOT / "MCP_Core" / "server.py",
            AI_ROOT / "MCP_Core" / "config.py",
            AI_ROOT / "ai.py",
        ]

        for file_path in files_to_update:
            if file_path.exists():
                print(f"检查: {file_path.name}")

    def check_dependencies(self) -> Dict:
        """
        检查依赖关系
        """
        print("\n" + "=" * 60)
        print("检查依赖关系")
        print("=" * 60 + "\n")

        dependencies = {
            "backup_dependencies": self._find_backup_dependencies(),
            "temp_dependencies": self._find_temp_dependencies(),
            "log_dependencies": self._find_log_dependencies(),
            "config_dependencies": self._find_config_dependencies(),
        }

        dep_file = AI_ROOT / "temp" / "optimization_dependencies.json"
        dep_file.parent.mkdir(parents=True, exist_ok=True)
        with open(dep_file, "w", encoding="utf-8") as f:
            json.dump(dependencies, f, indent=2, ensure_ascii=False)

        print(f"\n依赖关系已保存到: {dep_file}")

        for category, deps in dependencies.items():
            print(f"\n{category}:")
            for dep in deps:
                print(f"  - {dep}")

        return dependencies

    def _find_backup_dependencies(self) -> List[str]:
        """查找备份相关依赖"""
        deps = []

        backup_refs = [
            AI_ROOT / "GJ" / "GJ" / "auto_backup.py",
            AI_ROOT / "MCP_Core" / "skills" / "file_backup" / "skill.py",
        ]

        for ref in backup_refs:
            if ref.exists():
                deps.append(str(ref))

        return deps

    def _find_temp_dependencies(self) -> List[str]:
        """查找临时文件相关依赖"""
        deps = []

        temp_refs = [
            AI_ROOT / "auto_workflow.py",
            AI_ROOT / "MCP_Core" / "cache.py",
        ]

        for ref in temp_refs:
            if ref.exists():
                deps.append(str(ref))

        return deps

    def _find_log_dependencies(self) -> List[str]:
        """查找日志相关依赖"""
        deps = []

        log_refs = [
            AI_ROOT / "MCP_Core" / "logger.py",
            AI_ROOT / "MCP_Core" / "server.py",
        ]

        for ref in log_refs:
            if ref.exists():
                deps.append(str(ref))

        return deps

    def _find_config_dependencies(self) -> List[str]:
        """查找配置相关依赖"""
        deps = []

        config_refs = [
            AI_ROOT / "MCP_Core" / "config.py",
            AI_ROOT / "MCP_Core" / "config_manager.py",
            AI_ROOT / "ai.py",
        ]

        for ref in config_refs:
            if ref.exists():
                deps.append(str(ref))

        return deps

    def full_optimize(self) -> Dict:
        """
        完整优化
        """
        print("\n" + "=" * 60)
        print("开始完整系统优化")
        print("=" * 60)

        self.check_dependencies()
        self.clean_backups()
        self.clean_temp()
        self.unify_logs()
        self.unify_config()

        report = self._generate_report()

        print("\n" + "=" * 60)
        print("优化完成")
        print("=" * 60)

        return report

    def _generate_report(self) -> Dict:
        """
        生成优化报告
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "cleaned_files_count": len(self.results["cleaned_files"]),
                "cleaned_size_mb": round(self.results["cleaned_size"] / 1024 / 1024, 2),
                "errors_count": len(self.results["errors"]),
                "warnings_count": len(self.results["warnings"]),
                "updated_configs_count": len(self.results["updated_configs"]),
            },
            "details": self.results,
        }

        report_file = (
            AI_ROOT
            / "logs"
            / f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n优化报告已保存: {report_file}")
        return report

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义"""
        return {
            "action": {
                "type": "string",
                "required": True,
                "enum": [
                    "clean_backups",
                    "clean_temp",
                    "unify_logs",
                    "unify_config",
                    "check_dependencies",
                    "full_optimize",
                ],
                "description": "操作类型",
            },
            "max_age_days": {
                "type": "integer",
                "required": False,
                "default": 30,
                "description": "备份文件保留最大天数",
            },
            "keep_count": {
                "type": "integer",
                "required": False,
                "default": 5,
                "description": "备份文件最少保留数量",
            },
            "max_age_hours": {
                "type": "integer",
                "required": False,
                "default": 24,
                "description": "临时文件保留最大小时数",
            },
        }

    @handle_errors
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        action = params.get("action")
        max_age_days = params.get("max_age_days", 30)
        keep_count = params.get("keep_count", 5)
        max_age_hours = params.get("max_age_hours", 24)

        # 重置结果
        self.results = {
            "cleaned_files": [],
            "cleaned_size": 0,
            "errors": [],
            "warnings": [],
            "updated_configs": [],
        }

        if action == "clean_backups":
            result = self.clean_backups(max_age_days, keep_count)
            return {"success": True, "result": result}
        elif action == "clean_temp":
            result = self.clean_temp(max_age_hours)
            return {"success": True, "result": result}
        elif action == "unify_logs":
            result = self.unify_logs()
            return {"success": True, "result": result}
        elif action == "unify_config":
            result = self.unify_config()
            return {"success": True, "result": result}
        elif action == "check_dependencies":
            result = self.check_dependencies()
            return {"success": True, "result": result}
        elif action == "full_optimize":
            result = self.full_optimize()
            return {"success": True, "result": result}
        else:
            return {"success": False, "error": "无效的操作"}


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python system_optimizer_skill.py <命令>")
        print("命令:")
        print("  clean_backups      清理备份文件")
        print("  clean_temp         清理临时文件")
        print("  unify_logs         统一日志管理")
        print("  unify_config       统一配置管理")
        print("  check_dependencies 检查依赖关系")
        print("  full_optimize      完整优化")
        return

    command = sys.argv[1]
    optimizer = SystemOptimizerSkill()

    if command == "clean_backups":
        optimizer.clean_backups()
    elif command == "clean_temp":
        optimizer.clean_temp()
    elif command == "unify_logs":
        optimizer.unify_logs()
    elif command == "unify_config":
        optimizer.unify_config()
    elif command == "check_dependencies":
        optimizer.check_dependencies()
    elif command == "full_optimize":
        optimizer.full_optimize()
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
