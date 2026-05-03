#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Architecture Manager - GSTACK Skill
/python\gstack_core\skills\ai_architecture_manager\skill.py

功能:
- 每次对话启动时自动检查架构
- 提供 /check, /backup, /cleanup, /update 命令
- 输出状态报告
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 确保核心模块在路径中
sys.path.insert(0, "/python/scripts")
from arch_core import ArchitectureManager


# =============================================================================
# Skill 元数据
# =============================================================================
SKILL_NAME = "ai_architecture_manager"
SKILL_VERSION = "1.0.0"
SKILL_DESCRIPTION = "AI 架构管理系统 - 检查/备份/清理/更新"


class AIArchitectureSkill:
    """
    GSTACK Skill: AI Architecture Manager

    命令:
        /check   - 检查架构完整性
        /backup  - 备份关键目录和文件
        /cleanup - 清理临时文件和旧日志
        /update  - 更新 GitHub 项目
        /status  - 查看完整状态报告
    """

    def __init__(self):
        self.name = SKILL_NAME
        self.version = SKILL_VERSION
        self.manager = ArchitectureManager()
        self.last_check_result: Optional[Dict] = None
        self.auto_check_done = False

    # -------------------------------------------------------------------------
    # 自动检查（对话启动时调用）
    # -------------------------------------------------------------------------
    def on_conversation_start(self) -> str:
        """
        每次对话启动时自动调用
        返回状态报告字符串
        """
        if self.auto_check_done:
            return ""

        result = self.manager.check_architecture()
        self.last_check_result = result.to_dict()
        self.auto_check_done = True

        lines = [
            "=" * 60,
            "[AI Architecture Manager] 自动架构检查",
            "=" * 60,
            f"时间: {result.timestamp}",
            f"结果: {'通过' if result.success else '未通过'}",
            f"目录: {result.total_dirs - len(result.missing_dirs)}/{result.total_dirs} 正常",
        ]

        if result.missing_dirs:
            lines.append(f"缺失目录: {', '.join(result.missing_dirs)}")
        if result.missing_files:
            lines.append(f"缺失文件: {', '.join(result.missing_files)}")

        lines.append("-" * 60)
        lines.append("可用命令: /check | /backup | /cleanup | /update | /status")
        lines.append("=" * 60)

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # 命令处理
    # -------------------------------------------------------------------------
    def handle_command(self, command: str, args: List[str] = None) -> str:
        """
        处理 Skill 命令

        Args:
            command: 命令名称 (check/backup/cleanup/update/status)
            args: 额外参数

        Returns:
            格式化后的结果字符串
        """
        args = args or []
        cmd = command.lower().strip("/")

        if cmd == "check":
            return self._cmd_check()
        elif cmd == "backup":
            name = args[0] if args else None
            return self._cmd_backup(name)
        elif cmd == "cleanup":
            dry_run = "--dry-run" in args
            return self._cmd_cleanup(dry_run)
        elif cmd == "update":
            repos = args if args else None
            return self._cmd_update(repos)
        elif cmd == "status":
            return self._cmd_status()
        else:
            return self._help_text()

    def _cmd_check(self) -> str:
        """/check - 检查架构"""
        result = self.manager.check_architecture()
        self.last_check_result = result.to_dict()

        lines = [
            "[check] 架构检查结果",
            "-" * 40,
            f"时间: {result.timestamp}",
            f"状态: {'通过' if result.success else '未通过'}",
            f"目录检查: {result.total_dirs - len(result.missing_dirs)}/{result.total_dirs}",
        ]

        if result.dir_sizes:
            lines.append("目录大小:")
            for d, s in result.dir_sizes.items():
                lines.append(f"  {d}: {s}")

        if result.missing_dirs:
            lines.append(f"缺失目录 ({len(result.missing_dirs)}):")
            for d in result.missing_dirs:
                lines.append(f"  - {d}")

        if result.missing_files:
            lines.append(f"缺失文件 ({len(result.missing_files)}):")
            for f in result.missing_files:
                lines.append(f"  - {f}")

        if result.issues:
            lines.append(f"问题 ({len(result.issues)}):")
            for issue in result.issues:
                lines.append(f"  ! {issue}")

        lines.append("-" * 40)
        lines.append(result.summary)
        return "\n".join(lines)

    def _cmd_backup(self, name: Optional[str] = None) -> str:
        """/backup [name] - 备份架构"""
        result = self.manager.backup_ai(backup_name=name)

        lines = [
            "[backup] 备份结果",
            "-" * 40,
            f"时间: {result.timestamp}",
            f"状态: {'成功' if result.success else '失败'}",
            f"备份路径: {result.backup_path}",
            f"备份大小: {result.backup_size}",
            f"文件数: {result.files_backed}",
            f"目录数: {result.dirs_backed}",
            f"耗时: {result.duration_sec}s",
        ]

        if result.errors:
            lines.append(f"错误 ({len(result.errors)}):")
            for e in result.errors:
                lines.append(f"  ! {e}")

        return "\n".join(lines)

    def _cmd_cleanup(self, dry_run: bool = False) -> str:
        """/cleanup [--dry-run] - 清理文件"""
        result = self.manager.cleanup_files(dry_run=dry_run)

        lines = [
            f"[cleanup] 清理结果 {'(模拟)' if dry_run else ''}",
            "-" * 40,
            f"时间: {result.timestamp}",
            f"状态: {'成功' if result.success else '失败'}",
            f"扫描项目: {result.items_scanned}",
            f"删除文件: {result.files_removed}",
            f"删除目录: {result.dirs_removed}",
            f"释放空间: {result.space_freed_mb} MB",
        ]

        if result.details:
            lines.append("详情:")
            for d in result.details[:20]:
                lines.append(f"  - {d}")
            if len(result.details) > 20:
                lines.append(f"  ... 共 {len(result.details)} 项")

        if result.errors:
            lines.append(f"错误 ({len(result.errors)}):")
            for e in result.errors:
                lines.append(f"  ! {e}")

        return "\n".join(lines)

    def _cmd_update(self, repos: Optional[List[str]] = None) -> str:
        """/update [repo1 repo2 ...] - 更新 GitHub 项目"""
        result = self.manager.update_github(repos=repos)

        lines = [
            "[update] GitHub 更新结果",
            "-" * 40,
            f"时间: {result.timestamp}",
            f"状态: {'成功' if result.success else '失败'}",
            f"检查仓库: {result.repos_checked}",
            f"更新成功: {result.repos_updated}",
            f"更新失败: {result.repos_failed}",
        ]

        if result.details:
            lines.append("详情:")
            for d in result.details:
                status_icon = "OK" if d.get("status") == "updated" else "FAIL"
                lines.append(f"  [{status_icon}] {d.get('repo')}")
                if d.get("output"):
                    lines.append(f"      {d.get('output')}")
                if d.get("error"):
                    lines.append(f"      ERR: {d.get('error')}")

        if result.errors:
            lines.append(f"错误 ({len(result.errors)}):")
            for e in result.errors:
                lines.append(f"  ! {e}")

        return "\n".join(lines)

    def _cmd_status(self) -> str:
        """/status - 完整状态报告"""
        report = self.manager.get_status_report()

        lines = [
            "[status] 完整状态报告",
            "=" * 50,
            f"时间: {report.get('timestamp')}",
            f"根目录: {report.get('root')}",
            f"总大小: {report.get('total_size')}",
            "-" * 50,
        ]

        arch = report.get("architecture", {})
        lines.append("架构状态:")
        lines.append(f"  检查通过: {arch.get('success', False)}")
        lines.append(f"  缺失目录: {len(arch.get('missing_dirs', []))}")
        lines.append(f"  缺失文件: {len(arch.get('missing_files', []))}")

        backups = report.get("backups", [])
        lines.append(f"备份历史: {len(backups)} 次")
        for b in backups[-5:]:
            lines.append(f"  - {b.get('name')} ({b.get('size')}) @ {b.get('timestamp')}")

        lines.append("=" * 50)
        return "\n".join(lines)

    def _help_text(self) -> str:
        """帮助文本"""
        return """
AI Architecture Manager Skill

命令:
  /check              检查架构完整性
  /backup [name]      备份关键目录和文件
  /cleanup [--dry-run] 清理临时文件和旧日志
  /update [repos...]  更新 GitHub 项目
  /status             查看完整状态报告

示例:
  /check
  /backup daily_backup
  /cleanup --dry-run
  /update repo1 repo2
  /status
""".strip()

    # -------------------------------------------------------------------------
    # GSTACK 集成接口
    # -------------------------------------------------------------------------
    def execute(self, action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        GSTACK 统一执行接口

        Args:
            action: 动作名称
            params: 参数字典

        Returns:
            JSON 可序列化的结果字典
        """
        params = params or {}
        result_str = self.handle_command(action, params.get("args", []))

        return {
            "skill": self.name,
            "version": self.version,
            "action": action,
            "result": result_str,
            "timestamp": time.time(),
        }


# =============================================================================
# 单例实例（GSTACK 加载时使用）
# =============================================================================
_skill_instance: Optional[AIArchitectureSkill] = None


def get_skill() -> AIArchitectureSkill:
    """获取 Skill 单例"""
    global _skill_instance
    if _skill_instance is None:
        _skill_instance = AIArchitectureSkill()
    return _skill_instance


# =============================================================================
# GSTACK 标准接口
# =============================================================================
def on_load() -> str:
    """Skill 加载时调用"""
    skill = get_skill()
    return f"[{skill.name}] v{skill.version} 已加载"


def on_conversation_start() -> str:
    """对话开始时调用 - 自动检查架构"""
    skill = get_skill()
    return skill.on_conversation_start()


def handle_command(command: str, args: List[str] = None) -> str:
    """处理命令"""
    skill = get_skill()
    return skill.handle_command(command, args)


def execute(action: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """GSTACK 执行接口"""
    skill = get_skill()
    return skill.execute(action, params)


# =============================================================================
# 本地测试
# =============================================================================
if __name__ == "__main__":
    print(on_load())
    print()
    print(on_conversation_start())
    print()
    print(handle_command("/status"))
