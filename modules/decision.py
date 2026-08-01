"""Transparent sell-now versus wait recommendations."""

from __future__ import annotations

from config.settings import (
    MAX_FEASIBLE_DISTANCE_KM_BY_CROP,
    TRANSPORT_RATE_PER_KM,
    WAIT_RISK_BUFFER_INR,
    WAIT_TREND_THRESHOLD_PERCENT,
)
from modules.forecasting import forecast_prices
from pipeline.models import CropPriceSummary, DecisionResult, Grade, MarketRecommendation

GRADE_PRICE_MULTIPLIERS: dict[Grade, float] = {"A": 1.05, "B": 1.00, "C": 0.90}


def make_decision(
    prices: CropPriceSummary,
    quantity_kg: float,
    grade: Grade,
    transport_rate_per_km: float = TRANSPORT_RATE_PER_KM,
    wait_trend_threshold_percent: float = WAIT_TREND_THRESHOLD_PERCENT,
    wait_risk_buffer_inr: float = WAIT_RISK_BUFFER_INR,
    feasible_distance_by_crop: dict[str, float] = MAX_FEASIBLE_DISTANCE_KM_BY_CROP,
) -> DecisionResult:
    """Rank only realistically reachable markets, then apply the wait rule."""
    if quantity_kg <= 0:
        raise ValueError("Quantity must be greater than zero.")
    if transport_rate_per_km < 0:
        raise ValueError("Transport rate cannot be negative.")
    if prices.crop not in feasible_distance_by_crop:
        raise ValueError(f"No feasible-distance policy configured for crop: {prices.crop}.")
    feasible_distance_km = feasible_distance_by_crop[prices.crop]
    quantity_quintals = quantity_kg / 100.0
    all_comparisons: list[MarketRecommendation] = []
    for snapshot in prices.market_snapshots:
        base_price = snapshot.latest.modal_price
        gross = base_price * GRADE_PRICE_MULTIPLIERS[grade] * quantity_quintals
        transport = prices.distances_km[snapshot.market] * transport_rate_per_km
        forecast = forecast_prices(snapshot.history, horizon_days=2)
        projected_price = forecast.projected_prices[-1]
        projected_gross = projected_price * GRADE_PRICE_MULTIPLIERS[grade] * quantity_quintals
        projected_net = projected_gross - transport
        distance_km = prices.distances_km[snapshot.market]
        all_comparisons.append(MarketRecommendation(
            snapshot.market,
            snapshot.latest.state,
            distance_km,
            distance_km <= feasible_distance_km,
            gross,
            transport,
            gross - transport,
            projected_price,
            projected_net,
            forecast.projected_change_percent,
            forecast.projected_prices,
        ))

    comparisons = [comparison for comparison in all_comparisons if comparison.is_feasible]
    distance_warning: str | None = None
    if not comparisons:
        nearest = min(all_comparisons, key=lambda item: item.distance_km)
        comparisons = [nearest]
        distance_warning = (
            f"No markets within the {feasible_distance_km:.0f} km feasible distance for {prices.crop}; "
            f"showing nearest option ({nearest.market}, {nearest.distance_km:.0f} km) with a distance warning."
        )

    best = max(comparisons, key=lambda item: item.net_value_inr)
    projected_gain = best.projected_net_value_inr - best.net_value_inr
    should_wait = (
        best.projected_change_percent >= wait_trend_threshold_percent
        and projected_gain > wait_risk_buffer_inr
    )
    recommendation = "wait" if should_wait else "sell_now"
    latest = next(snapshot.latest for snapshot in prices.market_snapshots if snapshot.market == best.market)
    asking_price = latest.modal_price * GRADE_PRICE_MULTIPLIERS[grade]
    trail = [
        f"Quantity: {quantity_kg:.1f} kg = {quantity_quintals:.2f} quintals.",
        f"Feasible distance for {prices.crop}: up to {feasible_distance_km:.0f} km; {len(comparisons)} market(s) considered.",
        f"Best current net proceeds: ₹{best.net_value_inr:,.0f} at {best.market} after ₹{best.transport_cost_inr:,.0f} transport.",
        f"Projected two-day trend at {best.market}: {best.projected_change_percent:+.1f}% (wait threshold: +{wait_trend_threshold_percent:.1f}%).",
    ]
    if should_wait:
        trail.append(f"Wait: projected net gain of ₹{projected_gain:,.0f} clears the ₹{wait_risk_buffer_inr:,.0f} risk buffer.")
    else:
        trail.append("Sell now: the lightweight projection does not clear the conservative wait case.")
    if distance_warning:
        trail.append(distance_warning)

    explanation = _build_explanation(
        recommendation=recommendation,
        market=best.market,
        current_price=latest.modal_price,
        projected_price=best.projected_price_inr_per_quintal,
        projected_gain=projected_gain,
        projected_change_percent=best.projected_change_percent,
        risk_buffer_inr=wait_risk_buffer_inr,
        trend_threshold_percent=wait_trend_threshold_percent,
        distance_km=best.distance_km,
        feasible_distance_km=feasible_distance_km,
        distance_warning=distance_warning,
    )
    return DecisionResult(
        recommendation,
        best.market,
        asking_price,
        tuple(comparisons),
        tuple(trail),
        explanation,
        feasible_distance_km,
        distance_warning,
    )


def _build_explanation(
    *,
    recommendation: str,
    market: str,
    current_price: float,
    projected_price: float,
    projected_gain: float,
    projected_change_percent: float,
    risk_buffer_inr: float,
    trend_threshold_percent: float,
    distance_km: float,
    feasible_distance_km: float,
    distance_warning: str | None,
) -> tuple[str, ...]:
    """Turn the exact decision inputs into a concise, judge-readable rationale."""
    price_line = (
        f"- Projected 2-day price at **{market}**: ₹{projected_price:,.0f} "
        f"(from ₹{current_price:,.0f} today)."
    )
    gain_line = f"- Projected net gain: ₹{projected_gain:,.0f}; risk buffer: ₹{risk_buffer_inr:,.0f}."
    trend_line = (
        f"- Trend strength: {projected_change_percent:+.1f}% projected; "
        f"wait threshold: +{trend_threshold_percent:.1f}%."
    )
    distance_line = f"- Market distance: {distance_km:.0f} km (crop feasibility limit: {feasible_distance_km:.0f} km)."
    if recommendation == "wait":
        return (
            "Recommended **WAIT** because:",
            price_line,
            f"- Projected net gain of ₹{projected_gain:,.0f} exceeds the ₹{risk_buffer_inr:,.0f} risk buffer.",
            f"- Trend strength of {projected_change_percent:+.1f}% is above the +{trend_threshold_percent:.1f}% wait threshold.",
            distance_line,
            "- If either condition were not met, the recommendation would be **SELL NOW** instead.",
        )

    failed_conditions: list[str] = []
    if projected_gain <= risk_buffer_inr:
        failed_conditions.append(
            f"- Projected net gain of ₹{projected_gain:,.0f} does not clear the ₹{risk_buffer_inr:,.0f} risk buffer."
        )
    if projected_change_percent < trend_threshold_percent:
        failed_conditions.append(
            f"- Trend strength of {projected_change_percent:+.1f}% is below the +{trend_threshold_percent:.1f}% wait threshold."
        )
    explanation = (
        "Recommended **SELL NOW** because:",
        price_line,
        gain_line,
        trend_line,
        distance_line,
        *failed_conditions,
        "- Waiting requires both a strong projected trend and a gain that clears the risk buffer.",
    )
    if distance_warning:
        return explanation + (f"- ⚠️ {distance_warning}",)
    return explanation
