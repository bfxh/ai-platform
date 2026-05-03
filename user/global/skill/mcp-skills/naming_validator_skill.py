#!/usr/bin/env python3
"""
BlockWeaponArena - NamingValidator 技能
模型命名规范检查系统

功能:
1. 检查FBX文件名格式
2. 检查内部命名
3. 生成检查报告
4. 自动修复（可选）
5. 批量检查目录

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
# 命名规范配置
# ============================================================================

NAMING_RULES = {
    "scene_building": {
        "pattern": r"^SM_Scene_([A-Za-z]+)_([A-Za-z]+)_?(\d*)$",
        "example": "SM_Scene_Ruins_WallBroken_01",
        "description": "场景建筑模型",
        "required_parts": ["SM_Scene", "LevelName", "ElementType", "OptionalNumber"],
        "valid_levels": ["OpenPlains", "NarrowDungeon", "MountainForest", "Ruins", 
                        "WeaponWorkshop", "TrajectoryTest", "TrainingGround"],
        "valid_elements": ["Wall", "Floor", "Ceiling", "Pillar", "Door", "Window",
                          "Stairs", "Ramp", "Platform", "Rock", "Tree", "Ruin",
                          "Debris", "Machine", "Table", "Target", "Sign", "Cover",
                          "Grass", "Marker", "WallBroken", "PillarBroken", "Corner"]
    },
    "block_piece": {
        "pattern": r"^SM_BlockPiece_([A-Za-z]+)$",
        "example": "SM_BlockPiece_Cube",
        "description": "方块碎块模型",
        "required_parts": ["SM_BlockPiece", "Shape"],
        "valid_shapes": ["Cube", "Sphere", "Cylinder", "Cone", "Wedge", "Spike",
                        "Flat", "LShape", "TShape", "Cross", "Pyramid"]
    },
    "weapon_part": {
        "pattern": r"^SM_Weapon_([A-Za-z]+)$",
        "example": "SM_Weapon_Handle",
        "description": "武器部件模型",
        "required_parts": ["SM_Weapon", "PartType"],
        "valid_parts": ["Handle", "Blade", "HammerHead", "AxeHead", "SpearTip",
                       "Guard", "Shaft", "Pommel", "Crossguard"]
    },
    "material": {
        "pattern": r"^M_([A-Za-z]+)_?([A-Za-z]*)$",
        "example": "M_Stone_Wall",
        "description": "材质",
        "required_parts": ["M", "MaterialType", "OptionalDescription"],
        "valid_materials": ["Iron", "Steel", "Wood", "Stone", "Crystal", "Fire",
                           "Ice", "Metal", "Concrete", "Brick", "Grass", "Sand"]
    },
    "texture": {
        "pattern": r"^T_([A-Za-z]+)_([A-Za-z]+)_([A-Z]{2})$",
        "example": "T_Stone_Wall_BC",
        "description": "纹理",
        "required_parts": ["T", "MaterialType", "Description", "Suffix"],
        "valid_suffixes": ["BC", "N", "R", "M", "AO", "E", "ORM"]
    },
    "blueprint": {
        "pattern": r"^BP_([A-Za-z]+)_?([A-Za-z0-9]*)$",
        "example": "BP_BWA_Character",
        "description": "蓝图",
        "required_parts": ["BP", "Prefix", "Name"]
    }
}

# ============================================================================
# 验证结果类
# ============================================================================

class ValidationStatus(Enum):
    VALID = "有效"
    INVALID = "无效"
    WARNING = "警告"
    UNKNOWN = "未知"

@dataclass
class ValidationResult:
    """验证结果"""
    original_name: str
    asset_type: str
    status: ValidationStatus
    issues: List[str]
    suggestions: List[str]
    can_auto_fix: bool
    fixed_name: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "original_name": self.original_name,
            "asset_type": self.asset_type,
            "status": self.status.value,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "can_auto_fix": self.can_auto_fix,
            "fixed_name": self.fixed_name
        }

# ============================================================================
# NamingValidator 技能类
# ============================================================================

class NamingValidatorSkill:
    """命名验证技能"""
    
    def __init__(self):
        self.logs = []
        self.results: List[ValidationResult] = []
        self.valid_count = 0
        self.invalid_count = 0
        self.warning_count = 0
    
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        
        if level == "ERROR":
            unreal.log_error(f"[NamingValidator] {message}")
        elif level == "WARNING":
            unreal.log_warning(f"[NamingValidator] {message}")
        else:
            unreal.log(f"[NamingValidator] {message}")
    
    def detect_asset_type(self, name: str) -> str:
        """检测资源类型"""
        name_lower = name.lower()
        
        if name_lower.startswith("sm_scene"):
            return "scene_building"
        elif name_lower.startswith("sm_blockpiece"):
            return "block_piece"
        elif name_lower.startswith("sm_weapon"):
            return "weapon_part"
        elif name_lower.startswith("m_"):
            return "material"
        elif name_lower.startswith("t_"):
            return "texture"
        elif name_lower.startswith("bp_"):
            return "blueprint"
        elif name_lower.startswith("sm_"):
            return "static_mesh"
        else:
            return "unknown"
    
    def validate_name(self, name: str, asset_type: str = None) -> ValidationResult:
        """
        验证名称
        
        Args:
            name: 资源名称
            asset_type: 资源类型（可选，自动检测）
        """
        if asset_type is None:
            asset_type = self.detect_asset_type(name)
        
        issues = []
        suggestions = []
        can_auto_fix = False
        fixed_name = name
        
        # 检查基本规则
        if not name:
            issues.append("名称为空")
            return ValidationResult(name, asset_type, ValidationStatus.INVALID, 
                                  issues, suggestions, False)
        
        # 检查前缀
        if asset_type == "unknown":
            issues.append(f"无法识别资源类型: {name}")
            suggestions.append("使用标准前缀: SM_Scene_, SM_BlockPiece_, SM_Weapon_, M_, T_, BP_")
            return ValidationResult(name, asset_type, ValidationStatus.WARNING,
                                  issues, suggestions, False)
        
        # 获取规则
        rule = NAMING_RULES.get(asset_type)
        if not rule:
            issues.append(f"未找到规则: {asset_type}")
            return ValidationResult(name, asset_type, ValidationStatus.WARNING,
                                  issues, suggestions, False)
        
        # 检查正则匹配
        pattern = rule["pattern"]
        match = re.match(pattern, name)
        
        if not match:
            issues.append(f"不符合命名规范: {rule['example']}")
            suggestions.append(f"正确格式: {rule['example']}")
            
            # 尝试自动修复
            fixed = self._try_auto_fix(name, asset_type)
            if fixed and fixed != name:
                can_auto_fix = True
                fixed_name = fixed
                suggestions.append(f"建议修改为: {fixed}")
        else:
            # 检查特定规则
            groups = match.groups()
            
            if asset_type == "scene_building":
                level_name = groups[0] if len(groups) > 0 else ""
                element_type = groups[1] if len(groups) > 1 else ""
                
                valid_levels = rule.get("valid_levels", [])
                if level_name not in valid_levels:
                    issues.append(f"未知关卡名: {level_name}")
                    suggestions.append(f"有效关卡: {', '.join(valid_levels)}")
                
                valid_elements = rule.get("valid_elements", [])
                if element_type not in valid_elements:
                    issues.append(f"未知元素类型: {element_type}")
                    suggestions.append(f"有效元素: {', '.join(valid_elements[:10])}...")
            
            elif asset_type == "block_piece":
                shape = groups[0] if len(groups) > 0 else ""
                valid_shapes = rule.get("valid_shapes", [])
                if shape not in valid_shapes:
                    issues.append(f"未知形状: {shape}")
                    suggestions.append(f"有效形状: {', '.join(valid_shapes)}")
            
            elif asset_type == "weapon_part":
                part = groups[0] if len(groups) > 0 else ""
                valid_parts = rule.get("valid_parts", [])
                if part not in valid_parts:
                    issues.append(f"未知部件: {part}")
                    suggestions.append(f"有效部件: {', '.join(valid_parts)}")
        
        # 确定状态
        if issues:
            status = ValidationStatus.INVALID
        else:
            status = ValidationStatus.VALID
            self.valid_count += 1
        
        if issues and not can_auto_fix:
            self.invalid_count += 1
        elif issues:
            self.warning_count += 1
        
        return ValidationResult(name, asset_type, status, issues, suggestions, 
                              can_auto_fix, fixed_name)
    
    def _try_auto_fix(self, name: str, asset_type: str) -> str:
        """尝试自动修复名称"""
        fixed = name
        
        # 修复常见错误
        if asset_type == "scene_building":
            # 添加SM_Scene_前缀
            if not name.startswith("SM_Scene_"):
                if name.startswith("Scene_"):
                    fixed = "SM_" + name
                elif name.startswith("SM_"):
                    fixed = "SM_Scene_" + name[3:]
                else:
                    fixed = "SM_Scene_" + name
        
        elif asset_type == "block_piece":
            if not name.startswith("SM_BlockPiece_"):
                if name.startswith("BlockPiece_"):
                    fixed = "SM_" + name
                elif name.startswith("SM_"):
                    fixed = "SM_BlockPiece_" + name[3:]
                else:
                    fixed = "SM_BlockPiece_" + name
        
        elif asset_type == "weapon_part":
            if not name.startswith("SM_Weapon_"):
                if name.startswith("Weapon_"):
                    fixed = "SM_" + name
                elif name.startswith("SM_"):
                    fixed = "SM_Weapon_" + name[3:]
                else:
                    fixed = "SM_Weapon_" + name
        
        # 修复大小写
        parts = fixed.split("_")
        if len(parts) > 1:
            fixed = "_".join([parts[0]] + [p.capitalize() for p in parts[1:]])
        
        return fixed
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """验证文件"""
        filename = Path(file_path).stem
        return self.validate_name(filename)
    
    def validate_directory(self, directory: str, pattern: str = "*.fbx") -> List[ValidationResult]:
        """验证目录中的所有文件"""
        self._log(f"验证目录: {directory}")
        
        results = []
        
        if not os.path.exists(directory):
            self._log(f"目录不存在: {directory}", "ERROR")
            return results
        
        # 查找文件
        files = list(Path(directory).glob(pattern))
        
        self._log(f"找到 {len(files)} 个文件")
        
        for file_path in files:
            result = self.validate_file(str(file_path))
            results.append(result)
            self.results.append(result)
            
            # 记录结果
            if result.status == ValidationStatus.VALID:
                self._log(f"✅ {result.original_name}")
            elif result.status == ValidationStatus.WARNING:
                self._log(f"⚠️ {result.original_name}: {', '.join(result.issues)}")
            else:
                self._log(f"❌ {result.original_name}: {', '.join(result.issues)}")
        
        return results
    
    def validate_ue_asset(self, asset_path: str) -> ValidationResult:
        """验证UE资源"""
        asset_name = asset_path.split("/")[-1]
        return self.validate_name(asset_name)
    
    def validate_ue_directory(self, directory: str) -> List[ValidationResult]:
        """验证UE目录中的所有资源"""
        self._log(f"验证UE目录: {directory}")
        
        results = []
        
        # 获取所有资源
        asset_lib = unreal.EditorAssetLibrary
        asset_paths = asset_lib.list_assets(directory, recursive=True)
        
        self._log(f"找到 {len(asset_paths)} 个资源")
        
        for asset_path in asset_paths:
            result = self.validate_ue_asset(asset_path)
            results.append(result)
            self.results.append(result)
        
        return results
    
    def auto_fix_name(self, original_name: str, asset_type: str = None) -> str:
        """自动修复名称"""
        result = self.validate_name(original_name, asset_type)
        
        if result.can_auto_fix:
            return result.fixed_name
        
        return original_name
    
    def get_validation_report(self) -> str:
        """生成验证报告"""
        report = f"""# NamingValidator 验证报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计信息

