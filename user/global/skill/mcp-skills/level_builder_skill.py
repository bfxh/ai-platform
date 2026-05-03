#!/usr/bin/env python3
"""
BlockWeaponArena - LevelBuilder 技能
自动化关卡场景搭建系统

功能:
1. 根据配置自动放置建筑模型
2. 设置光照和氛围
3. 配置玩家出生点
4. 应用场景特效
5. 批量构建多个关卡

作者: AI Assistant
版本: 1.0
日期: 2026-03-31
"""

import unreal
import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# ============================================================================
# 配置
# ============================================================================

LEVEL_CONFIG = {
    "OpenPlains": {
        "map_name": "Map_OpenPlains",
        "theme": "开阔平原",
        "lighting": "Daylight",
        "sky": "Clear",
        "fog_density": 0.1,
        "player_start_positions": [
            {"x": -5000, "y": 0, "z": 100},
            {"x": 5000, "y": 0, "z": 100}
        ],
        "required_actors": [
            "DirectionalLight",
            "SkyAtmosphere",
            "PostProcessVolume"
        ],
        "building_categories": ["Rock", "Cover", "Grass"]
    },
    "NarrowDungeon": {
        "map_name": "Map_NarrowDungeon",
        "theme": "狭窄地牢",
        "lighting": "Dim",
        "sky": "None",
        "fog_density": 0.3,
        "player_start_positions": [
            {"x": -2000, "y": 0, "z": 100},
            {"x": 2000, "y": 0, "z": 100}
        ],
        "required_actors": [
            "DirectionalLight",
            "PostProcessVolume",
            "PointLight"
        ],
        "building_categories": ["Wall", "Corner", "Door", "Pillar"]
    },
    "MountainForest": {
        "map_name": "Map_MountainForest",
        "theme": "山林高低差",
        "lighting": "Daylight",
        "sky": "Cloudy",
        "fog_density": 0.2,
        "player_start_positions": [
            {"x": -3000, "y": -1000, "z": 500},
            {"x": 3000, "y": 1000, "z": 500}
        ],
        "required_actors": [
            "DirectionalLight",
            "SkyAtmosphere",
            "PostProcessVolume"
        ],
        "building_categories": ["Tree", "Rock", "Platform", "Ramp"]
    },
    "Ruins": {
        "map_name": "Map_Ruins",
        "theme": "废墟",
        "lighting": "Sunset",
        "sky": "Overcast",
        "fog_density": 0.15,
        "player_start_positions": [
            {"x": -2500, "y": 0, "z": 100},
            {"x": 2500, "y": 0, "z": 100}
        ],
        "required_actors": [
            "DirectionalLight",
            "SkyAtmosphere",
            "PostProcessVolume"
        ],
        "building_categories": ["WallBroken", "PillarBroken", "Debris", "Ruin"]
    },
    "WeaponWorkshop": {
        "map_name": "Map_WeaponWorkshop",
        "theme": "武器工坊",
        "lighting": "Indoor",
        "sky": "None",
        "fog_density": 0.05,
        "player_start_positions": [
            {"x": -1500, "y": 0, "z": 100},
            {"x": 1500, "y": 0, "z": 100}
        ],
        "required_actors": [
            "DirectionalLight",
            "PostProcessVolume",
            "PointLight"
        ],
        "building_categories": ["Floor", "Pillar", "Machine", "Table"]
    },
    "TrajectoryTest": {
        "map_name": "Map_TrajectoryTest",
        "theme": "轨迹测试场",
        "lighting": "Studio",
        "sky": "None",
        "fog_density": 0.0,
        "player_start_positions": [
            {"x": 0, "y": -2000, "z": 100},
            {"x": 0, "y": 2000, "z": 100}
        ],
        "required_actors": [
            "DirectionalLight",
            "PostProcessVolume"
        ],
        "building_categories": ["Floor", "Target", "Marker"]
    },
    "TrainingGround": {
        "map_name": "Map_TrainingGround",
        "theme": "训练场",
        "lighting": "Daylight",
        "sky": "Clear",
        "fog_density": 0.1,
        "player_start_positions": [
            {"x": -1000, "y": 0, "z": 100},
            {"x": 1000, "y": 0, "z": 100}
        ],
        "required_actors": [
            "DirectionalLight",
            "SkyAtmosphere",
            "PostProcessVolume"
        ],
        "building_categories": ["Table", "Target", "Sign"]
    }
}

