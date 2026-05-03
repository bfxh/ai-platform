"""Animation grouping module for organizing frames into animations."""

import numpy as np
from typing import List, Dict, Any, Optional
from collections import defaultdict


def group_animations(
    frames: List[Dict],
    grouping_mode: str = "rows",
    row_tolerance: int = 10,
    expected_animations: Optional[int] = None,
    ordering: str = "x_asc"
) -> Dict[str, Any]:
    """
    Group frames into animations based on spatial analysis.
    
    Args:
        frames: List of frame dicts with id, x, y, w, h
        grouping_mode: Strategy - "rows", "columns", "grid", "spatial_cluster"
        row_tolerance: Y-axis tolerance for row grouping
        expected_animations: Hint for number of animations (for clustering)
        ordering: Order frames within groups - "x_asc", "y_asc", "id"
    
    Returns:
        Dict with animations and metadata
    """
    if not frames:
        return {"animations": {}, "frame_count": 0, "notes": ["No frames provided"]}
    
    if grouping_mode == "rows":
        groups = _group_by_rows(frames, row_tolerance)
    elif grouping_mode == "columns":
        groups = _group_by_columns(frames, row_tolerance)
    elif grouping_mode == "grid":
        groups = _group_by_grid(frames)
    elif grouping_mode == "spatial_cluster":
        groups = _group_by_spatial_cluster(frames, expected_animations)
    else:
        raise ValueError(f"Unknown grouping mode: {grouping_mode}")
    
    # Order frames within each group
    for group_name, group_data in groups.items():
        frame_ids = group_data["frameIds"]
        frame_map = {f["id"]: f for f in frames}
        
        if ordering == "x_asc":
            frame_ids.sort(key=lambda fid: frame_map[fid]["x"])
        elif ordering == "y_asc":
            frame_ids.sort(key=lambda fid: frame_map[fid]["y"])
        elif ordering == "id":
            frame_ids.sort()
        
        group_data["frameIds"] = frame_ids
    
    return {
        "grouping_mode": grouping_mode,
        "frame_count": len(frames),
        "animation_count": len(groups),
        "animations": groups
    }


def _group_by_rows(frames: List[Dict], tolerance: int) -> Dict[str, Dict]:
    """Group frames by their Y position (rows)."""
    if not frames:
        return {}
    
    # Sort frames by Y position
    sorted_frames = sorted(frames, key=lambda f: f["y"])
    
    groups = {}
    current_group = []
    current_y = sorted_frames[0]["y"]
    group_idx = 0
    
    for frame in sorted_frames:
        if abs(frame["y"] - current_y) <= tolerance:
            current_group.append(frame["id"])
        else:
            # Save current group
            if current_group:
                groups[f"anim_{group_idx:02d}"] = {
                    "frameIds": current_group,
                    "fps": 10,
                    "loop": True
                }
                group_idx += 1
            
            # Start new group
            current_group = [frame["id"]]
            current_y = frame["y"]
    
    # Save last group
    if current_group:
        groups[f"anim_{group_idx:02d}"] = {
            "frameIds": current_group,
            "fps": 10,
            "loop": True
        }
    
    return groups


def _group_by_columns(frames: List[Dict], tolerance: int) -> Dict[str, Dict]:
    """Group frames by their X position (columns)."""
    if not frames:
        return {}
    
    # Sort frames by X position
    sorted_frames = sorted(frames, key=lambda f: f["x"])
    
    groups = {}
    current_group = []
    current_x = sorted_frames[0]["x"]
    group_idx = 0
    
    for frame in sorted_frames:
        if abs(frame["x"] - current_x) <= tolerance:
            current_group.append(frame["id"])
        else:
            # Save current group
            if current_group:
                groups[f"anim_{group_idx:02d}"] = {
                    "frameIds": current_group,
                    "fps": 10,
                    "loop": True
                }
                group_idx += 1
            
            # Start new group
            current_group = [frame["id"]]
            current_x = frame["x"]
    
    # Save last group
    if current_group:
        groups[f"anim_{group_idx:02d}"] = {
            "frameIds": current_group,
            "fps": 10,
            "loop": True
        }
    
    return groups


def _group_by_grid(frames: List[Dict]) -> Dict[str, Dict]:
    """Detect grid structure and group by rows."""
    if not frames:
        return {}
    
    # Find common frame sizes
    sizes = [(f["w"], f["h"]) for f in frames]
    common_size = max(set(sizes), key=sizes.count)
    
    # Use common height as row tolerance
    tolerance = common_size[1] // 2
    
    return _group_by_rows(frames, tolerance)


def _group_by_spatial_cluster(
    frames: List[Dict],
    expected_animations: Optional[int] = None
) -> Dict[str, Dict]:
    """
    Group frames using spatial clustering (DBSCAN or KMeans).
    
    Best for chaotic/irregular spritesheets.
    """
    if not frames:
        return {}
    
    try:
        from sklearn.cluster import DBSCAN, KMeans
    except ImportError:
        # Fallback to simple row grouping if sklearn not available
        return _group_by_rows(frames, 20)
    
    # Create feature matrix: center Y position (primary), center X (secondary)
    centers = np.array([
        [f["y"] + f["h"] / 2, f["x"] + f["w"] / 2]
        for f in frames
    ])
    
    if expected_animations and expected_animations > 0:
        # Use KMeans if we know how many animations to expect
        n_clusters = min(expected_animations, len(frames))
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = clusterer.fit_predict(centers)
    else:
        # Use DBSCAN for automatic cluster detection
        # Estimate eps based on average frame height
        avg_height = np.mean([f["h"] for f in frames])
        eps = avg_height * 0.8
        
        clusterer = DBSCAN(eps=eps, min_samples=1)
        labels = clusterer.fit_predict(centers)
    
    # Group frames by cluster label
    groups = defaultdict(list)
    for i, label in enumerate(labels):
        if label >= 0:  # Ignore noise (-1) in DBSCAN
            groups[label].append(frames[i]["id"])
    
    # Convert to output format
    result = {}
    for i, (label, frame_ids) in enumerate(sorted(groups.items())):
        result[f"anim_{i:02d}"] = {
            "frameIds": frame_ids,
            "fps": 10,
            "loop": True
        }
    
    return result


def suggest_animation_names(
    frames: List[Dict],
    animations: Dict[str, Dict]
) -> Dict[str, str]:
    """
    Suggest animation names based on frame characteristics.
    
    Returns mapping from generic names to suggested names.
    """
    suggestions = {}
    
    # Common animation patterns based on frame count
    count_patterns = {
        1: ["idle", "static", "single"],
        2: ["blink", "toggle", "switch"],
        3: ["idle", "walk_start", "effect"],
        4: ["walk", "idle", "attack"],
        6: ["walk", "run", "idle"],
        8: ["walk", "run", "attack"],
    }
    
    # Suggest based on row position
    sorted_anims = sorted(
        animations.items(),
        key=lambda x: _get_avg_y(frames, x[1]["frameIds"])
    )
    
    common_names = ["idle", "walk", "run", "jump", "attack", "hurt", "death", "special"]
    
    for i, (anim_name, anim_data) in enumerate(sorted_anims):
        if i < len(common_names):
            suggestions[anim_name] = common_names[i]
        else:
            suggestions[anim_name] = f"animation_{i}"
    
    return suggestions


def _get_avg_y(frames: List[Dict], frame_ids: List[int]) -> float:
    """Get average Y position of frames."""
    frame_map = {f["id"]: f for f in frames}
    y_values = [frame_map[fid]["y"] for fid in frame_ids if fid in frame_map]
    return np.mean(y_values) if y_values else 0