- **有效**: {self.valid_count}
- **无效**: {self.invalid_count}
- **警告**: {self.warning_count}
- **总计**: {len(self.results)}

## 命名规范

### 场景建筑模型
- **格式**: `SM_Scene_[关卡]_[元素]_[编号]`
- **示例**: `SM_Scene_Ruins_WallBroken_01`
- **有效关卡**: OpenPlains, NarrowDungeon, MountainForest, Ruins, WeaponWorkshop, TrajectoryTest, TrainingGround

### 方块碎块模型
- **格式**: `SM_BlockPiece_[形状]`
- **示例**: `SM_BlockPiece_Cube`
- **有效形状**: Cube, Sphere, Cylinder, Cone, Wedge, Spike, Flat, LShape, TShape

### 武器部件模型
- **格式**: `SM_Weapon_[部件]`
- **示例**: `SM_Weapon_Handle`
- **有效部件**: Handle, Blade, HammerHead, AxeHead, SpearTip, Guard, Shaft

### 材质
- **格式**: `M_[材质类型]_[描述]`
- **示例**: `M_Stone_Wall`

### 纹理
- **格式**: `T_[材质]_[描述]_[后缀]`
- **示例**: `T_Stone_Wall_BC`
- **有效后缀**: BC(基础颜色), N(法线), R(粗糙度), M(金属度), AO(环境光遮蔽), E(自发光), ORM(综合)

