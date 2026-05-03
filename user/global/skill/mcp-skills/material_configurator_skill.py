#!/usr/bin/env python3
"""
BlockWeaponArena - MaterialConfigurator 技能
自动材质配置系统

功能:
1. 识别模型材质类型
2. 自动应用对应材质模板
3. 批量处理材质
4. 材质参数调整
5. 生成材质报告

作者: AI Assistant
版本: 1.0
日期: 2026-03-31
"""

import unreal
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# ============================================================================
# 材质类型枚举
# ============================================================================

class MaterialType(Enum):
    IRON = "Iron"
    STEEL = "Steel"
    WOOD = "Wood"
    STONE = "Stone"
    CRYSTAL = "Crystal"
    FIRE = "Fire"
    ICE = "Ice"
    METAL = "Metal"
    CONCRETE = "Concrete"
    BRICK = "Brick"
    GRASS = "Grass"
    SAND = "Sand"
    WATER = "Water"
    GLASS = "Glass"
    UNKNOWN = "Unknown"

# ============================================================================
# 材质配置
# ============================================================================

MATERIAL_TEMPLATES = {
    MaterialType.IRON: {
        "base_color": "/Game/Textures/T_Iron_BC",
        "normal": "/Game/Textures/T_Iron_N",
        "roughness": "/Game/Textures/T_Iron_R",
        "metallic": 1.0,
        "roughness_value": 0.4,
        "specular": 0.5
    },
    MaterialType.STEEL: {
        "base_color": "/Game/Textures/T_Steel_BC",
        "normal": "/Game/Textures/T_Steel_N",
        "roughness": "/Game/Textures/T_Steel_R",
        "metallic": 1.0,
        "roughness_value": 0.3,
        "specular": 0.6
    },
    MaterialType.WOOD: {
        "base_color": "/Game/Textures/T_Wood_BC",
        "normal": "/Game/Textures/T_Wood_N",
        "roughness": "/Game/Textures/T_Wood_R",
        "metallic": 0.0,
        "roughness_value": 0.7,
        "specular": 0.1
    },
    MaterialType.STONE: {
        "base_color": "/Game/Textures/T_Stone_BC",
        "normal": "/Game/Textures/T_Stone_N",
        "roughness": "/Game/Textures/T_Stone_R",
        "metallic": 0.0,
        "roughness_value": 0.9,
        "specular": 0.2
    },
    MaterialType.CRYSTAL: {
        "base_color": "/Game/Textures/T_Crystal_BC",
        "normal": "/Game/Textures/T_Crystal_N",
        "roughness": "/Game/Textures/T_Crystal_R",
        "metallic": 0.0,
        "roughness_value": 0.1,
        "specular": 1.0,
        "translucency": True
    },
    MaterialType.FIRE: {
        "base_color": "/Game/Textures/T_Fire_BC",
        "emissive": "/Game/Textures/T_Fire_E",
        "metallic": 0.0,
        "roughness_value": 0.5,
        "emissive_intensity": 5.0
    },
    MaterialType.ICE: {
        "base_color": "/Game/Textures/T_Ice_BC",
        "normal": "/Game/Textures/T_Ice_N",
        "roughness": "/Game/Textures/T_Ice_R",
        "metallic": 0.0,
        "roughness_value": 0.05,
        "specular": 0.9,
        "translucency": True
    },
    MaterialType.METAL: {
        "base_color": "/Game/Textures/T_Metal_BC",
        "normal": "/Game/Textures/T_Metal_N",
        "roughness": "/Game/Textures/T_Metal_R",
        "metallic": 1.0,
        "roughness_value": 0.35,
        "specular": 0.5
    },
    MaterialType.CONCRETE: {
        "base_color": "/Game/Textures/T_Concrete_BC",
        "normal": "/Game/Textures/T_Concrete_N",
        "roughness": "/Game/Textures/T_Concrete_R",
        "metallic": 0.0,
        "roughness_value": 0.85,
        "specular": 0.1
    },
    MaterialType.BRICK: {
        "base_color": "/Game/Textures/T_Brick_BC",
        "normal": "/Game/Textures/T_Brick_N",
        "roughness": "/Game/Textures/T_Brick_R",
        "metallic": 0.0,
        "roughness_value": 0.8,
        "specular": 0.15
    }
}

# 材质检测关键词
MATERIAL_KEYWORDS = {
    MaterialType.IRON: ["iron", "铁"],
    MaterialType.STEEL: ["steel", "钢"],
    MaterialType.WOOD: ["wood", "木"],
    MaterialType.STONE: ["stone", "rock", "石", "岩"],
    MaterialType.CRYSTAL: ["crystal", "水晶", "晶体"],
    MaterialType.FIRE: ["fire", "火"],
    MaterialType.ICE: ["ice", "冰"],
    MaterialType.METAL: ["metal", "金属"],
    MaterialType.CONCRETE: ["concrete", "混凝土"],
    MaterialType.BRICK: ["brick", "砖"],
    MaterialType.GRASS: ["grass", "草"],
    MaterialType.SAND: ["sand", "沙"],
    MaterialType.WATER: ["water", "水"],
    MaterialType.GLASS: ["glass", "玻璃"]
}

