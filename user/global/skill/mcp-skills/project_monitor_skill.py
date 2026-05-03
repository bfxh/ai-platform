#!/usr/bin/env python3
"""
BlockWeaponArena - ProjectMonitor 技能
项目状态监控系统

功能:
1. 检查关卡完成度
2. 统计模型数量
3. 生成进度报告
4. 提醒待完成任务
5. 监控项目健康状态

作者: AI Assistant
版本: 1.0
日期: 2026-03-31
"""

import unreal
import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

# ============================================================================
# 项目配置
# ============================================================================

PROJECT_CONFIG = {
    "name": "BlockWeaponArena",
    "version": "1.0",
    "root_path": "%SOFTWARE_DIR%/KF/JM/UE_5.6/BlockWeaponArena",
    "content_path": "%SOFTWARE_DIR%/KF/JM/UE_5.6/BlockWeaponArena/Content",
    
    "levels": {
        "Map_OpenPlains": {"required": True, "category": "战斗关卡"},
        "Map_NarrowDungeon": {"required": True, "category": "战斗关卡"},
        "Map_MountainForest": {"required": True, "category": "战斗关卡"},
        "Map_Ruins": {"required": True, "category": "战斗关卡"},
        "Map_WeaponWorkshop": {"required": True, "category": "战斗关卡"},
        "Map_TrajectoryTest": {"required": True, "category": "测试关卡"},
        "Map_TrainingGround": {"required": True, "category": "训练关卡"}
    },
    
    "required_directories": [
        "/Game/Maps",
        "/Game/Meshes/SceneBuildings",
        "/Game/Meshes/BlockPiece",
        "/Game/Meshes/WeaponPart",
        "/Game/Materials",
        "/Game/Blueprints",
        "/Game/VFX"
    ],
    
    "milestones": [
        {"name": "Phase 1: 核心方块系统", "weight": 20, "tasks": ["碎块数据结构", "连接点系统", "组装管理器"]},
        {"name": "Phase 2: 武器系统", "weight": 15, "tasks": ["武器运行时实例", "武器物理", "武器蓝图存档"]},
        {"name": "Phase 3: 轨迹系统", "weight": 25, "tasks": ["输入采集", "轨迹约束", "样条生成", "碰撞检测"]},
        {"name": "Phase 4: 动作联动+战斗", "weight": 20, "tasks": ["角色状态采集", "联动规则引擎", "伤害计算", "Buff系统"]},
        {"name": "Phase 5: 场景+UI+网络", "weight": 20, "tasks": ["场景管理器", "组装UI", "战斗HUD", "网络同步"]}
    ]
}

# ============================================================================
# 监控指标类
# ============================================================================

class ProjectHealthStatus(Enum):
    EXCELLENT = "优秀"
    GOOD = "良好"
    WARNING = "警告"
    CRITICAL = "严重"
    UNKNOWN = "未知"

@dataclass
class LevelStatus:
    """关卡状态"""
    name: str
    exists: bool
    has_lighting: bool
    has_player_starts: bool
    has_post_process: bool
    building_count: int
    completion_percentage: float
    issues: List[str]

@dataclass
class AssetStatistics:
    """资源统计"""
    total_static_meshes: int
    total_materials: int
    total_textures: int
    total_blueprints: int
    scene_buildings: int
    block_pieces: int
    weapon_parts: int
    by_level: Dict[str, int]

@dataclass
class MilestoneProgress:
    """里程碑进度"""
    name: str
    weight: int
    completed_tasks: int
    total_tasks: int
    percentage: float
    status: str

# ============================================================================
# ProjectMonitor 技能类
# ============================================================================

