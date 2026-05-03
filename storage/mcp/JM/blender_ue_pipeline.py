#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blender到UE工作流 MCP Server

完整工作流：AI生成 → Blender → UE

用法：
    python blender_ue_pipeline.py

环境变量：
    BLENDER_EXECUTABLE - Blender可执行文件路径
    UE_EDITOR - UE编辑器路径
    MESHY_API_KEY - Meshy API密钥
"""

import os
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

# FastMCP
try:
    from fastmcp import FastMCP
except ImportError:
    print("FastMCP not installed. Install with: pip install fastmcp")
    raise

# ============================================================
# 配置
# ============================================================
@dataclass
class PipelineConfig:
    """流水线配置"""
    project_base: Path = Path("%SOFTWARE_DIR%/KF/JM")
    blender_dir: Path = Path("%SOFTWARE_DIR%/KF/JM/blender")
    ue_dir: Path = Path("%SOFTWARE_DIR%/KF/JM/ue")
    ai_models_dir: Path = Path("%SOFTWARE_DIR%/KF/JM/pipeline/ai_models")
    exports_dir: Path = Path("%SOFTWARE_DIR%/KF/JM/blender/exports")
    
    blender_executable: str = "%DEVTOOLS_DIR%/Blender/blender.exe"
    ue_editor: str = "%DEVTOOLS_DIR%/游戏引擎/UE_5.3/Engine/Binaries/Win64/UnrealEditor.exe"
    
    meshy_api_key: str = os.getenv("MESHY_API_KEY", "")

CONFIG = PipelineConfig()

# 确保目录存在
for dir_path in [CONFIG.blender_dir, CONFIG.ue_dir, CONFIG.ai_models_dir, CONFIG.exports_dir]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================
# FastMCP Server
# ============================================================
mcp = FastMCP("blender-ue-pipeline")

# ============================================================
# AI 3D生成
# ============================================================
async def generate_ai_model(prompt: str, style: str = "realistic") -> Dict[str, Any]:
    """使用AI生成3D模型"""
    try:
        import aiohttp
        
        url = "https://api.meshy.ai/v2/text-to-3d"
        headers = {
            "Authorization": f"Bearer {CONFIG.meshy_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "mode": "preview",
            "prompt": prompt,
            "style": style
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                return {
                    "success": True,
                    "task_id": data.get("result"),
                    "prompt": prompt,
                    "status": "pending"
                }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def check_ai_status(task_id: str) -> Dict[str, Any]:
    """检查AI生成状态"""
    try:
        import aiohttp
        
        url = f"https://api.meshy.ai/v2/text-to-3d/{task_id}"
        headers = {"Authorization": f"Bearer {CONFIG.meshy_api_key}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "status": data.get("status"),
                    "progress": data.get("progress", 0),
                    "model_urls": data.get("model_urls", {})
                }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def download_ai_model(task_id: str, format: str = "glb") -> Path:
    """下载AI生成的模型"""
    try:
        import aiohttp
        
        # 检查状态
        status = await check_ai_status(task_id)
        if not status.get("success") or status.get("status") != "SUCCEEDED":
            raise Exception("Model not ready")
        
        model_urls = status.get("model_urls", {})
        download_url = model_urls.get(format)
        
        if not download_url:
            raise Exception(f"Format {format} not available")
        
        # 下载
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                response.raise_for_status()
                content = await response.read()
                
                output_file = CONFIG.ai_models_dir / f"ai_model_{task_id}.{format}"
                output_file.write_bytes(content)
                
                return output_file
    except Exception as e:
        raise Exception(f"Download failed: {e}")

# ============================================================
# Blender操作
# ============================================================
async def run_blender_script(script_path: Path, args: list = None) -> Dict[str, Any]:
    """运行Blender脚本"""
    try:
        cmd = [
            CONFIG.blender_executable,
            "--background",
            "--python", str(script_path)
        ]
        
        if args:
            cmd.extend(["--"] + args)
        
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            return {
                "success": True,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
        else:
            return {
                "success": False,
                "error": stderr.decode(),
                "stdout": stdout.decode()
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def import_to_blender(model_file: Path, blend_file: Path = None) -> Dict[str, Any]:
    """导入模型到Blender"""
    # 创建临时脚本
    script_content = f'''
import bpy
import sys

# 清理场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 导入模型
model_path = r"{model_file}"
ext = model_path.split('.')[-1].lower()

if ext == "obj":
    bpy.ops.import_scene.obj(filepath=model_path)
elif ext == "fbx":
    bpy.ops.import_scene.fbx(filepath=model_path)
elif ext in ["glb", "gltf"]:
    bpy.ops.import_scene.gltf(filepath=model_path)

# 应用变换
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 保存
output_path = r"{blend_file or CONFIG.blender_dir / 'imported.blend'}"
bpy.ops.wm.save_as_mainfile(filepath=output_path)
print(f"Saved to: {{output_path}}")
'''
    
    script_file = Path("/python/Temp/blender_import.py")
    script_file.parent.mkdir(parents=True, exist_ok=True)
    script_file.write_text(script_content, encoding="utf-8")
    
    return await run_blender_script(script_file)

async def export_from_blender(blend_file: Path, output_file: Path, format: str = "fbx") -> Dict[str, Any]:
    """从Blender导出"""
    script_content = f'''
import bpy

# 打开文件
bpy.ops.wm.open_mainfile(filepath=r"{blend_file}")

# 选择所有对象
bpy.ops.object.select_all(action='SELECT')

# 导出
output_path = r"{output_file}"

if "{format}" == "fbx":
    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=True,
        global_scale=1.0,
        apply_unit_scale=True,
        axis_forward='-Z',
        axis_up='Y'
    )
elif "{format}" == "gltf":
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        use_selection=True,
        export_format='GLB'
    )

print(f"Exported to: {{output_path}}")
'''
    
    script_file = Path("/python/Temp/blender_export.py")
    script_file.parent.mkdir(parents=True, exist_ok=True)
    script_file.write_text(script_content, encoding="utf-8")
    
    return await run_blender_script(script_file)

# ============================================================
# UE操作
# ============================================================
async def import_to_ue(fbx_file: Path, ue_project: Path, import_path: str = "/Game/Imported") -> Dict[str, Any]:
    """导入到UE"""
    try:
        cmd = [
            "python",
            "/python/MCP/ue_import.py",
            "--project", str(ue_project),
            "--file", str(fbx_file),
            "--path", import_path
        ]
        
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await result.communicate()
        
        return {
            "success": result.returncode == 0,
            "stdout": stdout.decode(),
            "stderr": stderr.decode()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================
# MCP Tools
# ============================================================
@mcp.tool()
async def full_pipeline(
    prompt: str,
    project_path: str = "%SOFTWARE_DIR%/KF/JM",
    style: str = "realistic",
    export_format: str = "fbx",
    ue_project: str = None
) -> Dict[str, Any]:
    """
    完整工作流：AI生成 → Blender → UE
    
    Args:
        prompt: AI生成提示词
        project_path: 项目基础路径
        style: 风格 (realistic/cartoon/sculpture)
        export_format: 导出格式 (fbx/gltf)
        ue_project: UE项目文件路径
    
    Returns:
        工作流执行结果
    """
    try:
        results = {"steps": []}
        
        # 步骤1: AI生成
        print("Step 1: Generating AI model...")
        gen_result = await generate_ai_model(prompt, style)
        if not gen_result.get("success"):
            return gen_result
        
        task_id = gen_result["task_id"]
        results["steps"].append({"step": 1, "action": "ai_generate", "result": gen_result})
        
        # 步骤2: 等待生成完成
        print("Step 2: Waiting for AI generation...")
        max_wait = 600  # 10分钟
        waited = 0
        while waited < max_wait:
            status = await check_ai_status(task_id)
            if status.get("status") == "SUCCEEDED":
                break
            elif status.get("status") in ["FAILED", "CANCELLED"]:
                return {"success": False, "error": f"AI generation {status['status']}"}
            await asyncio.sleep(10)
            waited += 10
        
        results["steps"].append({"step": 2, "action": "wait_generation", "status": "completed"})
        
        # 步骤3: 下载模型
        print("Step 3: Downloading model...")
        model_file = await download_ai_model(task_id, "glb")
        results["steps"].append({"step": 3, "action": "download", "file": str(model_file)})
        
        # 步骤4: 导入Blender
        print("Step 4: Importing to Blender...")
        blend_file = Path(project_path) / "blender" / f"{task_id}.blend"
        import_result = await import_to_blender(model_file, blend_file)
        if not import_result.get("success"):
            return import_result
        results["steps"].append({"step": 4, "action": "import_blender", "result": import_result})
        
        # 步骤5: 从Blender导出
        print("Step 5: Exporting from Blender...")
        export_file = CONFIG.exports_dir / f"{task_id}.{export_format}"
        export_result = await export_from_blender(blend_file, export_file, export_format)
        if not export_result.get("success"):
            return export_result
        results["steps"].append({"step": 5, "action": "export_blender", "result": export_result})
        
        # 步骤6: 导入UE（如果提供了UE项目）
        if ue_project:
            print("Step 6: Importing to UE...")
            ue_result = await import_to_ue(export_file, Path(ue_project))
            results["steps"].append({"step": 6, "action": "import_ue", "result": ue_result})
        
        results["success"] = True
        results["task_id"] = task_id
        results["model_file"] = str(export_file)
        
        return results
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def ai_to_blender(
    prompt: str,
    blend_file: str,
    style: str = "realistic"
) -> Dict[str, Any]:
    """
    AI生成并导入Blender
    
    Args:
        prompt: AI生成提示词
        blend_file: 输出Blender文件路径
        style: 风格
    
    Returns:
        导入结果
    """
    try:
        # 生成AI模型
        gen_result = await generate_ai_model(prompt, style)
        if not gen_result.get("success"):
            return gen_result
        
        task_id = gen_result["task_id"]
        
        # 等待完成
        while True:
            status = await check_ai_status(task_id)
            if status.get("status") == "SUCCEEDED":
                break
            elif status.get("status") in ["FAILED", "CANCELLED"]:
                return {"success": False, "error": f"Generation {status['status']}"}
            await asyncio.sleep(10)
        
        # 下载
        model_file = await download_ai_model(task_id, "glb")
        
        # 导入Blender
        return await import_to_blender(model_file, Path(blend_file))
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def blender_to_ue(
    blender_file: str,
    ue_project: str,
    export_format: str = "fbx",
    import_path: str = "/Game/Imported"
) -> Dict[str, Any]:
    """
    Blender导出到UE
    
    Args:
        blender_file: Blender文件路径
        ue_project: UE项目路径
        export_format: 导出格式
        import_path: UE导入路径
    
    Returns:
        导入结果
    """
    try:
        blend_path = Path(blender_file)
        export_file = CONFIG.exports_dir / f"{blend_path.stem}.{export_format}"
        
        # 导出
        export_result = await export_from_blender(blend_path, export_file, export_format)
        if not export_result.get("success"):
            return export_result
        
        # 导入UE
        return await import_to_ue(export_file, Path(ue_project), import_path)
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def check_pipeline_status(task_id: str) -> Dict[str, Any]:
    """检查AI生成状态"""
    return await check_ai_status(task_id)

# ============================================================
# 主函数
# ============================================================
if __name__ == "__main__":
    mcp.run()