## 详细结果

"""
        
        # 按状态分组
        valid_results = [r for r in self.results if r.status == ValidationStatus.VALID]
        invalid_results = [r for r in self.results if r.status == ValidationStatus.INVALID]
        warning_results = [r for r in self.results if r.status == ValidationStatus.WARNING]
        
        if invalid_results:
            report += "### ❌ 无效\n\n"
            for result in invalid_results:
                report += f"**{result.original_name}** ({result.asset_type})\n"
                for issue in result.issues:
                    report += f"- 问题: {issue}\n"
                for suggestion in result.suggestions:
                    report += f"- 建议: {suggestion}\n"
                if result.can_auto_fix:
                    report += f"- 自动修复: `{result.fixed_name}`\n"
                report += "\n"
        
        if warning_results:
            report += "### ⚠️ 警告\n\n"
            for result in warning_results:
                report += f"**{result.original_name}** ({result.asset_type})\n"
                for issue in result.issues:
                    report += f"- {issue}\n"
                report += "\n"
        
        if valid_results:
            report += "### ✅ 有效\n\n"
            for result in valid_results[:20]:  # 只显示前20个
                report += f"- {result.original_name} ({result.asset_type})\n"
            if len(valid_results) > 20:
                report += f"- ... 还有 {len(valid_results) - 20} 个\n"
            report += "\n"
        
        report += "## 日志\n\n```\n"
        for log in self.logs:
            report += f"{log}\n"
        report += "```\n"
        
        return report
    
    def save_report(self, filename: str = None):
        """保存报告"""
        if filename is None:
            filename = f"naming_validator_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_path = os.path.join("/python/logs", filename)
        os.makedirs("/python/logs", exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.get_validation_report())
        
        self._log(f"报告已保存: {report_path}")
        return report_path

# ============================================================================
# 快捷函数
# ============================================================================

_naming_validator = None

def get_naming_validator() -> NamingValidatorSkill:
    """获取NamingValidator实例"""
    global _naming_validator
    if _naming_validator is None:
        _naming_validator = NamingValidatorSkill()
    return _naming_validator

def validate_name(name: str, asset_type: str = None):
    """验证单个名称"""
    validator = get_naming_validator()
    return validator.validate_name(name, asset_type)

def validate_file(file_path: str):
    """验证文件"""
    validator = get_naming_validator()
    return validator.validate_file(file_path)

def validate_directory(directory: str, pattern: str = "*.fbx"):
    """验证目录"""
    validator = get_naming_validator()
    results = validator.validate_directory(directory, pattern)
    validator.save_report()
    return results

def validate_ue_directory(directory: str):
    """验证UE目录"""
    validator = get_naming_validator()
    results = validator.validate_ue_directory(directory)
    validator.save_report()
    return results

def auto_fix_name(name: str, asset_type: str = None):
    """自动修复名称"""
    validator = get_naming_validator()
    return validator.auto_fix_name(name, asset_type)

def get_naming_report():
    """获取验证报告"""
    validator = get_naming_validator()
    return validator.get_validation_report()

# ============================================================================
# 使用示例
# ============================================================================

# 在UE Python控制台中:
# import naming_validator_skill
# result = naming_validator_skill.validate_name("SM_Scene_Ruins_Wall_01")
# results = naming_validator_skill.validate_directory("D:/BlenderExports")
# results = naming_validator_skill.validate_ue_directory("/Game/Meshes/SceneBuildings")
# fixed_name = naming_validator_skill.auto_fix_name("ruins_wall_01")
# print(naming_validator_skill.get_naming_report())

if __name__ == "__main__":
    # 测试验证
    test_names = [
        "SM_Scene_Ruins_Wall_01",
        "SM_BlockPiece_Cube",
        "SM_Weapon_Handle",
        "ruins_wall_01",
        "SM_Scene_Unknown_Test_01",
        "WrongPrefix_Test"
    ]
    
    validator = get_naming_validator()
    for name in test_names:
        result = validator.validate_name(name)
        print(f"{name}: {result.status.value}")
        if result.issues:
            print(f"  问题: {result.issues}")
        if result.can_auto_fix:
            print(f"  建议: {result.fixed_name}")
