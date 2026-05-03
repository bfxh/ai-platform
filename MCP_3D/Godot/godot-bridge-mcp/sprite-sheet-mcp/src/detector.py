"""Frame detection module using OpenCV for spritesheet analysis."""

import os
import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional, Tuple


def analyze_sheet(
    image_path: str,
    mode: str = "auto",
    bg_color: Optional[Dict] = None,
    min_area: int = 64,
    merge_distance: int = 4
) -> Dict[str, Any]:
    """
    Analyze a spritesheet and detect individual frames.
    
    Args:
        image_path: Path to the spritesheet image
        mode: Detection mode - "auto", "alpha", or "bg_color"
        bg_color: Background color dict {r, g, b, tolerance} for bg_color mode
        min_area: Minimum pixel area to consider a valid frame
        merge_distance: Max distance to merge nearby components
    
    Returns:
        Dict with sheet info and detected frames
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Load image with alpha channel if present
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    height, width = img.shape[:2]
    has_alpha = img.shape[2] == 4 if len(img.shape) > 2 else False
    
    # Determine detection mode
    actual_mode = mode
    if mode == "auto":
        actual_mode = "alpha" if has_alpha else "bg_color"
    
    # Create binary mask based on mode
    if actual_mode == "alpha" and has_alpha:
        mask = _create_alpha_mask(img)
    else:
        mask = _create_bg_color_mask(img, bg_color)
    
    # Find connected components
    raw_rects = _find_connected_components(mask, min_area)
    
    # Merge nearby components
    merged_rects = _merge_nearby_rects(raw_rects, merge_distance)
    
    # Create frame objects
    frames = []
    for i, rect in enumerate(merged_rects):
        x, y, w, h = rect
        frames.append({
            "id": i,
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h)
        })
    
    return {
        "sheet": {
            "width": width,
            "height": height,
            "has_alpha": has_alpha,
            "path": image_path
        },
        "detection": {
            "mode": actual_mode,
            "min_area": min_area,
            "merge_distance": merge_distance,
            "raw_components": len(raw_rects),
            "merged_frames": len(merged_rects)
        },
        "frames": frames
    }


def _create_alpha_mask(img: np.ndarray) -> np.ndarray:
    """Create binary mask from alpha channel."""
    alpha = img[:, :, 3]
    # Threshold: pixels with alpha > 10 are considered foreground
    _, mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
    return mask


def _create_bg_color_mask(img: np.ndarray, bg_color: Optional[Dict] = None) -> np.ndarray:
    """Create binary mask by detecting background color."""
    # Convert to RGB if needed
    if len(img.shape) > 2 and img.shape[2] == 4:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    elif len(img.shape) > 2:
        img_rgb = img
    else:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    if bg_color:
        # Use specified background color
        r, g, b = bg_color.get("r", 0), bg_color.get("g", 0), bg_color.get("b", 0)
        tolerance = bg_color.get("tolerance", 30)
        
        # Create color range
        lower = np.array([max(0, b - tolerance), max(0, g - tolerance), max(0, r - tolerance)])
        upper = np.array([min(255, b + tolerance), min(255, g + tolerance), min(255, r + tolerance)])
        
        bg_mask = cv2.inRange(img_rgb, lower, upper)
        mask = cv2.bitwise_not(bg_mask)
    else:
        # Auto-detect background color from corners
        corners = [
            img_rgb[0, 0],
            img_rgb[0, -1],
            img_rgb[-1, 0],
            img_rgb[-1, -1]
        ]
        
        # Use most common corner color as background
        bg_color_detected = max(set(map(tuple, corners)), key=list(map(tuple, corners)).count)
        b, g, r = bg_color_detected
        tolerance = 30
        
        lower = np.array([max(0, b - tolerance), max(0, g - tolerance), max(0, r - tolerance)])
        upper = np.array([min(255, b + tolerance), min(255, g + tolerance), min(255, r + tolerance)])
        
        bg_mask = cv2.inRange(img_rgb, lower, upper)
        mask = cv2.bitwise_not(bg_mask)
    
    return mask


def _find_connected_components(mask: np.ndarray, min_area: int) -> List[Tuple[int, int, int, int]]:
    """Find connected components and return bounding rectangles."""
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    rects = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= min_area:
            x, y, w, h = cv2.boundingRect(contour)
            rects.append((x, y, w, h))
    
    # Sort by Y then X for consistent ordering
    rects.sort(key=lambda r: (r[1], r[0]))
    
    return rects


def _merge_nearby_rects(rects: List[Tuple[int, int, int, int]], distance: int) -> List[Tuple[int, int, int, int]]:
    """Merge rectangles that are within distance pixels of each other."""
    if not rects or distance <= 0:
        return rects
    
    merged = list(rects)
    changed = True
    
    while changed:
        changed = False
        new_merged = []
        used = set()
        
        for i, rect1 in enumerate(merged):
            if i in used:
                continue
            
            x1, y1, w1, h1 = rect1
            current = rect1
            
            for j, rect2 in enumerate(merged):
                if i == j or j in used:
                    continue
                
                x2, y2, w2, h2 = rect2
                
                # Check if rects are close enough to merge
                cx1, cy1 = x1 + w1, y1 + h1  # Current rect end
                cx2, cy2 = x2 + w2, y2 + h2  # Other rect end
                
                # Expand rect1 by distance and check overlap
                exp_x1 = x1 - distance
                exp_y1 = y1 - distance
                exp_x2 = cx1 + distance
                exp_y2 = cy1 + distance
                
                # Check if rect2 overlaps with expanded rect1
                if not (x2 > exp_x2 or cx2 < exp_x1 or y2 > exp_y2 or cy2 < exp_y1):
                    # Merge: create bounding box of both
                    new_x = min(x1, x2)
                    new_y = min(y1, y2)
                    new_w = max(cx1, cx2) - new_x
                    new_h = max(cy1, cy2) - new_y
                    current = (new_x, new_y, new_w, new_h)
                    x1, y1, w1, h1 = current
                    used.add(j)
                    changed = True
            
            new_merged.append(current)
            used.add(i)
        
        merged = new_merged
    
    # Re-sort after merging
    merged.sort(key=lambda r: (r[1], r[0]))
    
    return merged


def slice_frames(
    image_path: str,
    frames: List[Dict],
    output_dir: str,
    export_mode: str = "png_frames",
    naming: str = "frame_{id}",
    padding: int = 0
) -> Dict[str, Any]:
    """
    Slice frames from spritesheet and export them.
    
    Args:
        image_path: Path to the spritesheet
        frames: List of frame dicts with id, x, y, w, h
        output_dir: Directory to save output
        export_mode: "png_frames" or "atlas_json"
        naming: Naming pattern for files
        padding: Padding to add around frames
    
    Returns:
        Dict with exported files info
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load image
    img = Image.open(image_path)
    
    exported = []
    
    if export_mode == "png_frames":
        for frame in frames:
            fid = frame["id"]
            x, y, w, h = frame["x"], frame["y"], frame["w"], frame["h"]
            
            # Crop with padding
            left = max(0, x - padding)
            top = max(0, y - padding)
            right = min(img.width, x + w + padding)
            bottom = min(img.height, y + h + padding)
            
            cropped = img.crop((left, top, right, bottom))
            
            # Generate filename
            filename = naming.replace("{id}", str(fid)) + ".png"
            filepath = os.path.join(output_dir, filename)
            
            cropped.save(filepath)
            exported.append({
                "id": fid,
                "path": filepath,
                "original_rect": {"x": x, "y": y, "w": w, "h": h},
                "exported_size": {"w": right - left, "h": bottom - top}
            })
    
    elif export_mode == "atlas_json":
        # Just export metadata, no actual slicing
        atlas_data = {
            "source": image_path,
            "frames": frames
        }
        
        json_path = os.path.join(output_dir, "atlas.json")
        import json
        with open(json_path, "w") as f:
            json.dump(atlas_data, f, indent=2)
        
        exported.append({
            "type": "atlas_json",
            "path": json_path
        })
    
    return {
        "export_mode": export_mode,
        "output_dir": output_dir,
        "frame_count": len(frames),
        "exported": exported
    }


