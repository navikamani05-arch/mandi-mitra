"""Typed contracts shared by every module in the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal


Grade = Literal["A", "B", "C"]
Recommendation = Literal["sell_now", "wait"]


@dataclass(frozen=True)
class FarmLocation:
    """A demo location and its road distance to each supported market."""

    id: str
    display_name: str
    state: str
    distances_km: dict[str, float]
    latitude: float
    longitude: float


@dataclass(frozen=True)
class PriceRecord:
    """One crop-market price observation, quoted in INR per quintal."""

    record_date: date
    state: str
    market: str
    crop: str
    min_price: float
    max_price: float
    modal_price: float


@dataclass(frozen=True)
class MarketPriceSnapshot:
    """Latest price and seven-day history for a market/crop pair."""

    market: str
    latest: PriceRecord
    history: tuple[PriceRecord, ...]


@dataclass(frozen=True)
class PriceForecast:
    """A lightweight, local statistical estimate from recent modal prices."""

    market: str
    projected_prices: tuple[float, ...]
    slope_per_day: float
    projected_change_percent: float


@dataclass(frozen=True)
class CropPriceSummary:
    """Price-data module output for one crop at a chosen farm location."""

    crop: str
    state: str
    as_of_date: date
    market_snapshots: tuple[MarketPriceSnapshot, ...]
    today_min_price: float
    today_max_price: float
    price_unit: str
    distances_km: dict[str, float]


@dataclass(frozen=True)
class VisionResult:
    crop: str | None
    confidence: float
    grade: Grade | None
    requires_manual_crop_selection: bool
    reasoning: tuple[str, ...] = ()


@dataclass(frozen=True)
class MarketRecommendation:
    market: str
    state: str
    distance_km: float
    is_feasible: bool
    gross_value_inr: float
    transport_cost_inr: float
    net_value_inr: float
    projected_price_inr_per_quintal: float
    projected_net_value_inr: float
    projected_change_percent: float
    forecast_prices: tuple[float, ...]


@dataclass(frozen=True)
class DecisionResult:
    recommendation: Recommendation
    recommended_market: str
    suggested_asking_price_inr_per_quintal: float
    market_comparisons: tuple[MarketRecommendation, ...]
    reasoning: tuple[str, ...]
    explanation: tuple[str, ...] = ()
    feasible_distance_km: float = 0.0
    distance_warning: str | None = None


@dataclass(frozen=True)
class MessageDraft:
    language: str
    text: str


@dataclass(frozen=True)
class PipelineResult:
    vision: VisionResult
    prices: CropPriceSummary
    decision: DecisionResult
    message: MessageDraft
    trail: tuple[dict[str, object], ...] = field(default_factory=tuple)