# ============================================================================
# LevelBuilder 技能类
# ============================================================================

class LevelBuilderSkill:
    """关卡构建技能"""
    
    def __init__(self):
        self.editor_level_lib = unreal.EditorLevelLibrary
        self.asset_lib = unreal.EditorAssetLibrary
        self.level_lib = unreal.LevelLibrary
        self.logs = []
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        
        if level == "ERROR":
            unreal.log_error(f"[LevelBuilder] {message}")
        elif level == "WARNING":
            unreal.log_warning(f"[LevelBuilder] {message}")
        else:
            unreal.log(f"[LevelBuilder] {message}")
    
    def get_level_config(self, level_name: str) -> Dict:
        """获取关卡配置"""
        return LEVEL_CONFIG.get(level_name, {})
    
    def create_or_open_level(self, level_name: str) -> bool:
        """创建或打开关卡"""
        config = self.get_level_config(level_name)
        if not config:
            self._log(f"未找到关卡配置: {level_name}", "ERROR")
            return False
        
        map_name = config["map_name"]
        map_path = f"/Game/Maps/{map_name}"
        
        # 检查关卡是否存在
        if self.asset_lib.does_asset_exist(map_path):
            self._log(f"打开现有关卡: {map_name}")
            # 打开关卡
            unreal.EditorLoadingAndSavingUtils.load_map(map_path)
        else:
            self._log(f"创建新关卡: {map_name}")
            # 创建新关卡
            new_level = self.editor_level_lib.new_level(map_path)
            if not new_level:
                self._log(f"创建关卡失败: {map_name}", "ERROR")
                return False
        
        return True
    
    def setup_lighting(self, level_name: str) -> bool:
        """设置光照"""
        config = self.get_level_config(level_name)
        lighting_type = config.get("lighting", "Daylight")
        
        self._log(f"设置光照: {lighting_type}")
        
        # 删除现有光源
        existing_lights = self.editor_level_lib.get_all_level_actors()
        for actor in existing_lights:
            if isinstance(actor, (unreal.DirectionalLight, unreal.SkyLight)):
                actor.destroy_actor()
        
        # 创建主光源
        if lighting_type in ["Daylight", "Sunset", "Studio"]:
            # 创建方向光
            light_location = unreal.Vector(0, 0, 1000)
            light_rotation = unreal.Rotator(-45, 0, 0)
            
            directional_light = self.editor_level_lib.spawn_actor_from_class(
                unreal.DirectionalLight,
                light_location,
                light_rotation
            )
            
            if directional_light:
                # 设置光照强度
                light_component = directional_light.directional_light_component
                if lighting_type == "Daylight":
                    light_component.set_intensity(10.0)
                elif lighting_type == "Sunset":
                    light_component.set_intensity(5.0)
                    light_component.set_light_color(unreal.LinearColor(1.0, 0.6, 0.3))
                elif lighting_type == "Studio":
                    light_component.set_intensity(8.0)
        
        # 创建天光
        if config.get("sky") != "None":
            sky_light = self.editor_level_lib.spawn_actor_from_class(
                unreal.SkyLight,
                unreal.Vector(0, 0, 500)
            )
            if sky_light:
                sky_light.get_editor_property('light_component').set_intensity(1.0)
        
        # 创建天空氛围
        if config.get("sky") in ["Clear", "Cloudy", "Overcast"]:
            sky_atmosphere = self.editor_level_lib.spawn_actor_from_class(
                unreal.SkyAtmosphere,
                unreal.Vector(0, 0, 0)
            )
        
        return True
    
    def setup_post_process(self, level_name: str) -> bool:
        """设置后期处理"""
        config = self.get_level_config(level_name)
        
        self._log("设置后期处理")
        
        # 创建后期处理体积
        pp_volume = self.editor_level_lib.spawn_actor_from_class(
            unreal.PostProcessVolume,
            unreal.Vector(0, 0, 500)
        )
        
        if pp_volume:
            # 设置为无限范围
            pp_volume.set_editor_property("bUnbound", True)
            
            # 获取设置
            settings = pp_volume.get_editor_property("settings")
            
            # 设置Bloom
            settings.set_editor_property("bOverride_BloomIntensity", True)
            settings.set_editor_property("bloom_intensity", 0.5)
            
            # 设置环境光遮蔽
            settings.set_editor_property("bOverride_AmbientOcclusionIntensity", True)
            settings.set_editor_property("ambient_occlusion_intensity", 0.5)
            
            # 设置雾
            fog_density = config.get("fog_density", 0.1)
            if fog_density > 0:
                settings.set_editor_property("bOverride_FogDensity", True)
                # 注意：实际雾设置需要在ExponentialHeightFog中
        
        # 创建指数高度雾
        if config.get("fog_density", 0) > 0:
            fog_actor = self.editor_level_lib.spawn_actor_from_class(
                unreal.ExponentialHeightFog,
                unreal.Vector(0, 0, -100)
            )
            if fog_actor:
                fog_component = fog_actor.get_editor_property("fog_component")
                fog_component.set_editor_property("fog_density", config["fog_density"])
        
        return True
    
    def place_player_starts(self, level_name: str) -> bool:
        """放置玩家出生点"""
        config = self.get_level_config(level_name)
        positions = config.get("player_start_positions", [])
        
        self._log(f"放置 {len(positions)} 个玩家出生点")
        
        # 删除现有出生点
        existing_actors = self.editor_level_lib.get_all_level_actors()
        for actor in existing_actors:
            if isinstance(actor, unreal.PlayerStart):
                actor.destroy_actor()
        
        # 创建新的出生点
        for i, pos in enumerate(positions):
            location = unreal.Vector(pos["x"], pos["y"], pos["z"])
            
            # 计算朝向（朝向对方）
            if i == 0 and len(positions) > 1:
                target = positions[1]
                rotation = unreal.Rotator(0, self._calculate_yaw(pos, target), 0)
            elif i == 1:
                target = positions[0]
                rotation = unreal.Rotator(0, self._calculate_yaw(pos, target), 0)
            else:
                rotation = unreal.Rotator(0, 0, 0)
            
            player_start = self.editor_level_lib.spawn_actor_from_class(
                unreal.PlayerStart,
                location,
                rotation
            )
            
            if player_start:
                player_start.set_actor_label(f"PlayerStart_{i+1}")
        
        return True
    
    def _calculate_yaw(self, from_pos: Dict, to_pos: Dict) -> float:
        """计算朝向角度"""
        import math
        dx = to_pos["x"] - from_pos["x"]
        dy = to_pos["y"] - from_pos["y"]
        yaw = math.atan2(dy, dx) * 180 / math.pi
        return yaw
    
    def place_building_models(self, level_name: str) -> bool:
        """放置建筑模型"""
        config = self.get_level_config(level_name)
        categories = config.get("building_categories", [])
        
        self._log(f"放置建筑模型，类别: {categories}")
        
        # 获取该关卡的建筑模型路径
        mesh_path = f"/Game/Meshes/SceneBuildings/{level_name}"
        
        # 检查路径是否存在
        if not self.asset_lib.does_directory_exist(mesh_path):
            self._log(f"建筑模型目录不存在: {mesh_path}", "WARNING")
            return False
        
        # 获取所有静态网格
        asset_paths = self.asset_lib.list_assets(mesh_path, recursive=True)
        
        placed_count = 0
        for asset_path in asset_paths:
            # 只处理静态网格
            if "StaticMesh" in asset_path:
                mesh = self.asset_lib.load_asset(asset_path)
                if mesh:
                    # 计算放置位置（这里使用简单网格布局）
                    x = (placed_count % 5) * 500 - 1000
                    y = (placed_count // 5) * 500 - 1000
                    location = unreal.Vector(x, y, 0)
                    
                    # 放置Actor
                    actor = self.editor_level_lib.spawn_actor_from_object(
                        mesh,
                        location
                    )
                    
                    if actor:
                        actor.set_actor_label(f"Building_{placed_count}")
                        placed_count += 1
        
        self._log(f"放置了 {placed_count} 个建筑模型")
        return True
    
    def build_level(self, level_name: str, quick_mode: bool = False) -> bool:
        """
        构建单个关卡
        
        Args:
            level_name: 关卡名（如"Ruins", "MountainForest"）
            quick_mode: 快速模式（跳过建筑模型放置）
        """
        self._log(f"=" * 70)
        self._log(f"开始构建关卡: {level_name}")
        self._log(f"=" * 70)
        
        # 1. 创建/打开关卡
        if not self.create_or_open_level(level_name):
            return False
        
        # 2. 设置光照
        self.setup_lighting(level_name)
        
        # 3. 设置后期处理
        self.setup_post_process(level_name)
        
        # 4. 放置玩家出生点
        self.place_player_starts(level_name)
        
        # 5. 放置建筑模型（非快速模式）
        if not quick_mode:
            self.place_building_models(level_name)
        
        # 6. 保存关卡
        unreal.EditorLoadingAndSavingUtils.save_current_level()
        
        self._log(f"✅ 关卡构建完成: {level_name}")
        return True
    
    def build_all_levels(self, quick_mode: bool = False) -> Dict:
        """构建所有关卡"""
        results = {
            "success": [],
            "failed": []
        }
        
        self._log("=" * 70)
        self._log("开始构建所有关卡")
        self._log("=" * 70)
        
        for level_name in LEVEL_CONFIG.keys():
            success = self.build_level(level_name, quick_mode)
            if success:
                results["success"].append(level_name)
            else:
                results["failed"].append(level_name)
        
        self._log(f"\n构建完成统计:")
        self._log(f"- 成功: {len(results['success'])}")
        self._log(f"- 失败: {len(results['failed'])}")
        
        return results
    
    def get_build_report(self) -> str:
        """生成构建报告"""
        report = f"""# LevelBuilder 构建报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 日志

```
"""
        for log in self.logs:
            report += f"{log}\n"
        
        report += """```

## 关卡配置

"""
        for level_name, config in LEVEL_CONFIG.items():
            report += f"""### {level_name}
- **地图名**: {config['map_name']}
- **主题**: {config['theme']}
- **光照**: {config['lighting']}
- **天空**: {config['sky']}
- **雾密度**: {config['fog_density']}
- **建筑类别**: {', '.join(config['building_categories'])}

"""
        
        return report
    
    def save_report(self, filename: str = None):
        """保存报告"""
        if filename is None:
            filename = f"levelbuilder_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_path = os.path.join("/python/logs", filename)
        os.makedirs("/python/logs", exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.get_build_report())
        
        self._log(f"报告已保存: {report_path}")
        return report_path

# ============================================================================
# 快捷函数
# ============================================================================

_level_builder = None

def get_level_builder() -> LevelBuilderSkill:
    """获取LevelBuilder实例"""
    global _level_builder
    if _level_builder is None:
        _level_builder = LevelBuilderSkill()
    return _level_builder

def build_level(level_name: str, quick_mode: bool = False):
    """构建单个关卡"""
    builder = get_level_builder()
    return builder.build_level(level_name, quick_mode)

def build_all_levels(quick_mode: bool = False):
    """构建所有关卡"""
    builder = get_level_builder()
    results = builder.build_all_levels(quick_mode)
    builder.save_report()
    return results

def get_level_report():
    """获取构建报告"""
    builder = get_level_builder()
    return builder.get_build_report()

# ============================================================================
# 使用示例
# ============================================================================

# 在UE Python控制台中:
# import level_builder_skill
# level_builder_skill.build_level("Ruins")           # 构建单个关卡
# level_builder_skill.build_all_levels()             # 构建所有关卡
# level_builder_skill.build_all_levels(quick_mode=True)  # 快速模式
# print(level_builder_skill.get_level_report())      # 获取报告

if __name__ == "__main__":
    build_all_levels()
