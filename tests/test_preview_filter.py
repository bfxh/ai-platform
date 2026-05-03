"""Tests for preview_filter.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.preview_filter import PreviewFilter, KNOWN_PREVIEWABLE, KNOWN_NON_PREVIEWABLE


class TestPreviewFilter:
    def setup_method(self):
        self.filter = PreviewFilter()

    def test_is_previewable_gltf(self):
        assert self.filter.is_previewable("model.gltf") is True
        assert self.filter.is_previewable("model.glb") is True

    def test_is_previewable_obj_fbx(self):
        assert self.filter.is_previewable("model.obj") is True
        assert self.filter.is_previewable("model.fbx") is True

    def test_is_not_previewable_cad(self):
        assert self.filter.is_previewable("model.step") is False
        assert self.filter.is_previewable("model.iges") is False
        assert self.filter.is_previewable("model.dwg") is False

    def test_is_not_previewable_point_cloud(self):
        assert self.filter.is_previewable("scan.las") is False
        assert self.filter.is_previewable("scan.e57") is False

    def test_unknown_format_returns_false(self):
        assert self.filter.is_previewable("model.xyz") is False
        assert self.filter.is_previewable("model.abc") is False

    def test_filter_non_previewable(self):
        files = [
            "model.glb",
            "model.step",
            "model.obj",
            "model.dwg",
            "model.fbx",
        ]
        previewable, non_previewable = self.filter.filter_non_previewable(files)
        assert set(previewable) == {"model.glb", "model.obj", "model.fbx"}
        assert set(non_previewable) == {"model.step", "model.dwg"}

    def test_get_format_category(self):
        assert self.filter.get_format_category("model.gltf") == "previewable"
        assert self.filter.get_format_category("model.step") == "non_previewable"
        assert self.filter.get_format_category("model.xyz") == "unknown"

    def test_known_sets_not_empty(self):
        assert len(KNOWN_PREVIEWABLE) > 5
        assert len(KNOWN_NON_PREVIEWABLE) > 5

    def test_no_overlap_between_sets(self):
        overlap = KNOWN_PREVIEWABLE & KNOWN_NON_PREVIEWABLE
        assert len(overlap) == 0, f"Overlapping formats: {overlap}"

    def test_case_insensitive(self):
        assert self.filter.is_previewable("MODEL.GLB") is True
        assert self.filter.is_previewable("Model.STEP") is False
