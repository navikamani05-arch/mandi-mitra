from PIL import Image

from modules import vision
from modules.vision import VisionModule, VisionModuleError, _grade
from utils.image_utils import calculate_visual_metrics


def test_demo_grade_policy_uses_confidence_and_visual_checks():
    assert _grade(0.90, 0.80, 0.02) == "A"
    assert _grade(0.65, 0.20, 0.12) == "C"


def test_visual_metrics_are_bounded_for_a_valid_image():
    metrics = calculate_visual_metrics(Image.new("RGB", (32, 32), "red"))
    assert 0 <= metrics.color_uniformity <= 1
    assert 0 <= metrics.dark_region_fraction <= 1


def test_vision_downloads_when_the_local_cache_is_unavailable(monkeypatch):
    attempts = []
    downloaded = []
    model = type("Model", (), {"eval": lambda self: None})()

    def fake_load(_model_id, local_files_only):
        attempts.append(local_files_only)
        if local_files_only:
            raise VisionModuleError("No cached model")
        return model, object()

    monkeypatch.setattr(vision, "_load_clip", fake_load)
    VisionModule()._ensure_loaded(on_model_download=lambda: downloaded.append(True))

    assert attempts == [True, False]
    assert downloaded == [True]