def preview_layout(
    image_path: str,
    frames: List[Dict],
    animations: Optional[Dict] = None,
    output_path: str = None,
    show_labels: bool = True,
    show_dimensions: bool = False
) -> Dict[str, Any]:
    """
    Generate a preview image with bounding boxes overlaid.
    
    Args:
        image_path: Path to the spritesheet
        frames: List of frame dicts
        animations: Optional animation groups for color coding
        output_path: Path to save preview
        show_labels: Show frame ID labels
        show_dimensions: Show frame dimensions
    
    Returns:
        Dict with preview info
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Load image
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img.shape[2] == 4:
        # Convert BGRA to BGR for drawing
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    # Create color map for animations
    colors = [
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 0, 255),    # Red
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Yellow
        (128, 0, 255),  # Purple
        (255, 128, 0),  # Orange
    ]
    
    # Map frame IDs to animation colors
    frame_colors = {}
    if animations:
        for i, (anim_name, anim_data) in enumerate(animations.items()):
            color = colors[i % len(colors)]
            frame_ids = anim_data.get("frameIds", anim_data.get("frame_ids", []))
            for fid in frame_ids:
                frame_colors[fid] = color
    
    # Draw rectangles
    for frame in frames:
        fid = frame["id"]
        x, y, w, h = frame["x"], frame["y"], frame["w"], frame["h"]
        
        color = frame_colors.get(fid, (0, 255, 0))
        
        # Draw rectangle
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        
        # Draw label
        if show_labels:
            label = str(fid)
            if show_dimensions:
                label += f" ({w}x{h})"
            
            # Background for text
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.rectangle(img, (x, y - th - 4), (x + tw + 4, y), color, -1)
            cv2.putText(img, label, (x + 2, y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    
    # Save preview
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        cv2.imwrite(output_path, img)
    
    return {
        "output_path": output_path,
        "frame_count": len(frames),
        "animation_count": len(animations) if animations else 0,
        "dimensions": {"w": img.shape[1], "h": img.shape[0]}
    }


def remove_background(
    image_path: str,
    output_path: str,
    bg_color: Optional[Dict] = None,
    tolerance: int = 30,
    feather: int = 0,
    mode: str = "color"
) -> Dict[str, Any]:
    """
    Remove background from image and save with transparency.
    
    Args:
        image_path: Path to the source image
        output_path: Path to save the result (PNG)
        bg_color: Background color {r, g, b} - auto-detected if not provided
        tolerance: Color tolerance for background detection (0-255)
        feather: Feather/blur amount for edge smoothing (0-10)
        mode: "color" (remove specific color) or "corners" (detect from corners)
    
    Returns:
        Dict with result info
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Load image
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    height, width = img.shape[:2]
    
    # Convert to BGRA if needed
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    
    # Get background color
    if bg_color:
        bg_b, bg_g, bg_r = bg_color.get("b", 0), bg_color.get("g", 0), bg_color.get("r", 0)
    else:
        # Auto-detect from corners
        corners = [
            img[0, 0, :3],
            img[0, -1, :3],
            img[-1, 0, :3],
            img[-1, -1, :3]
        ]
        # Most common corner color
        corner_tuples = [tuple(c) for c in corners]
        bg_bgr = max(set(corner_tuples), key=corner_tuples.count)
        bg_b, bg_g, bg_r = bg_bgr
    
    # Create mask for background
    img_bgr = img[:, :, :3]
    lower = np.array([max(0, bg_b - tolerance), max(0, bg_g - tolerance), max(0, bg_r - tolerance)])
    upper = np.array([min(255, bg_b + tolerance), min(255, bg_g + tolerance), min(255, bg_r + tolerance)])
    
    bg_mask = cv2.inRange(img_bgr, lower, upper)
    
    # Apply feathering if requested
    if feather > 0:
        kernel_size = feather * 2 + 1
        bg_mask = cv2.GaussianBlur(bg_mask, (kernel_size, kernel_size), 0)
    
    # Create alpha channel (inverse of background mask)
    alpha = cv2.bitwise_not(bg_mask)
    
    # Apply alpha to image
    img[:, :, 3] = alpha
    
    # Save result
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, img)
    
    # Count transparent pixels
    transparent_pixels = np.sum(alpha == 0)
    total_pixels = width * height
    
    return {
        "ok": True,
        "output_path": output_path,
        "dimensions": {"w": width, "h": height},
        "background_color": {"r": int(bg_r), "g": int(bg_g), "b": int(bg_b)},
        "tolerance": tolerance,
        "feather": feather,
        "transparent_pixels": int(transparent_pixels),
        "transparency_percent": round(transparent_pixels / total_pixels * 100, 2)
    }


