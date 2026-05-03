#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UE自动化导入脚本

用于在Unreal Engine中执行自动化导入操作

用法：
    python ue_import.py --project <uproject> --file <fbx> --path <import_path>
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# ============================================================
# 配置
# ============================================================
CONFIG = {
    "ue_editor": "%DEVTOOLS_DIR%/游戏引擎/UE_5.3/Engine/Binaries/Win64/UnrealEditor.exe",
    "ue_python": "%DEVTOOLS_DIR%/游戏引擎/UE_5.3/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
}

# ============================================================
# UE导入脚本模板
# ============================================================
UE_PYTHON_SCRIPT = '''
import unreal
import sys

# 获取参数
file_path = "{file_path}"
import_path = "{import_path}"

print(f"Importing: {{file_path}}")
print(f"To: {{import_path}}")

# 设置导入选项
options = unreal.FbxImportUI()
options.set_editor_property('import_mesh', True)
options.set_editor_property('import_textures', True)
options.set_editor_property('import_materials', True)
options.set_editor_property('import_as_skeletal', False)

# 静态网格导入选项
static_mesh_import_data = unreal.FbxStaticMeshImportData()
static_mesh_import_data.set_editor_property('combine_meshes', True)
static_mesh_import_data.set_editor_property('build_nanite', True)
static_mesh_import_data.set_editor_property('build_reversed_index_buffer', True)
static_mesh_import_data.set_editor_property('generate_lightmap_u_vs', True)

options.set_editor_property('static_mesh_import_data', static_mesh_import_data)

# 材质导入选项
material_import_data = unreal.FbxMaterialImportData()
material_import_data.set_editor_property('base_material_name', '/Engine/BasicShapes/BasicShapeMaterial')
options.set_editor_property('material_import_data', material_import_data)

# 执行导入
task = unreal.AssetImportTask()
task.set_editor_property('automated', True)
task.set_editor_property('destination_path', import_path)
task.set_editor_property('filename', file_path)
task.set_editor_property('replace_existing', True)
task.set_editor_property('options', options)

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

print("Import completed!")
'''

# ============================================================
# UE工具类
# ============================================================
class UEImporter:
    """UE导入器"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project not found: {project_path}")
    
    def import_fbx(self, file_path: str, import_path: str = "/Game/Imported") -> Dict[str, Any]:
        """导入FBX文件"""
        try:
            # 生成Python脚本
            script_content = UE_PYTHON_SCRIPT.format(
                file_path=file_path.replace("\\", "/"),
                import_path=import_path
            )
            
            # 保存临时脚本
            temp_script = Path("/python/Temp/ue_import_script.py")
            temp_script.parent.mkdir(parents=True, exist_ok=True)
            temp_script.write_text(script_content, encoding="utf-8")
            
            # 构建命令
            cmd = [
                CONFIG["ue_python"],
                str(self.project_path),
                "-ExecutePythonScript=" + str(temp_script),
                "-stdout",
                "-unattended",
                "-nosplash"
            ]
            
            # 执行导入
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "file": file_path,
                    "import_path": import_path,
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "output": result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Import timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def import_with_datasmith(self, file_path: str, import_path: str = "/Game/Imported") -> Dict[str, Any]:
        """使用Datasmith导入"""
        try:
            # Datasmith导入脚本
            datasmith_script = f'''
import unreal

file_path = "{file_path.replace("\\", "/")}"
import_path = "{import_path}"

# 使用Datasmith导入
import_options = unreal.DatasmithImportBaseOptions()
result = unreal.DatasmithSceneImporter.import_scene(
    file_path,
    import_path,
    import_options
)

print(f"Datasmith import result: {{result}}")
'''
            
            temp_script = Path("/python/Temp/ue_datasmith_script.py")
            temp_script.parent.mkdir(parents=True, exist_ok=True)
            temp_script.write_text(datasmith_script, encoding="utf-8")
            
            cmd = [
                CONFIG["ue_python"],
                str(self.project_path),
                "-ExecutePythonScript=" + str(temp_script),
                "-stdout",
                "-unattended"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "file": file_path,
                    "import_path": import_path,
                    "method": "datasmith",
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='UE Import Tool')
    parser.add_argument('--project', required=True, help='UE project path')
    parser.add_argument('--file', required=True, help='File to import')
    parser.add_argument('--path', default='/Game/Imported', help='Import path')
    parser.add_argument('--datasmith', action='store_true', help='Use Datasmith')
    
    args = parser.parse_args()
    
    importer = UEImporter(args.project)
    
    if args.datasmith:
        result = importer.import_with_datasmith(args.file, args.path)
    else:
        result = importer.import_fbx(args.file, args.path)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