# ============================================================================
# MaterialConfigurator 技能类
# ============================================================================

class MaterialConfiguratorSkill:
    """材质配置技能"""
    
    def __init__(self):
        self.asset_lib = unreal.EditorAssetLibrary
        self.material_lib = unreal.EditorMaterialLibrary
        self.logs = []
        self.configured_count = 0
        self.failed_count = 0
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        
        if level == "ERROR":
            unreal.log_error(f"[MaterialConfigurator] {message}")
        elif level == "WARNING":
            unreal.log_warning(f"[MaterialConfigurator] {message}")
        else:
            unreal.log(f"[MaterialConfigurator] {message}")
    
    def detect_material_type(self, mesh_name: str, material_name: str = "") -> MaterialType:
        """
        检测材质类型
        
        Args:
            mesh_name: 网格名称
            material_name: 材质名称（可选）
        """
        search_text = f"{mesh_name} {material_name}".lower()
        
        for mat_type, keywords in MATERIAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in search_text:
                    return mat_type
        
        return MaterialType.UNKNOWN
    
    def get_or_create_material(self, material_type: MaterialType, material_name: str = None) -> Optional[unreal.Material]:
        """
        获取或创建材质
        
        Args:
            material_type: 材质类型
            material_name: 材质名称（可选）
        """
        if material_type == MaterialType.UNKNOWN:
            return None
        
        # 检查材质模板是否存在
        template_path = f"/Game/Materials/M_{material_type.value}"
        
        if self.asset_lib.does_asset_exist(template_path):
            return self.asset_lib.load_asset(template_path)
        
        # 创建新材质
        if material_name is None:
            material_name = f"M_{material_type.value}_{datetime.now().strftime('%H%M%S')}"
        
        self._log(f"创建新材质: {material_name}")
        
        # 创建材质工厂
        factory = unreal.MaterialFactoryNew()
        material = self.asset_lib.create_asset(
            material_name,
            "/Game/Materials/AutoGenerated",
            unreal.Material,
            factory
        )
        
        if material:
            self._configure_material(material, material_type)
        
        return material
    
    def _configure_material(self, material: unreal.Material, material_type: MaterialType):
        """配置材质参数"""
        config = MATERIAL_TEMPLATES.get(material_type, {})
        
        if not config:
            return
        
        # 设置基础颜色
        if "base_color" in config:
            texture_path = config["base_color"]
            if self.asset_lib.does_asset_exist(texture_path):
                texture = self.asset_lib.load_asset(texture_path)
                if texture:
                    # 创建纹理采样节点并连接到基础颜色
                    # 注意：这里简化处理，实际需要在材质图中创建节点
                    pass
        
        # 设置金属度
        if "metallic" in config:
            material.set_editor_property("metallic", config["metallic"])
        
        # 设置粗糙度
        if "roughness_value" in config:
            material.set_editor_property("roughness", config["roughness_value"])
        
        # 设置高光
        if "specular" in config:
            material.set_editor_property("specular", config["specular"])
        
        # 设置自发光
        if "emissive_intensity" in config:
            material.set_editor_property("emissive_color", unreal.LinearColor(1, 1, 1))
            # 注意：自发光强度需要在材质节点中设置
        
        # 设置半透明
        if config.get("translucency", False):
            material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        
        # 保存材质
        self.asset_lib.save_loaded_asset(material)
    
    def configure_static_mesh_materials(self, mesh_path: str, auto_create: bool = True) -> bool:
        """
        配置静态网格材质
        
        Args:
            mesh_path: 静态网格路径
            auto_create: 是否自动创建缺失的材质
        """
        try:
            mesh = self.asset_lib.load_asset(mesh_path)
            if not mesh:
                self._log(f"无法加载网格: {mesh_path}", "ERROR")
                return False
            
            mesh_name = mesh_path.split("/")[-1]
            self._log(f"配置材质: {mesh_name}")
            
            # 获取材质槽数量
            num_sections = mesh.get_num_sections(0)
            
            for section_idx in range(num_sections):
                # 获取当前材质
                current_material = mesh.get_material(section_idx)
                
                if current_material:
                    material_name = current_material.get_name()
                else:
                    material_name = ""
                
                # 检测材质类型
                mat_type = self.detect_material_type(mesh_name, material_name)
                
                if mat_type != MaterialType.UNKNOWN:
                    # 获取或创建材质
                    new_material = self.get_or_create_material(mat_type, material_name)
                    
                    if new_material:
                        # 应用材质
                        mesh.set_material(section_idx, new_material)
                        self._log(f"  应用材质 [{section_idx}]: {mat_type.value}")
                    else:
                        self._log(f"  无法创建材质: {mat_type.value}", "WARNING")
                else:
                    self._log(f"  未识别材质类型 [{section_idx}]: {material_name}", "WARNING")
            
            # 保存网格
            self.asset_lib.save_loaded_asset(mesh)
            self.configured_count += 1
            
            return True
            
        except Exception as e:
            self._log(f"配置失败 {mesh_path}: {str(e)}", "ERROR")
            self.failed_count += 1
            return False
    
    def batch_configure_directory(self, directory: str, recursive: bool = True) -> Dict:
        """
        批量配置目录中的所有静态网格
        
        Args:
            directory: 目录路径
            recursive: 是否递归子目录
        """
        results = {
            "success": [],
            "failed": [],
            "skipped": []
        }
        
        self._log(f"批量配置目录: {directory}")
        
        # 获取所有静态网格
        asset_paths = self.asset_lib.list_assets(directory, recursive=recursive)
        
        static_meshes = [path for path in asset_paths if "StaticMesh" in path]
        
        self._log(f"找到 {len(static_meshes)} 个静态网格")
        
        for mesh_path in static_meshes:
            success = self.configure_static_mesh_materials(mesh_path)
            
            mesh_name = mesh_path.split("/")[-1]
            if success:
                results["success"].append(mesh_name)
            else:
                results["failed"].append(mesh_name)
        
        self._log(f"\n批量配置完成:")
        self._log(f"- 成功: {len(results['success'])}")
        self._log(f"- 失败: {len(results['failed'])}")
        
        return results
    
    def configure_level_materials(self, level_name: str) -> Dict:
        """配置关卡中所有模型的材质"""
        directory = f"/Game/Meshes/SceneBuildings/{level_name}"
        return self.batch_configure_directory(directory)
    
    def create_material_preset(self, preset_name: str, material_type: MaterialType, 
                               custom_params: Dict = None) -> Optional[unreal.Material]:
        """
        创建材质预设
        
        Args:
            preset_name: 预设名称
            material_type: 材质类型
            custom_params: 自定义参数
        """
        material = self.get_or_create_material(material_type, preset_name)
        
        if material and custom_params:
            # 应用自定义参数
            for param, value in custom_params.items():
                if hasattr(material, param):
                    setattr(material, param, value)
            
            self.asset_lib.save_loaded_asset(material)
        
        return material
    
    def get_configuration_report(self) -> str:
        """生成配置报告"""
        report = f"""# MaterialConfigurator 配置报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计信息

- **配置成功**: {self.configured_count}
- **配置失败**: {self.failed_count}
- **总计**: {self.configured_count + self.failed_count}

## 支持的材质类型

"""
        for mat_type in MaterialType:
            if mat_type != MaterialType.UNKNOWN:
                keywords = MATERIAL_KEYWORDS.get(mat_type, [])
                report += f"- **{mat_type.value}**: {', '.join(keywords)}\n"
        
        report += """
## 日志

```
"""
        for log in self.logs:
            report += f"{log}\n"
        
        report += """```

"""
        
        return report
    
    def save_report(self, filename: str = None):
        """保存报告"""
        if filename is None:
            filename = f"material_configurator_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_path = os.path.join("/python/logs", filename)
        os.makedirs("/python/logs", exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.get_configuration_report())
        
        self._log(f"报告已保存: {report_path}")
        return report_path

