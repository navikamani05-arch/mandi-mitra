"""Pretrained zero-shot crop detection and a non-certified demo grade."""

from __future__ import annotations

from PIL import Image

from config.settings import CLIP_MODEL_ID, SUPPORTED_CROPS, VISION_CONFIDENCE_THRESHOLD
from pipeline.models import VisionResult
from utils.image_utils import calculate_visual_metrics


class VisionModuleError(RuntimeError):
    """Raised when a locally cached vision model cannot be used."""


def _load_clip(model_path_or_id: str, local_files_only: bool):
    """Lazy import keeps price-only tests independent of ML dependencies."""
    try:
        from transformers import CLIPModel, CLIPProcessor
    except ImportError as error:  # pragma: no cover - depends on runtime install
        raise VisionModuleError("Install the vision dependencies listed in requirements.txt.") from error
    try:
        return (
            CLIPModel.from_pretrained(model_path_or_id, local_files_only=local_files_only),
            CLIPProcessor.from_pretrained(model_path_or_id, local_files_only=local_files_only),
        )
    except OSError as error:  # pragma: no cover - depends on local model cache
        raise VisionModuleError(
            "The CLIP model is not cached locally. Run scripts/cache_vision_model.py while online before demo day."
        ) from error


def _grade(confidence: float, color_uniformity: float, dark_region_fraction: float) -> str:
    score = 0
    score += 2 if confidence >= 0.80 else 1 if confidence >= 0.60 else 0
    score += 1 if color_uniformity >= 0.45 else 0
    score += 1 if dark_region_fraction <= 0.08 else 0
    return "A" if score >= 4 else "B" if score >= 2 else "C"


class VisionModule:
    """Classifies the four demo crops with cached `openai/clip-vit-base-patch32`."""

    def __init__(self, model_id: str = CLIP_MODEL_ID, confidence_threshold: float = VISION_CONFIDENCE_THRESHOLD):
        self.model_id = model_id
        self.confidence_threshold = confidence_threshold
        self._model = None
        self._processor = None

    def _ensure_loaded(self) -> None:
        if self._model is None or self._processor is None:
            self._model, self._processor = _load_clip(self.model_id, local_files_only=True)
            self._model.eval()

    def analyze(self, image: Image.Image) -> VisionResult:
        self._ensure_loaded()
        prompts = [f"a clear photo of fresh {crop}" for crop in SUPPORTED_CROPS]
        inputs = self._processor(text=prompts, images=image.convert("RGB"), return_tensors="pt", padding=True)
        import torch
        with torch.no_grad():
            probabilities = self._model(**inputs).logits_per_image.softmax(dim=1)[0]
        best_index = int(probabilities.argmax().item())
        confidence = float(probabilities[best_index].item())
        metrics = calculate_visual_metrics(image)
        crop = SUPPORTED_CROPS[best_index]
        reasoning = (
            f"Cached CLIP selected {crop} with {confidence:.0%} confidence.",
            f"Demo visual signals: colour uniformity {metrics.color_uniformity:.0%}; dark-region fraction {metrics.dark_region_fraction:.0%}.",
            "Grade is a demo heuristic, not a certified quality standard.",
        )
        if confidence < self.confidence_threshold:
            return VisionResult(None, confidence, None, True, reasoning + ("Confidence is too low; select the crop manually.",))
        return VisionResult(crop, confidence, _grade(confidence, metrics.color_uniformity, metrics.dark_region_fraction), False, reasoning)
