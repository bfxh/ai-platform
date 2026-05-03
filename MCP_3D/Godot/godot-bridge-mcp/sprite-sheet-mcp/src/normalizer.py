"""Frame normalization module for consistent animation playback."""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple


def normalize_frames(
    frames: List[Dict],
    mode: str = "none",
    pivot: str = "center"
) -> Dict[str, Any]:
    """
    Normalize frame sizes and calculate pivot offsets.
    
    Args:
        frames: List of frame dicts with id, x, y, w, h
        mode: Normalization mode - "none", "max", "median"
        pivot: Pivot point - "center", "bottom_center", "top_left"
    
    Returns:
        Dict with normalized frames and metadata
    """
    if not frames:
        return {"frames": [], "normalized_size": None, "pivot": pivot}
    
    # Calculate target size based on mode
    widths = [f["w"] for f in frames]
    heights = [f["h"] for f in frames]
    
    if mode == "none":
        target_w, target_h = None, None
    elif mode == "max":
        target_w = max(widths)
        target_h = max(heights)
    elif mode == "median":
        target_w = int(np.median(widths))
        target_h = int(np.median(heights))
    else:
        raise ValueError(f"Unknown normalization mode: {mode}")
    
    # Calculate pivot and offset for each frame
    normalized = []
    for frame in frames:
        norm_frame = frame.copy()
        
        if target_w and target_h:
            # Calculate offset to center the original frame in the normalized size
            offset_x, offset_y = _calculate_pivot_offset(
                original_w=frame["w"],
                original_h=frame["h"],
                target_w=target_w,
                target_h=target_h,
                pivot=pivot
            )
            
            norm_frame["normalized_w"] = target_w
            norm_frame["normalized_h"] = target_h
            norm_frame["offset_x"] = offset_x
            norm_frame["offset_y"] = offset_y
        
        # Calculate pivot point in original frame
        pivot_x, pivot_y = _get_pivot_point(frame["w"], frame["h"], pivot)
        norm_frame["pivot"] = {"x": pivot_x, "y": pivot_y}
        
        normalized.append(norm_frame)
    
    return {
        "mode": mode,
        "pivot": pivot,
        "original_sizes": {
            "min_w": min(widths),
            "max_w": max(widths),
            "min_h": min(heights),
            "max_h": max(heights),
            "avg_w": int(np.mean(widths)),
            "avg_h": int(np.mean(heights))
        },
        "normalized_size": {"w": target_w, "h": target_h} if target_w else None,
        "frames": normalized
    }


def _calculate_pivot_offset(
    original_w: int,
    original_h: int,
    target_w: int,
    target_h: int,
    pivot: str
) -> Tuple[int, int]:
    """
    Calculate offset to position original frame within normalized size.
    
    Returns offset from top-left of normalized rect to top-left of original.
    """
    if pivot == "center":
        offset_x = (target_w - original_w) // 2
        offset_y = (target_h - original_h) // 2
    elif pivot == "bottom_center":
        offset_x = (target_w - original_w) // 2
        offset_y = target_h - original_h
    elif pivot == "top_left":
        offset_x = 0
        offset_y = 0
    else:
        offset_x = 0
        offset_y = 0
    
    return offset_x, offset_y


def _get_pivot_point(w: int, h: int, pivot: str) -> Tuple[int, int]:
    """Get pivot point coordinates within a frame."""
    if pivot == "center":
        return w // 2, h // 2
    elif pivot == "bottom_center":
        return w // 2, h
    elif pivot == "top_left":
        return 0, 0
    else:
        return w // 2, h // 2


def apply_padding(
    frames: List[Dict],
    padding: int
) -> List[Dict]:
    """
    Apply uniform padding to all frames.
    
    Args:
        frames: List of frame dicts
        padding: Padding in pixels to add on all sides
    
    Returns:
        List of frames with adjusted coordinates
    """
    padded = []
    for frame in frames:
        pf = frame.copy()
        pf["x"] = frame["x"] - padding
        pf["y"] = frame["y"] - padding
        pf["w"] = frame["w"] + padding * 2
        pf["h"] = frame["h"] + padding * 2
        pf["padding"] = padding
        padded.append(pf)
    
    return padded


def calculate_animation_bounds(
    frames: List[Dict],
    animation: Dict
) -> Dict[str, Any]:
    """
    Calculate the bounding box that contains all frames of an animation.
    
    Useful for creating a unified AtlasTexture region.
    """
    frame_ids = animation.get("frameIds", [])
    frame_map = {f["id"]: f for f in frames}
    
    anim_frames = [frame_map[fid] for fid in frame_ids if fid in frame_map]
    
    if not anim_frames:
        return {"error": "No frames found for animation"}
    
    min_x = min(f["x"] for f in anim_frames)
    min_y = min(f["y"] for f in anim_frames)
    max_x = max(f["x"] + f["w"] for f in anim_frames)
    max_y = max(f["y"] + f["h"] for f in anim_frames)
    
    return {
        "bounds": {
            "x": min_x,
            "y": min_y,
            "w": max_x - min_x,
            "h": max_y - min_y
        },
        "frame_count": len(anim_frames),
        "frame_sizes": {
            "min_w": min(f["w"] for f in anim_frames),
            "max_w": max(f["w"] for f in anim_frames),
            "min_h": min(f["h"] for f in anim_frames),
            "max_h": max(f["h"] for f in anim_frames)
        }
    }


def suggest_grid_layout(frames: List[Dict]) -> Dict[str, Any]:
    """
    Analyze frames and suggest if they follow a grid pattern.
    
    Returns suggested hframes/vframes for Sprite2D.
    """
    if not frames:
        return {"is_grid": False, "reason": "No frames"}
    
    # Check for consistent sizes
    sizes = [(f["w"], f["h"]) for f in frames]
    unique_sizes = set(sizes)
    
    if len(unique_sizes) > len(frames) * 0.2:
        return {
            "is_grid": False,
            "reason": "Too many different frame sizes",
            "unique_sizes": len(unique_sizes)
        }
    
    # Find most common size
    common_size = max(set(sizes), key=sizes.count)
    matching = sum(1 for s in sizes if s == common_size)
    
    if matching < len(frames) * 0.8:
        return {
            "is_grid": False,
            "reason": "Less than 80% of frames match common size"
        }
    
    # Detect grid dimensions
    xs = sorted(set(f["x"] for f in frames))
    ys = sorted(set(f["y"] for f in frames))
    
    # Check if X positions are evenly spaced
    if len(xs) > 1:
        x_gaps = [xs[i+1] - xs[i] for i in range(len(xs)-1)]
        x_consistent = max(x_gaps) - min(x_gaps) < common_size[0] * 0.2
    else:
        x_consistent = True
    
    # Check if Y positions are evenly spaced
    if len(ys) > 1:
        y_gaps = [ys[i+1] - ys[i] for i in range(len(ys)-1)]
        y_consistent = max(y_gaps) - min(y_gaps) < common_size[1] * 0.2
    else:
        y_consistent = True
    
    is_grid = x_consistent and y_consistent
    
    return {
        "is_grid": is_grid,
        "common_size": {"w": common_size[0], "h": common_size[1]},
        "columns": len(xs),
        "rows": len(ys),
        "hframes": len(xs) if is_grid else None,
        "vframes": len(ys) if is_grid else None,
        "x_consistent": x_consistent,
        "y_consistent": y_consistent
    }