# ============================================================================
# 快捷函数
# ============================================================================

_material_configurator = None

def get_material_configurator() -> MaterialConfiguratorSkill:
    """获取MaterialConfigurator实例"""
    global _material_configurator
    if _material_configurator is None:
        _material_configurator = MaterialConfiguratorSkill()
    return _material_configurator

def configure_mesh_materials(mesh_path: str):
    """配置单个网格材质"""
    configurator = get_material_configurator()
    return configurator.configure_static_mesh_materials(mesh_path)

def configure_directory_materials(directory: str, recursive: bool = True):
    """批量配置目录材质"""
    configurator = get_material_configurator()
    results = configurator.batch_configure_directory(directory, recursive)
    configurator.save_report()
    return results

def configure_level_materials(level_name: str):
    """配置关卡材质"""
    configurator = get_material_configurator()
    results = configurator.configure_level_materials(level_name)
    configurator.save_report()
    return results

def get_material_report():
    """获取配置报告"""
    configurator = get_material_configurator()
    return configurator.get_configuration_report()

# ============================================================================
# 使用示例
# ============================================================================

# 在UE Python控制台中:
# import material_configurator_skill
# material_configurator_skill.configure_mesh_materials("/Game/Meshes/SceneBuildings/Ruins/SM_Scene_Ruins_Wall_01")
# material_configurator_skill.configure_directory_materials("/Game/Meshes/SceneBuildings")
# material_configurator_skill.configure_level_materials("Ruins")
# print(material_configurator_skill.get_material_report())

if __name__ == "__main__":
    configure_directory_materials("/Game/Meshes/SceneBuildings")
