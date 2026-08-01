"""Pure helpers for keeping result visualizations aligned with decision outputs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from pipeline.models import MarketPriceSnapshot, MarketRecommendation


def feasible_snapshots_for_charts(
    snapshots: Iterable[MarketPriceSnapshot],
    comparisons_by_market: Mapping[str, MarketRecommendation],
) -> tuple[MarketPriceSnapshot, ...]:
    """Return only snapshots whose markets survived Decision filtering."""
    return tuple(snapshot for snapshot in snapshots if snapshot.market in comparisons_by_market)
