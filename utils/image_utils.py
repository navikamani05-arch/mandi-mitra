"""Deliberately simple image signals for the clearly-labelled demo grade."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class VisualMetrics:
    color_uniformity: float
    dark_region_fraction: float


def calculate_visual_metrics(image: Image.Image) -> VisualMetrics:
    """Return non-diagnostic colour and dark-pixel signals from an image."""
    rgb = np.asarray(image.convert("RGB").resize((224, 224)), dtype=np.float32) / 255.0
    saturation_proxy = rgb.max(axis=2) - rgb.min(axis=2)
    color_uniformity = float(1.0 - min(saturation_proxy.std() / 0.30, 1.0))
    brightness = rgb.mean(axis=2)
    dark_region_fraction = float((brightness < 0.16).mean())
    return VisualMetrics(color_uniformity=color_uniformity, dark_region_fraction=dark_region_fraction)
