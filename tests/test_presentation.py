from datetime import date

from pipeline.models import MarketPriceSnapshot, MarketRecommendation, PriceRecord
from utils.presentation import feasible_snapshots_for_charts


def _snapshot(market: str) -> MarketPriceSnapshot:
    record = PriceRecord(date(2026, 7, 25), "Maharashtra", market, "tomato", 900, 1100, 1000)
    return MarketPriceSnapshot(market, record, (record,))


def _comparison(market: str) -> MarketRecommendation:
    return MarketRecommendation(
        market=market,
        state="Maharashtra",
        distance_km=5,
        is_feasible=True,
        gross_value_inr=1000,
        transport_cost_inr=50,
        net_value_inr=950,
        projected_price_inr_per_quintal=1020,
        projected_net_value_inr=970,
        projected_change_percent=2.0,
        forecast_prices=(1000, 1000),
    )


def test_chart_snapshots_skip_history_only_markets_filtered_from_decision():
    snapshots = (_snapshot("Nashik APMC"), _snapshot("Pune Market Yard"))
    comparisons = {"Pune Market Yard": _comparison("Pune Market Yard")}

    chart_snapshots = feasible_snapshots_for_charts(snapshots, comparisons)

    assert [snapshot.market for snapshot in chart_snapshots] == ["Pune Market Yard"]
    # The app's chart lookup is now safe because every rendered snapshot has a comparison.
    assert all(snapshot.market in comparisons for snapshot in chart_snapshots)