def analyze_grid(
    image_path: str,
    columns: int,
    rows: int,
    offset_x: int = 0,
    offset_y: int = 0,
    spacing_x: int = 0,
    spacing_y: int = 0,
    margin_x: int = 0,
    margin_y: int = 0
) -> Dict[str, Any]:
    """
    Analyze spritesheet using fixed grid parameters.
    
    Args:
        image_path: Path to the spritesheet
        columns: Number of columns (hframes)
        rows: Number of rows (vframes)
        offset_x: X offset from left edge to start
        offset_y: Y offset from top edge to start
        spacing_x: Horizontal spacing between frames
        spacing_y: Vertical spacing between frames
        margin_x: Horizontal margin inside each cell
        margin_y: Vertical margin inside each cell
    
    Returns:
        Dict with grid info and frames
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    height, width = img.shape[:2]
    
    # Calculate cell size
    usable_width = width - offset_x - (spacing_x * (columns - 1))
    usable_height = height - offset_y - (spacing_y * (rows - 1))
    
    cell_width = usable_width // columns
    cell_height = usable_height // rows
    
    # Generate frames
    frames = []
    frame_id = 0
    
    for row in range(rows):
        for col in range(columns):
            x = offset_x + col * (cell_width + spacing_x) + margin_x
            y = offset_y + row * (cell_height + spacing_y) + margin_y
            w = cell_width - (margin_x * 2)
            h = cell_height - (margin_y * 2)
            
            frames.append({
                "id": frame_id,
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
                "row": row,
                "col": col
            })
            frame_id += 1
    
    return {
        "sheet": {
            "width": width,
            "height": height,
            "path": image_path
        },
        "grid": {
            "columns": columns,
            "rows": rows,
            "cell_width": cell_width,
            "cell_height": cell_height,
            "offset": {"x": offset_x, "y": offset_y},
            "spacing": {"x": spacing_x, "y": spacing_y},
            "margin": {"x": margin_x, "y": margin_y}
        },
        "frame_count": len(frames),
        "frames": frames
    }


def detect_grid(
    image_path: str,
    min_cell_size: int = 16,
    max_cell_size: int = 512
) -> Dict[str, Any]:
    """
    Auto-detect if spritesheet has a regular grid pattern.
    
    Args:
        image_path: Path to the spritesheet
        min_cell_size: Minimum expected cell size
        max_cell_size: Maximum expected cell size
    
    Returns:
        Dict with detected grid info or detection failure
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    height, width = img.shape[:2]
    has_alpha = img.shape[2] == 4 if len(img.shape) > 2 else False
    
    # Create binary mask
    if has_alpha:
        mask = _create_alpha_mask(img)
    else:
        mask = _create_bg_color_mask(img, None)
    
    # Find all frames first
    raw_rects = _find_connected_components(mask, min_cell_size * min_cell_size // 4)
    
    if len(raw_rects) < 2:
        return {
            "is_grid": False,
            "reason": "Not enough sprites detected",
            "sprite_count": len(raw_rects)
        }
    
    # Analyze frame sizes
    widths = [r[2] for r in raw_rects]
    heights = [r[3] for r in raw_rects]
    
    # Check size consistency
    width_variance = np.std(widths) / np.mean(widths) if np.mean(widths) > 0 else 1
    height_variance = np.std(heights) / np.mean(heights) if np.mean(heights) > 0 else 1
    
    size_consistent = width_variance < 0.15 and height_variance < 0.15
    
    # Analyze X positions to find columns
    x_positions = sorted(set(r[0] for r in raw_rects))
    y_positions = sorted(set(r[1] for r in raw_rects))
    
    # Check if positions are evenly spaced
    def check_spacing(positions):
        if len(positions) < 2:
            return True, 0
        gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
        if not gaps:
            return True, 0
        avg_gap = np.mean(gaps)
        variance = np.std(gaps) / avg_gap if avg_gap > 0 else 1
        return variance < 0.15, int(avg_gap)
    
    x_regular, x_spacing = check_spacing(x_positions)
    y_regular, y_spacing = check_spacing(y_positions)
    
    # Convert numpy bools to Python bools for JSON serialization
    x_regular = bool(x_regular)
    y_regular = bool(y_regular)
    size_consistent = bool(size_consistent)
    
    is_grid = size_consistent and (x_regular or len(x_positions) == 1) and (y_regular or len(y_positions) == 1)
    
    result = {
        "is_grid": bool(is_grid),
        "confidence": "high" if is_grid else "low",
        "sprite_count": len(raw_rects),
        "detected_columns": len(x_positions),
        "detected_rows": len(y_positions),
        "avg_frame_size": {
            "w": int(np.mean(widths)),
            "h": int(np.mean(heights))
        },
        "size_variance": {
            "w": round(float(width_variance), 3),
            "h": round(float(height_variance), 3)
        },
        "spacing": {
            "x": x_spacing,
            "y": y_spacing
        },
        "x_regular": x_regular,
        "y_regular": y_regular
    }
    
    if is_grid:
        # Suggest grid parameters
        result["suggested_params"] = {
            "columns": len(x_positions),
            "rows": len(y_positions),
            "offset_x": min(x_positions) if x_positions else 0,
            "offset_y": min(y_positions) if y_positions else 0,
            "spacing_x": x_spacing - int(np.mean(widths)) if x_spacing > int(np.mean(widths)) else 0,
            "spacing_y": y_spacing - int(np.mean(heights)) if y_spacing > int(np.mean(heights)) else 0
        }
    
    return result


def filter_frames(
    frames: List[Dict],
    min_width: Optional[int] = None,
    max_width: Optional[int] = None,
    min_height: Optional[int] = None,
    max_height: Optional[int] = None,
    min_area: Optional[int] = None,
    max_area: Optional[int] = None,
    region: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Filter frames by size or region constraints.
    
    Args:
        frames: List of frame dicts
        min_width: Minimum frame width
        max_width: Maximum frame width
        min_height: Minimum frame height
        max_height: Maximum frame height
        min_area: Minimum frame area
        max_area: Maximum frame area
        region: Region constraint {x, y, w, h} - only frames inside
    
    Returns:
        Dict with filtered frames and stats
    """
    filtered = []
    removed = []
    
    for frame in frames:
        w, h = frame["w"], frame["h"]
        x, y = frame["x"], frame["y"]
        area = w * h
        
        keep = True
        reason = None
        
        # Size filters
        if min_width and w < min_width:
            keep = False
            reason = f"width {w} < {min_width}"
        elif max_width and w > max_width:
            keep = False
            reason = f"width {w} > {max_width}"
        elif min_height and h < min_height:
            keep = False
            reason = f"height {h} < {min_height}"
        elif max_height and h > max_height:
            keep = False
            reason = f"height {h} > {max_height}"
        elif min_area and area < min_area:
            keep = False
            reason = f"area {area} < {min_area}"
        elif max_area and area > max_area:
            keep = False
            reason = f"area {area} > {max_area}"
        
        # Region filter
        if keep and region:
            rx, ry, rw, rh = region["x"], region["y"], region["w"], region["h"]
            if not (x >= rx and y >= ry and x + w <= rx + rw and y + h <= ry + rh):
                keep = False
                reason = "outside region"
        
        if keep:
            filtered.append(frame)
        else:
            removed.append({"frame": frame, "reason": reason})
    
    # Re-index frames
    for i, f in enumerate(filtered):
        f["id"] = i
    
    return {
        "original_count": len(frames),
        "filtered_count": len(filtered),
        "removed_count": len(removed),
        "frames": filtered,
        "removed": removed[:10]  # Only show first 10 removed
    }


def adjust_frames(
    frames: List[Dict],
    offset_x: int = 0,
    offset_y: int = 0,
    expand_x: int = 0,
    expand_y: int = 0,
    padding: int = 0,
    uniform_size: bool = False
) -> Dict[str, Any]:
    """
    Adjust frame positions and sizes.
    
    Args:
        frames: List of frame dicts
        offset_x: Add to all X positions
        offset_y: Add to all Y positions
        expand_x: Expand width (negative to shrink)
        expand_y: Expand height (negative to shrink)
        padding: Add uniform padding to all sides
        uniform_size: Make all frames the same size (use max)
    
    Returns:
        Dict with adjusted frames
    """
    if not frames:
        return {"frames": [], "adjustments": {}}
    
    adjusted = []
    
    # Calculate max size if uniform
    max_w = max(f["w"] for f in frames) if uniform_size else 0
    max_h = max(f["h"] for f in frames) if uniform_size else 0
    
    for frame in frames:
        new_frame = frame.copy()
        
        # Base adjustments
        new_frame["x"] = frame["x"] + offset_x - padding - (expand_x // 2)
        new_frame["y"] = frame["y"] + offset_y - padding - (expand_y // 2)
        new_frame["w"] = frame["w"] + expand_x + (padding * 2)
        new_frame["h"] = frame["h"] + expand_y + (padding * 2)
        
        # Uniform size
        if uniform_size:
            # Center the frame in the max box
            diff_w = max_w - frame["w"]
            diff_h = max_h - frame["h"]
            new_frame["x"] = frame["x"] + offset_x - (diff_w // 2)
            new_frame["y"] = frame["y"] + offset_y - (diff_h // 2)
            new_frame["w"] = max_w
            new_frame["h"] = max_h
        
        # Ensure positive values
        new_frame["x"] = max(0, new_frame["x"])
        new_frame["y"] = max(0, new_frame["y"])
        new_frame["w"] = max(1, new_frame["w"])
        new_frame["h"] = max(1, new_frame["h"])
        
        adjusted.append(new_frame)
    
    return {
        "frame_count": len(adjusted),
        "adjustments": {
            "offset": {"x": offset_x, "y": offset_y},
            "expand": {"x": expand_x, "y": expand_y},
            "padding": padding,
            "uniform_size": uniform_size,
            "uniform_dimensions": {"w": max_w, "h": max_h} if uniform_size else None
        },
        "frames": adjusted
    }


def sample_colors(
    image_path: str,
    sample_points: Optional[List[Dict]] = None,
    sample_corners: bool = True,
    sample_edges: bool = False,
    sample_count: int = 10
) -> Dict[str, Any]:
    """
    Sample colors from specific points or regions of the image.
    
    Args:
        image_path: Path to the image
        sample_points: List of {x, y} points to sample
        sample_corners: Sample from corners
        sample_edges: Sample from edges
        sample_count: Number of samples per edge/region
    
    Returns:
        Dict with sampled colors and analysis
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    height, width = img.shape[:2]
    has_alpha = img.shape[2] == 4 if len(img.shape) > 2 else False
    
    samples = []
    
    # Sample corners
    if sample_corners:
        corners = [
            (0, 0, "top_left"),
            (width - 1, 0, "top_right"),
            (0, height - 1, "bottom_left"),
            (width - 1, height - 1, "bottom_right")
        ]
        for x, y, name in corners:
            pixel = img[y, x]
            if has_alpha:
                b, g, r, a = pixel
            else:
                b, g, r = pixel[:3]
                a = 255
            samples.append({
                "location": name,
                "x": x, "y": y,
                "color": {"r": int(r), "g": int(g), "b": int(b), "a": int(a)},
                "hex": f"#{int(r):02x}{int(g):02x}{int(b):02x}"
            })
    
    # Sample edges
    if sample_edges:
        edge_points = []
        step = max(1, width // sample_count)
        for i in range(0, width, step):
            edge_points.append((i, 0, "top"))
            edge_points.append((i, height - 1, "bottom"))
        step = max(1, height // sample_count)
        for i in range(0, height, step):
            edge_points.append((0, i, "left"))
            edge_points.append((width - 1, i, "right"))
        
        for x, y, edge in edge_points:
            pixel = img[y, x]
            if has_alpha:
                b, g, r, a = pixel
            else:
                b, g, r = pixel[:3]
                a = 255
            samples.append({
                "location": edge,
                "x": x, "y": y,
                "color": {"r": int(r), "g": int(g), "b": int(b), "a": int(a)},
                "hex": f"#{int(r):02x}{int(g):02x}{int(b):02x}"
            })
    
    # Sample custom points
    if sample_points:
        for point in sample_points:
            x, y = int(point["x"]), int(point["y"])
            if 0 <= x < width and 0 <= y < height:
                pixel = img[y, x]
                if has_alpha:
                    b, g, r, a = pixel
                else:
                    b, g, r = pixel[:3]
                    a = 255
                samples.append({
                    "location": "custom",
                    "x": x, "y": y,
                    "color": {"r": int(r), "g": int(g), "b": int(b), "a": int(a)},
                    "hex": f"#{int(r):02x}{int(g):02x}{int(b):02x}"
                })
    
    # Analyze most common colors
    colors_only = [s["hex"] for s in samples]
    from collections import Counter
    color_counts = Counter(colors_only)
    most_common = color_counts.most_common(5)
    
    # Find most likely background color
    likely_bg = most_common[0][0] if most_common else None
    likely_bg_rgb = None
    if likely_bg:
        likely_bg_rgb = {
            "r": int(likely_bg[1:3], 16),
            "g": int(likely_bg[3:5], 16),
            "b": int(likely_bg[5:7], 16)
        }
    
    return {
        "dimensions": {"w": width, "h": height},
        "has_alpha": has_alpha,
        "sample_count": len(samples),
        "samples": samples[:20],  # Limit output
        "color_frequency": [{"hex": h, "count": c} for h, c in most_common],
        "likely_background": {
            "hex": likely_bg,
            "rgb": likely_bg_rgb
        }
    }