class ProjectMonitorSkill:
    """项目监控技能"""
    
    def __init__(self):
        self.asset_lib = unreal.EditorAssetLibrary
        self.level_lib = unreal.EditorLevelLibrary
        self.logs = []
        self.check_history = []
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        
        if level == "ERROR":
            unreal.log_error(f"[ProjectMonitor] {message}")
        elif level == "WARNING":
            unreal.log_warning(f"[ProjectMonitor] {message}")
        else:
            unreal.log(f"[ProjectMonitor] {message}")
    
    def check_project_structure(self) -> Dict:
        """检查项目结构"""
        self._log("检查项目结构...")
        
        results = {
            "existing_dirs": [],
            "missing_dirs": [],
            "health_score": 0
        }
        
        for dir_path in PROJECT_CONFIG["required_directories"]:
            if self.asset_lib.does_directory_exist(dir_path):
                results["existing_dirs"].append(dir_path)
            else:
                results["missing_dirs"].append(dir_path)
        
        total_dirs = len(PROJECT_CONFIG["required_directories"])
        existing_dirs = len(results["existing_dirs"])
        results["health_score"] = (existing_dirs / total_dirs) * 100
        
        self._log(f"目录检查完成: {existing_dirs}/{total_dirs}")
        
        return results
    
    def check_levels(self) -> List[LevelStatus]:
        """检查所有关卡状态"""
        self._log("检查关卡状态...")
        
        level_statuses = []
        
        for level_name, level_config in PROJECT_CONFIG["levels"].items():
            status = self._check_single_level(level_name)
            level_statuses.append(status)
        
        return level_statuses
    
    def _check_single_level(self, level_name: str) -> LevelStatus:
        """检查单个关卡"""
        map_path = f"/Game/Maps/{level_name}"
        
        exists = self.asset_lib.does_asset_exist(map_path)
        has_lighting = False
        has_player_starts = False
        has_post_process = False
        building_count = 0
        issues = []
        
        if exists:
            # 尝试加载关卡
            try:
                # 获取关卡中的Actor
                # 注意：这里简化处理，实际需要在关卡中检查
                
                # 检查建筑模型数量
                level_mesh_path = f"/Game/Meshes/SceneBuildings/{level_name.replace('Map_', '')}"
                if self.asset_lib.does_directory_exist(level_mesh_path):
                    assets = self.asset_lib.list_assets(level_mesh_path)
                    building_count = len([a for a in assets if "StaticMesh" in a])
                
                # 检查基本要求
                if building_count < 3:
                    issues.append(f"建筑模型数量不足: {building_count}")
                
            except Exception as e:
                issues.append(f"检查失败: {str(e)}")
        else:
            issues.append("关卡不存在")
        
        # 计算完成度
        completion = 0
        if exists:
            completion += 30
        if building_count >= 3:
            completion += 40
        if building_count >= 5:
            completion += 30
        
        return LevelStatus(
            name=level_name,
            exists=exists,
            has_lighting=has_lighting,
            has_player_starts=has_player_starts,
            has_post_process=has_post_process,
            building_count=building_count,
            completion_percentage=completion,
            issues=issues
        )
    
    def get_asset_statistics(self) -> AssetStatistics:
        """获取资源统计"""
        self._log("统计资源...")
        
        stats = AssetStatistics(
            total_static_meshes=0,
            total_materials=0,
            total_textures=0,
            total_blueprints=0,
            scene_buildings=0,
            block_pieces=0,
            weapon_parts=0,
            by_level={}
        )
        
        # 统计静态网格
        mesh_paths = self.asset_lib.list_assets("/Game/Meshes", recursive=True)
        stats.total_static_meshes = len([p for p in mesh_paths if "StaticMesh" in p])
        
        # 统计材质
        material_paths = self.asset_lib.list_assets("/Game/Materials", recursive=True)
        stats.total_materials = len([p for p in material_paths if "Material" in p])
        
        # 统计纹理
        texture_paths = self.asset_lib.list_assets("/Game/Textures", recursive=True)
        stats.total_textures = len([p for p in texture_paths if "Texture" in p])
        
        # 统计蓝图
        blueprint_paths = self.asset_lib.list_assets("/Game/Blueprints", recursive=True)
        stats.total_blueprints = len([p for p in blueprint_paths if "Blueprint" in p])
        
        # 统计场景建筑
        scene_building_paths = self.asset_lib.list_assets("/Game/Meshes/SceneBuildings", recursive=True)
        stats.scene_buildings = len([p for p in scene_building_paths if "StaticMesh" in p])
        
        # 统计方块碎块
        block_piece_paths = self.asset_lib.list_assets("/Game/Meshes/BlockPiece", recursive=True)
        stats.block_pieces = len([p for p in block_piece_paths if "StaticMesh" in p])
        
        # 统计武器部件
        weapon_part_paths = self.asset_lib.list_assets("/Game/Meshes/WeaponPart", recursive=True)
        stats.weapon_parts = len([p for p in weapon_part_paths if "StaticMesh" in p])
        
        # 按关卡统计
        for level_name in PROJECT_CONFIG["levels"].keys():
            level_key = level_name.replace("Map_", "")
            level_path = f"/Game/Meshes/SceneBuildings/{level_key}"
            if self.asset_lib.does_directory_exist(level_path):
                level_assets = self.asset_lib.list_assets(level_path)
                stats.by_level[level_key] = len([a for a in level_assets if "StaticMesh" in a])
            else:
                stats.by_level[level_key] = 0
        
        self._log(f"资源统计完成: {stats.total_static_meshes} 静态网格")
        
        return stats
    
    def check_milestones(self) -> List[MilestoneProgress]:
        """检查里程碑进度"""
        self._log("检查里程碑进度...")
        
        milestones = []
        
        for milestone in PROJECT_CONFIG["milestones"]:
            # 这里简化处理，实际应该检查具体任务完成情况
            # 根据资源数量估算进度
            
            stats = self.get_asset_statistics()
            
            # 根据里程碑名称估算完成度
            completed = 0
            total = len(milestone["tasks"])
            
            if "方块" in milestone["name"] or "Block" in milestone["name"]:
                completed = min(stats.block_pieces // 3, total)
            elif "武器" in milestone["name"] or "Weapon" in milestone["name"]:
                completed = min(stats.weapon_parts // 3, total)
            elif "场景" in milestone["name"] or "Scene" in milestone["name"]:
                completed = min(stats.scene_buildings // 5, total)
            elif "轨迹" in milestone["name"] or "Trajectory" in milestone["name"]:
                completed = min(len([l for l in self.check_levels() if l.exists]), total)
            else:
                completed = total // 2  # 默认50%
            
            percentage = (completed / total) * 100 if total > 0 else 0
            
            status = "进行中"
            if percentage >= 100:
                status = "已完成"
            elif percentage >= 70:
                status = "即将完成"
            elif percentage >= 30:
                status = "进行中"
            else:
                status = "刚开始"
            
            milestones.append(MilestoneProgress(
                name=milestone["name"],
                weight=milestone["weight"],
                completed_tasks=completed,
                total_tasks=total,
                percentage=percentage,
                status=status
            ))
        
        return milestones
    
    def calculate_overall_progress(self) -> float:
        """计算总体进度"""
        milestones = self.check_milestones()
        
        total_weight = sum(m.weight for m in milestones)
        weighted_progress = sum(m.percentage * (m.weight / 100) for m in milestones)
        
        return weighted_progress
    
    def get_health_status(self) -> ProjectHealthStatus:
        """获取项目健康状态"""
        structure = self.check_project_structure()
        levels = self.check_levels()
        progress = self.calculate_overall_progress()
        
        # 计算健康分数
        health_score = 0
        
        # 结构健康度 (30%)
        health_score += structure["health_score"] * 0.3
        
        # 关卡完成度 (40%)
        level_completion = sum(l.completion_percentage for l in levels) / len(levels) if levels else 0
        health_score += level_completion * 0.4
        
        # 总体进度 (30%)
        health_score += progress * 0.3
        
        # 确定状态
        if health_score >= 80:
            return ProjectHealthStatus.EXCELLENT
        elif health_score >= 60:
            return ProjectHealthStatus.GOOD
        elif health_score >= 40:
            return ProjectHealthStatus.WARNING
        else:
            return ProjectHealthStatus.CRITICAL
    
    def get_pending_tasks(self) -> List[str]:
        """获取待完成任务列表"""
        tasks = []
        
        # 检查缺失的关卡
        levels = self.check_levels()
        for level in levels:
            if not level.exists:
                tasks.append(f"创建关卡: {level.name}")
            elif level.completion_percentage < 100:
                tasks.append(f"完善关卡: {level.name} ({level.completion_percentage:.0f}%)")
        
        # 检查缺失的目录
        structure = self.check_project_structure()
        for missing_dir in structure["missing_dirs"]:
            tasks.append(f"创建目录: {missing_dir}")
        
        # 检查里程碑
        milestones = self.check_milestones()
        for milestone in milestones:
            if milestone.percentage < 100:
                tasks.append(f"完成里程碑: {milestone.name} ({milestone.percentage:.0f}%)")
        
        return tasks
    
    def generate_full_report(self) -> str:
        """生成完整报告"""
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        health = self.get_health_status()
        progress = self.calculate_overall_progress()
        
        report = f"""# ProjectMonitor 项目监控报告

**生成时间**: {report_time}
**项目**: {PROJECT_CONFIG["name"]} v{PROJECT_CONFIG["version"]}

## 📊 总体状态

- **健康状态**: {health.value}
- **总体进度**: {progress:.1f}%
- **项目路径**: `{PROJECT_CONFIG["root_path"]}`

## 🗺️ 关卡状态

| 关卡 | 状态 | 建筑数 | 完成度 | 问题 |
|------|------|--------|--------|------|
"""
        
        levels = self.check_levels()
        for level in levels:
            status_icon = "✅" if level.exists else "❌"
            issues_text = "; ".join(level.issues) if level.issues else "无"
            report += f"| {level.name} | {status_icon} | {level.building_count} | {level.completion_percentage:.0f}% | {issues_text} |\n"
        
        report += """
## 📦 资源统计

"""
        
        stats = self.get_asset_statistics()
        report += f"""### 总体统计

- **静态网格**: {stats.total_static_meshes}
- **材质**: {stats.total_materials}
- **纹理**: {stats.total_textures}
- **蓝图**: {stats.total_blueprints}

### 分类统计

- **场景建筑**: {stats.scene_buildings}
- **方块碎块**: {stats.block_pieces}
- **武器部件**: {stats.weapon_parts}

### 按关卡分布

"""
        for level, count in stats.by_level.items():
            bar = "█" * (count // 2) + "░" * (10 - count // 2)
            report += f"- **{level}**: {bar} ({count})\n"
        
        report += """
## 🎯 里程碑进度

"""
        
        milestones = self.check_milestones()
        for milestone in milestones:
            bar_length = 20
            filled = int(milestone.percentage / 100 * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            report += f"""### {milestone.name}
- **进度**: {bar} {milestone.percentage:.1f}%
- **任务**: {milestone.completed_tasks}/{milestone.total_tasks}
- **状态**: {milestone.status}
- **权重**: {milestone.weight}%

"""
        
        report += """## 📋 待完成任务

"""
        
        pending = self.get_pending_tasks()
        if pending:
            for i, task in enumerate(pending[:20], 1):  # 只显示前20个
                report += f"{i}. {task}\n"
            if len(pending) > 20:
                report += f"\n... 还有 {len(pending) - 20} 个任务\n"
        else:
            report += "✅ 所有任务已完成！\n"
        
        report += """
## 📁 项目结构

"""
        
        structure = self.check_project_structure()
        report += f"""- **健康分数**: {structure['health_score']:.1f}%
- **存在目录**: {len(structure['existing_dirs'])}
- **缺失目录**: {len(structure['missing_dirs'])}

### 缺失目录

"""
        if structure['missing_dirs']:
            for dir_path in structure['missing_dirs']:
                report += f"- ❌ `{dir_path}`\n"
        else:
            report += "✅ 所有必需目录都存在\n"
        
        report += """
## 📝 日志

```
"""
        for log in self.logs[-50:]:  # 只显示最后50条
            report += f"{log}\n"
        report += """```

---

*报告由 ProjectMonitor 技能生成*
"""
        
        return report
    
    def save_report(self, filename: str = None):
        """保存报告"""
        if filename is None:
            filename = f"project_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_path = os.path.join("/python/logs", filename)
        os.makedirs("/python/logs", exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_full_report())
        
        self._log(f"报告已保存: {report_path}")
        return report_path
    
    def check_and_notify(self):
        """检查并提醒"""
        health = self.get_health_status()
        pending = self.get_pending_tasks()
        
        self._log(f"项目健康状态: {health.value}")
        
        if health == ProjectHealthStatus.CRITICAL:
            self._log("⚠️ 项目健康状态严重，需要立即处理！", "WARNING")
            if pending:
                self._log(f"有 {len(pending)} 个待完成任务", "WARNING")
        elif health == ProjectHealthStatus.WARNING:
            self._log("⚠️ 项目健康状态警告，建议检查", "WARNING")
        elif health == ProjectHealthStatus.GOOD:
            self._log("✅ 项目健康状态良好")
        else:
            self._log("✨ 项目健康状态优秀！")
        
        return {
            "health": health,
            "pending_count": len(pending),
            "top_tasks": pending[:5]
        }

# ============================================================================
# 快捷函数
# ============================================================================

_project_monitor = None

def get_project_monitor() -> ProjectMonitorSkill:
    """获取ProjectMonitor实例"""
    global _project_monitor
    if _project_monitor is None:
        _project_monitor = ProjectMonitorSkill()
    return _project_monitor

def check_project_status():
    """检查项目状态"""
    monitor = get_project_monitor()
    return monitor.check_and_notify()

def get_project_report():
    """获取项目报告"""
    monitor = get_project_monitor()
    return monitor.generate_full_report()

def save_project_report():
    """保存项目报告"""
    monitor = get_project_monitor()
    return monitor.save_report()

def check_levels_status():
    """检查关卡状态"""
    monitor = get_project_monitor()
    return monitor.check_levels()

def get_asset_stats():
    """获取资源统计"""
    monitor = get_project_monitor()
    return monitor.get_asset_statistics()

def get_pending_tasks_list():
    """获取待完成任务列表"""
    monitor = get_project_monitor()
    return monitor.get_pending_tasks()

# ============================================================================
# 使用示例
# ============================================================================

# 在UE Python控制台中:
# import project_monitor_skill
# status = project_monitor_skill.check_project_status()
# report = project_monitor_skill.get_project_report()
# project_monitor_skill.save_project_report()
# levels = project_monitor_skill.check_levels_status()
# stats = project_monitor_skill.get_asset_stats()
# tasks = project_monitor_skill.get_pending_tasks_list()

if __name__ == "__main__":
    monitor = get_project_monitor()
    monitor.check_and_notify()
    monitor.save_report()
