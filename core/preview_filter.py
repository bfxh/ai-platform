"""
Preview-aware file filter for 3D modeling assets.
Detects whether file formats are visually previewable and filters out
non-previewable formats at import/crawl time to save storage.
"""
from pathlib import Path
from typing import Optional

# Formats known to be previewable in common 3D viewers (glTF, Blender, Unreal, etc.)
KNOWN_PREVIEWABLE: set = {
    # glTF / GLB (universal)
    ".gltf", ".glb",
    # Standard interchange
    ".obj", ".fbx", ".stl", ".ply", ".dae",
    # USD (Universal Scene Description)
    ".usd", ".usda", ".usdc", ".usdz",
    # Blender
    ".blend",
}

# Formats known to NOT be previewable or rarely supported
KNOWN_NON_PREVIEWABLE: set = {
    # Raw / intermediate formats
    ".raw", ".vox", ".3ds", ".max", ".ma", ".mb",
    # CAD formats (need conversion)
    ".step", ".stp", ".iges", ".igs", ".dwg", ".dxf",
    # Game-specific compressed
    ".mesh", ".mdl", ".md2", ".md3", ".md5mesh",
    # Point clouds (specialized viewers)
    ".las", ".laz", ".e57", ".pts", ".ptx",
    # Procedural / shader
    ".hda", ".otl", ".hip", ".nk",
}


class PreviewFilter:
    """Filters files based on 3D preview compatibility."""

    def is_previewable(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        if ext in KNOWN_PREVIEWABLE:
            return True
        if ext in KNOWN_NON_PREVIEWABLE:
            return False
        # Unknown formats: conservative — mark as non-previewable
        return False

    def filter_non_previewable(self, files: list) -> tuple[list, list]:
        previewable = []
        non_previewable = []
        for f in files:
            path = f if isinstance(f, str) else str(f)
            if self.is_previewable(path):
                previewable.append(path)
            else:
                non_previewable.append(path)
        return previewable, non_previewable

    def get_format_category(self, file_path: str) -> Optional[str]:
        ext = Path(file_path).suffix.lower()
        if ext in KNOWN_PREVIEWABLE:
            return "previewable"
        if ext in KNOWN_NON_PREVIEWABLE:
            return "non_previewable"
        return "unknown"
