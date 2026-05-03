"""Export module for generating Godot-compatible JSON output."""

import os
import json
from typing import List, Dict, Any, Optional

import normalizer


def export_godot_json(
    source_image: str,
    frames: List[Dict],
    animations: Dict[str, Dict],
    normalize_size: str = "none",
    pivot: str = "center",
    output_path: Optional[str] = None,
    godot_texture_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export spritesheet data as Godot-compatible JSON.
    
    The output can be used directly with godot-mcp-bridge tools:
    - godot_atlas_batch_create (create AtlasTextures)
    - godot_spriteframes_create + godot_spriteframes_add_frame
    
    Args:
        source_image: Path to original spritesheet
        frames: List of frame dicts with id, x, y, w, h
        animations: Animation groups {name: {frameIds, fps, loop}}
        normalize_size: Normalization mode - "none", "max", "median"
        pivot: Pivot point - "center", "bottom_center", "top_left"
        output_path: Optional path to save JSON file
        godot_texture_path: Godot res:// path for the texture
    
    Returns:
        Dict with Godot-ready data structure
    """
    # Normalize frames if requested
    norm_result = normalizer.normalize_frames(frames, normalize_size, pivot)
    normalized_frames = norm_result["frames"]
    
    # Convert source path to Godot path if not provided
    if not godot_texture_path:
        # Try to detect res:// path from source
        godot_texture_path = _guess_godot_path(source_image)
    
    # Build frame rects for atlas creation
    atlas_rects = []
    for frame in normalized_frames:
        rect = {
            "id": frame["id"],
            "x": frame["x"],
            "y": frame["y"],
            "w": frame["w"],
            "h": frame["h"]
        }
        
        # Add pivot info
        if "pivot" in frame:
            rect["pivot"] = frame["pivot"]
        
        # Add normalization offset if applicable
        if "offset_x" in frame:
            rect["offset"] = {
                "x": frame["offset_x"],
                "y": frame["offset_y"]
            }
        
        atlas_rects.append(rect)
    
    # Build animation definitions
    animation_defs = {}
    for anim_name, anim_data in animations.items():
        frame_ids = anim_data.get("frameIds", anim_data.get("frame_ids", []))
        animation_defs[anim_name] = {
            "frameIds": frame_ids,
            "fps": anim_data.get("fps", 10),
            "loop": anim_data.get("loop", True),
            "frameCount": len(frame_ids)
        }
    
    # Build Godot-ready output
    output = {
        "meta": {
            "generator": "sprite-sheet-mcp",
            "version": "1.0.0",
            "source_image": source_image,
            "normalization": normalize_size,
            "pivot": pivot
        },
        "texture": {
            "path": godot_texture_path,
            "local_path": source_image
        },
        "frames": atlas_rects,
        "animations": animation_defs,
        "normalized_size": norm_result.get("normalized_size"),
        
        # Pre-built commands for Godot MCP
        "godot_commands": _build_godot_commands(
            godot_texture_path,
            atlas_rects,
            animation_defs
        )
    }
    
    # Save to file if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        output["saved_to"] = output_path
    
    return output


def _guess_godot_path(local_path: str) -> str:
    """
    Try to guess the Godot res:// path from a local path.
    
    Looks for common project structures.
    """
    # Normalize path
    path = local_path.replace("\\", "/")
    
    # Common patterns
    markers = [
        "/Art/", "/art/",
        "/Assets/", "/assets/",
        "/Sprites/", "/sprites/",
        "/Images/", "/images/",
        "/Textures/", "/textures/",
        "/Graphics/", "/graphics/"
    ]
    
    for marker in markers:
        if marker in path:
            idx = path.find(marker)
            return "res:/" + path[idx:]
    
    # Fallback: use filename only
    filename = os.path.basename(path)
    return f"res://Art/{filename}"


def _build_godot_commands(
    texture_path: str,
    frames: List[Dict],
    animations: Dict[str, Dict]
) -> Dict[str, Any]:
    """
    Build ready-to-use Godot MCP command sequences.
    
    These can be executed directly by the LLM.
    """
    commands = {
        "description": "Pre-built commands for godot-mcp-bridge",
        "workflow": [
            "1. Create AtlasTextures with godot_atlas_batch_create",
            "2. Create SpriteFrames with godot_spriteframes_create",
            "3. Add animations with godot_spriteframes_add_animation",
            "4. Add frames with godot_spriteframes_add_frame"
        ],
        "commands": []
    }
    
    # Command 1: Create all AtlasTextures in batch
    rects = [{"x": f["x"], "y": f["y"], "w": f["w"], "h": f["h"]} for f in frames]
    
    commands["commands"].append({
        "tool": "godot_atlas_batch_create",
        "description": "Create AtlasTextures for all frames",
        "arguments": {
            "texture_path": texture_path,
            "rects": rects,
            "save_folder": texture_path.rsplit("/", 1)[0] + "/frames"
        }
    })
    
    # Command 2: Create SpriteFrames resource
    spriteframes_path = texture_path.rsplit(".", 1)[0] + "_frames.tres"
    
    commands["commands"].append({
        "tool": "godot_spriteframes_create",
        "description": "Create SpriteFrames resource",
        "arguments": {
            "save_path": spriteframes_path
        }
    })
    
    # Commands 3+: Add each animation
    for anim_name, anim_data in animations.items():
        commands["commands"].append({
            "tool": "godot_spriteframes_add_animation",
            "description": f"Add animation: {anim_name}",
            "arguments": {
                "spriteframes_path": spriteframes_path,
                "animation_name": anim_name
            }
        })
        
        commands["commands"].append({
            "tool": "godot_spriteframes_set_fps",
            "arguments": {
                "spriteframes_path": spriteframes_path,
                "animation_name": anim_name,
                "fps": anim_data.get("fps", 10)
            }
        })
        
        commands["commands"].append({
            "tool": "godot_spriteframes_set_loop",
            "arguments": {
                "spriteframes_path": spriteframes_path,
                "animation_name": anim_name,
                "loop": anim_data.get("loop", True)
            }
        })
    
    # Note about frame addition
    commands["frame_addition_note"] = (
        "After creating AtlasTextures, use the returned paths with "
        "godot_spriteframes_add_frame for each frame in each animation."
    )
    
    return commands


def export_simple_atlas(
    frames: List[Dict],
    texture_path: str
) -> Dict[str, Any]:
    """
    Export a simple atlas definition (just rects) for direct use.
    """
    return {
        "texture": texture_path,
        "rects": [
            {"x": f["x"], "y": f["y"], "w": f["w"], "h": f["h"]}
            for f in frames
        ]
    }


def export_spriteframes_script(
    source_image: str,
    frames: List[Dict],
    animations: Dict[str, Dict],
    godot_texture_path: str
) -> str:
    """
    Generate a GDScript that creates SpriteFrames programmatically.
    
    Useful for complex setups or when MCP isn't available.
    """
    script_lines = [
        "@tool",
        "extends EditorScript",
        "",
        "func _run():",
        f'\tvar texture = load("{godot_texture_path}")',
        "\tvar sf = SpriteFrames.new()",
        "\t",
        "\t# Remove default animation",
        '\tif sf.has_animation("default"):',
        '\t\tsf.remove_animation("default")',
        "\t",
    ]
    
    # Create AtlasTextures for each frame
    script_lines.append("\t# Create AtlasTextures")
    script_lines.append("\tvar atlas_textures = []")
    
    for i, frame in enumerate(frames):
        script_lines.append(f"\t")
        script_lines.append(f"\tvar atlas_{i} = AtlasTexture.new()")
        script_lines.append(f"\tatlas_{i}.atlas = texture")
        script_lines.append(f"\tatlas_{i}.region = Rect2({frame['x']}, {frame['y']}, {frame['w']}, {frame['h']})")
        script_lines.append(f"\tatlas_textures.append(atlas_{i})")
    
    script_lines.append("\t")
    script_lines.append("\t# Create animations")
    
    for anim_name, anim_data in animations.items():
        frame_ids = anim_data.get("frameIds", [])
        fps = anim_data.get("fps", 10)
        loop = "true" if anim_data.get("loop", True) else "false"
        
        script_lines.append(f"\t")
        script_lines.append(f'\tsf.add_animation("{anim_name}")')
        script_lines.append(f'\tsf.set_animation_speed("{anim_name}", {fps})')
        script_lines.append(f'\tsf.set_animation_loop("{anim_name}", {loop})')
        
        for fid in frame_ids:
            script_lines.append(f'\tsf.add_frame("{anim_name}", atlas_textures[{fid}])')
    
    # Save resource
    base_name = os.path.splitext(os.path.basename(godot_texture_path))[0]
    save_path = f'res://Art/{base_name}_frames.tres'
    
    script_lines.append("\t")
    script_lines.append(f'\tResourceSaver.save(sf, "{save_path}")')
    script_lines.append(f'\tprint("SpriteFrames saved to: {save_path}")')
    
    return "\n".join(script_lines)
