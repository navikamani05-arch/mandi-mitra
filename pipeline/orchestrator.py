"""Chains specialist modules and records their individual reasoning trail."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PIL import Image

from config.settings import FARM_LOCATION_PATH, PRICE_DATA_PATH, PROJECT_ROOT
from modules.decision import make_decision
from modules.messaging import draft_message
from modules.price_data import get_crop_price_summary, load_farm_locations, load_price_records
from modules.vision import VisionModule
from pipeline.models import PipelineResult
from utils.logging_utils import build_step_logger, log_step


class MandiMitraPipeline:
    def __init__(self, vision: Optional[VisionModule] = None, log_directory: Path = PROJECT_ROOT / "logs"):
        self.vision = vision or VisionModule()
        self.records = load_price_records(PRICE_DATA_PATH)
        self.locations = load_farm_locations(FARM_LOCATION_PATH)
        self.logger = build_step_logger(log_directory)

    def run(
        self,
        image: Image.Image,
        quantity_kg: float,
        language: str,
        location_id: str,
        manual_crop: str | None = None,
        on_step: Callable[[str, str], None] | None = None,
    ) -> PipelineResult:
        """Run every specialist module, optionally reporting completed UI stages."""
        def report(agent: str, summary: str) -> None:
            if on_step:
                on_step(agent, summary)

        vision = self.vision.analyze(
            image,
            on_model_download=lambda: report(
                "Vision Agent", "Downloading model, first run may take a minute."
            ),
        )
        crop = manual_crop or vision.crop
        trail: list[dict[str, object]] = [{"step": "vision", "result": vision.reasoning}]
        log_step(self.logger, "vision", {"crop": vision.crop, "confidence": vision.confidence, "manual_required": vision.requires_manual_crop_selection})
        detected_crop = vision.crop or "uncertain crop"
        detected_grade = vision.grade or "manual grade pending"
        report("Vision Agent", f"Detected {detected_crop}; grade {detected_grade}; {vision.confidence:.0%} confidence.")
        if crop is None:
            raise ValueError("Choose a crop manually because image confidence was too low.")
        if location_id not in self.locations:
            raise ValueError("Choose a valid demo farm location.")
        prices = get_crop_price_summary(self.records, crop, self.locations[location_id])
        trail.append({"step": "price_data", "as_of": prices.as_of_date.isoformat(), "range": [prices.today_min_price, prices.today_max_price]})
        log_step(self.logger, "price_data", {"crop": crop, "as_of": prices.as_of_date.isoformat()})
        report(
            "Price Data Agent",
            f"Loaded 7-day mock price history for {crop} across {len(prices.market_snapshots)} markets.",
        )
        grade = vision.grade or "B"
        decision = make_decision(prices, quantity_kg, grade)
        trail.append({"step": "decision", "result": decision.reasoning})
        log_step(self.logger, "decision", {"recommendation": decision.recommendation, "market": decision.recommended_market})
        action = "WAIT" if decision.recommendation == "wait" else "SELL NOW"
        best = next(item for item in decision.market_comparisons if item.market == decision.recommended_market)
        report("Decision Agent", f"{action} recommendation: {decision.recommended_market}; two-day estimate {best.projected_change_percent:+.1f}%.")
        message = draft_message(language, crop, quantity_kg, grade, decision.recommended_market, decision.suggested_asking_price_inr_per_quintal)
        trail.append({"step": "message", "language": language})
        log_step(self.logger, "message", {"language": language})
        report("Message Agent", f"Drafted an offline {language} WhatsApp-style message.")
        return PipelineResult(vision, prices, decision, message, tuple(trail))
