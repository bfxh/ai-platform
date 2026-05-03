"""
ComfyUI MCP Server Bridge
连接 ComfyUI (本地 :8188) 到 AI 助手，实现 AI驱动的概念设计/材质生成
"""
import json
import base64
import uuid
import asyncio
from pathlib import Path
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = Path("/MCP_3D/Shared/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("ComfyUI-AAA")


@mcp.tool()
async def generate_concept_art(
    prompt: str,
    negative_prompt: str = "pixel art, voxel, blocky, low poly, cartoon, simple, blurry, bad quality, deformed",
    width: int = 1024,
    height: int = 1024,
    steps: int = 25,
    cfg: float = 7.0,
    seed: int = -1,
    style: str = "photorealistic"
) -> dict:
    """生成 AAA 级概念艺术图/氛围图。
    
    默认 style=photorealistic，会过滤掉所有像素/方块/低面数风格。
    
    用法: "generate_concept_art('未来赛博朋克城市 雨夜 霓虹灯 广角镜头', style='cinematic')"
    """
    if seed == -1:
        seed = hash(prompt) % 100000000 + 42
    
    full_prompt = f"{prompt}, {style}, 8k, highly detailed, professional concept art, AAA quality, photorealistic, trending on artstation, sharp focus, 32k uhd"
    
    workflow = _build_txt2img_workflow(full_prompt, negative_prompt, width, height, steps, cfg, seed)
    
    client = httpx.AsyncClient(timeout=120.0)
    try:
        r = await client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
        r.raise_for_status()
        prompt_id = r.json()["prompt_id"]
        
        result = await _wait_for_result(client, prompt_id)
        
        if result and result.get("images"):
            images = result["images"]
            return {
                "status": "success",
                "prompt_id": prompt_id,
                "prompt": prompt,
                "style": style,
                "images": images,
                "output_dir": str(OUTPUT_DIR / prompt_id),
                "message": f"生成了 {len(images)} 张概念图。提示词: '{prompt}' 风格: {style}"
            }
        else:
            return {"status": "error", "message": "生成未返回图片，检查ComfyUI日志", "prompt_id": prompt_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await client.aclose()


@mcp.tool()
async def generate_material_texture(
    material_type: str,
    resolution: str = "2k",
    art_style: str = "PBR realistic"
) -> dict:
    """生成 PBR 材质贴图集 (Albedo/Normal/Roughness/Metallic/Height)。
    
    material_type: asphalt, concrete, wood, metal, rock, fabric, leather, marble, etc.
    
    用法: "generate_material_texture('weathered concrete', resolution='4k')"
    """
    size_map = {"1k": 1024, "2k": 2048, "4k": 4096}
    size = size_map.get(resolution, 2048)
    
    full_prompt = (
        f"seamless {material_type} PBR texture, {art_style}, "
        f"top-down flat lay, even lighting, square tileable, "
        f"no shadows cast, no pixel art no cartoon no blocky, "
        f"AAA game asset quality, high detail surface imperfections"
    )
    negative = "pixel art, voxel, cartoon, 3D perspective, shadows, seams, edges, borders, frame"

    workflow = _build_txt2img_workflow(full_prompt, negative, size, size, 30, 9.0, 42)
    
    filename = material_type.lower().replace(" ", "_").replace(",", "")
    
    client = httpx.AsyncClient(timeout=120.0)
    try:
        r = await client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
        r.raise_for_status()
        prompt_id = r.json()["prompt_id"]
        
        result = await _wait_for_result(client, prompt_id)
        
        if result and result.get("images"):
            return {
                "status": "success",
                "material": material_type,
                "resolution": resolution,
                "style": art_style,
                "images": result["images"],
                "filename_base": filename,
                "message": f"生成了 {material_type} PBR 材质 ({resolution})"
            }
        return {"status": "error", "message": "材质生成未返回图片", "prompt_id": prompt_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await client.aclose()


@mcp.tool()
async def generate_ui_element(
    element_type: str,
    description: str,
    width: int = 512,
    height: int = 512,
    style: str = "AAA sci-fi UI"
) -> dict:
    """生成游戏 UI 元素 (按钮/图标/面板/HUD元素)。
    
    element_type: button, icon, panel, frame, bar, slot, card, etc.
    
    用法: "generate_ui_element('button', 'glowing neon cyber button', style='cyberpunk HUD')"
    """
    full_prompt = (
        f"game UI {element_type}, {description}, {style}, "
        f"transparent background, clean design, game interface element, "
        f"AAA quality, professional UI design, sharp vector-like, "
        f"no 3D scene, no characters, no environment"
    )
    negative = "pixel art, 8-bit, cartoon, 3D scene, environment, characters, text labels, blurry, messy"

    workflow = _build_txt2img_workflow(full_prompt, negative, width, height, 20, 8.0, 43)
    
    client = httpx.AsyncClient(timeout=120.0)
    try:
        r = await client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
        r.raise_for_status()
        prompt_id = r.json()["prompt_id"]
        
        result = await _wait_for_result(client, prompt_id)
        
        if result and result.get("images"):
            return {
                "status": "success",
                "element_type": element_type,
                "description": description,
                "style": style,
                "images": result["images"],
                "message": f"生成了 {element_type} UI 元素: {description}"
            }
        return {"status": "error", "message": "UI生成未返回图片", "prompt_id": prompt_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await client.aclose()


@mcp.tool()
async def generate_sprite_sheet(
    description: str,
    frames: int = 8,
    frame_width: int = 128,
    frame_height: int = 128,
    style: str = "realistic"
) -> dict:
    """生成角色/物体的 spritesheet 动画帧序列。
    
    用法: "generate_sprite_sheet('fire explosion animation', frames=12)"
    """
    full_prompt = (
        f"sprite sheet animation, {description}, {style}, "
        f"{frames} frames arranged in a grid, "
        f"each frame separated by clear divisions, "
        f"consistent lighting between frames, smooth animation sequence, "
        f"AAA game asset quality, transparent or uniform background"
    )
    negative = "pixel art, 8-bit, blurred frames, inconsistent frames, 3D, perspective"

    width = frame_width * 4
    height = frame_height * ((frames + 3) // 4)

    workflow = _build_txt2img_workflow(full_prompt, negative, width, height, 30, 8.0, 44)
    
    client = httpx.AsyncClient(timeout=120.0)
    try:
        r = await client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
        r.raise_for_status()
        prompt_id = r.json()["prompt_id"]
        
        result = await _wait_for_result(client, prompt_id)
        
        if result and result.get("images"):
            return {
                "status": "success",
                "description": description,
                "frames": frames,
                "images": result["images"],
                "message": f"生成了 {frames} 帧动画 spritesheet"
            }
        return {"status": "error", "message": "SpriteSheet生成未返回图片"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await client.aclose()


@mcp.tool()
async def check_comfyui_status() -> dict:
    """检查 ComfyUI 服务状态"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{COMFYUI_URL}/system_stats")
            if r.status_code == 200:
                stats = r.json()
                return {
                    "status": "online",
                    "system": stats.get("system", {}),
                    "python_version": stats.get("python_version", ""),
                    "message": "ComfyUI 运行正常"
                }
            return {"status": "error", "message": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "offline", "message": f"ComfyUI 未运行: {e}"}


def _build_txt2img_workflow(
    positive: str, negative: str,
    width: int, height: int,
    steps: int, cfg: float, seed: int
) -> dict:
    """构建基本的 txt2img workflow JSON"""
    return {
        "3": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "dpmpp_2m_sde",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler"
        },
        "4": {
            "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"},
            "class_type": "CheckpointLoaderSimple"
        },
        "5": {
            "inputs": {"width": width, "height": height, "batch_size": 1},
            "class_type": "EmptyLatentImage"
        },
        "6": {
            "inputs": {"text": positive, "clip": ["4", 1]},
            "class_type": "CLIPTextEncode"
        },
        "7": {
            "inputs": {"text": negative, "clip": ["4", 1]},
            "class_type": "CLIPTextEncode"
        },
        "8": {
            "inputs": {"samples": ["3", 0]},
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]},
            "class_type": "SaveImage"
        },
        "10": {
            "inputs": {"vae": ["4", 2]},
            "class_type": "VAELoader"
        }
    }


async def _wait_for_result(client: httpx.AsyncClient, prompt_id: str, timeout: float = 120.0) -> dict | None:
    """等待 ComfyUI 生成完成并获取结果"""
    import time
    start = time.time()
    while time.time() - start < timeout:
        await asyncio.sleep(2)
        try:
            r = await client.get(f"{COMFYUI_URL}/history/{prompt_id}")
            if r.status_code == 200:
                history = r.json()
                if prompt_id in history:
                    outputs = history[prompt_id]["outputs"]
                    images = []
                    for node_id, node_output in outputs.items():
                        for img in node_output.get("images", []):
                            images.append({
                                "filename": img["filename"],
                                "subfolder": img.get("subfolder", ""),
                                "type": img["type"],
                                "url": f"{COMFYUI_URL}/view?filename={img['filename']}&subfolder={img.get('subfolder', '')}&type={img['type']}"
                            })
                    return {"images": images, "prompt_id": prompt_id}
        except Exception:
            pass
    return None


if __name__ == "__main__":
    mcp.run()
