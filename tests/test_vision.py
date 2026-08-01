from PIL import Image

from modules.vision import _grade
from utils.image_utils import calculate_visual_metrics


def test_demo_grade_policy_uses_confidence_and_visual_checks():
    assert _grade(0.90, 0.80, 0.02) == "A"
    assert _grade(0.65, 0.20, 0.12) == "C"


def test_visual_metrics_are_bounded_for_a_valid_image():
    metrics = calculate_visual_metrics(Image.new("RGB", (32, 32), "red"))
    assert 0 <= metrics.color_uniformity <= 1
    assert 0 <= metrics.dark_region_fraction <= 1
