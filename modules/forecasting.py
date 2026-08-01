"""Small, fully offline price forecasts based only on the supplied history."""

from __future__ import annotations

import numpy as np

from pipeline.models import PriceForecast, PriceRecord


class ForecastError(ValueError):
    """Raised when price history cannot support a meaningful projection."""


def forecast_prices(history: tuple[PriceRecord, ...], horizon_days: int = 2) -> PriceForecast:
    """Project modal prices for the next few days from a market's full history.

    Recency-weighted linear regression is deliberately used instead of a
    first-versus-last comparison: all seven observations inform the slope,
    while weights make it less stale when the mock series changes direction.
    """
    if len(history) < 2:
        raise ForecastError("At least two days of price history are required for a forecast.")
    if horizon_days not in (2, 3):
        raise ForecastError("Forecast horizon must be 2 or 3 days.")
    ordered = tuple(sorted(history, key=lambda record: record.record_date))
    if len({record.market for record in ordered}) != 1:
        raise ForecastError("Forecast history must contain exactly one market.")
    if len({record.crop for record in ordered}) != 1:
        raise ForecastError("Forecast history must contain exactly one crop.")

    prices = np.asarray([record.modal_price for record in ordered], dtype=float)
    days = np.arange(len(prices), dtype=float)
    weights = np.arange(1, len(prices) + 1, dtype=float)
    slope, intercept = np.polyfit(days, prices, deg=1, w=weights)
    future_days = np.arange(len(prices), len(prices) + horizon_days, dtype=float)
    projected = tuple(float(max(0.0, value)) for value in slope * future_days + intercept)
    projected_change = ((projected[-1] - prices[-1]) / prices[-1]) * 100 if prices[-1] else 0.0
    return PriceForecast(
        market=ordered[-1].market,
        projected_prices=projected,
        slope_per_day=float(slope),
        projected_change_percent=float(projected_change),
    )
