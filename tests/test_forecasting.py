from datetime import date, timedelta

import pytest

from modules.forecasting import ForecastError, forecast_prices
from pipeline.models import PriceRecord


def _history(prices: list[float], market: str = "Nashik APMC") -> tuple[PriceRecord, ...]:
    start = date(2026, 7, 19)
    return tuple(
        PriceRecord(start + timedelta(days=index), "Maharashtra", market, "tomato", price - 100, price + 100, price)
        for index, price in enumerate(prices)
    )


def test_forecast_rising_history_projects_higher_prices():
    result = forecast_prices(_history([1000, 1020, 1040, 1060, 1080, 1100, 1120]))
    assert len(result.projected_prices) == 2
    assert result.projected_prices[0] > 1120
    assert result.projected_change_percent > 0


def test_forecast_falling_history_projects_lower_prices():
    result = forecast_prices(_history([1120, 1100, 1080, 1060, 1040, 1020, 1000]))
    assert result.projected_prices[-1] < 1000
    assert result.projected_change_percent < 0


def test_forecast_flat_history_stays_close_to_current_price():
    result = forecast_prices(_history([1500] * 7), horizon_days=3)
    assert result.projected_prices == pytest.approx((1500, 1500, 1500))
    assert result.slope_per_day == pytest.approx(0)


def test_forecast_handles_low_variance_history_without_overreacting():
    result = forecast_prices(_history([1500, 1502, 1499, 1501, 1500, 1502, 1501]))
    assert abs(result.projected_change_percent) < 1


def test_forecast_rejects_insufficient_or_mixed_history():
    with pytest.raises(ForecastError, match="At least two"):
        forecast_prices(_history([1000]))
    with pytest.raises(ForecastError, match="exactly one market"):
        forecast_prices(_history([1000, 1010], market="Nashik APMC") + _history([1020], market="Pune Market Yard"))
