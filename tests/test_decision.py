from datetime import date

import pytest

from modules.decision import make_decision
from pipeline.models import CropPriceSummary, FarmLocation, MarketPriceSnapshot, PriceRecord


def _summary(modal_prices: tuple[float, float]) -> CropPriceSummary:
    history = tuple(
        PriceRecord(date(2026, 7, 19 + index), "Maharashtra", "Nashik APMC", "tomato", price - 100, price + 100, price)
        for index, price in enumerate(modal_prices)
    )
    snapshot = MarketPriceSnapshot("Nashik APMC", history[-1], history)
    return CropPriceSummary("tomato", "Maharashtra", history[-1].record_date, (snapshot,), history[-1].min_price, history[-1].max_price, "INR/quintal", {"Nashik APMC": 5})


def test_sell_now_when_trend_is_below_conservative_threshold():
    decision = make_decision(_summary((1000, 1050)), quantity_kg=100, grade="B")
    assert decision.recommendation == "sell_now"
    assert decision.recommended_market == "Nashik APMC"
    assert decision.market_comparisons[0].state == "Maharashtra"
    assert decision.market_comparisons[0].projected_price_inr_per_quintal > 1050
    assert decision.market_comparisons[0].net_value_inr == 1010


def test_wait_when_gain_clears_trend_and_risk_thresholds():
    decision = make_decision(_summary((1000, 1200)), quantity_kg=1000, grade="A")
    assert decision.recommendation == "wait"
    assert decision.suggested_asking_price_inr_per_quintal == 1260
    assert decision.market_comparisons[0].projected_net_value_inr > decision.market_comparisons[0].net_value_inr
    explanation = "\n".join(decision.explanation)
    assert "Recommended **WAIT**" in explanation
    assert "₹1,600" in explanation
    assert "₹150 risk buffer" in explanation
    assert "+8.0% wait threshold" in explanation


def test_sell_explanation_identifies_the_failed_risk_buffer_condition():
    decision = make_decision(_summary((1000, 1050)), quantity_kg=100, grade="B")
    assert decision.recommendation == "sell_now"
    explanation = "\n".join(decision.explanation)
    assert "Recommended **SELL NOW**" in explanation
    assert "₹100 does not clear the ₹150 risk buffer" in explanation


def test_rejects_invalid_quantity():
    with pytest.raises(ValueError, match="greater than zero"):
        make_decision(_summary((1000, 1050)), quantity_kg=0, grade="B")


def test_karnataka_tomato_recommendation_stays_within_a_realistic_local_area():
    from config.settings import FARM_LOCATION_PATH, PRICE_DATA_PATH
    from modules.price_data import get_crop_price_summary, load_farm_locations, load_price_records

    prices = get_crop_price_summary(
        load_price_records(PRICE_DATA_PATH),
        "tomato",
        load_farm_locations(FARM_LOCATION_PATH)["bengaluru_demo_village"],
    )
    decision = make_decision(prices, quantity_kg=100, grade="B")
    assert decision.market_comparisons
    assert all(item.state != "Punjab" for item in decision.market_comparisons)
    assert all(item.distance_km <= 100 for item in decision.market_comparisons)


def test_paddy_can_recommend_a_profitable_cross_state_market_within_500km():
    from config.settings import FARM_LOCATION_PATH, PRICE_DATA_PATH
    from modules.price_data import get_crop_price_summary, load_farm_locations, load_price_records

    prices = get_crop_price_summary(
        load_price_records(PRICE_DATA_PATH),
        "paddy",
        load_farm_locations(FARM_LOCATION_PATH)["ludhiana_demo_village"],
    )
    decision = make_decision(prices, quantity_kg=5000, grade="B")
    assert decision.recommended_market == "Lucknow APMC"
    assert any(item.state == "Uttar Pradesh" for item in decision.market_comparisons)
    assert any(item.distance_km <= 500 and item.state == "Uttar Pradesh" for item in decision.market_comparisons)


def test_no_feasible_market_returns_only_nearest_option_with_warning():
    source = _summary((1000, 1050))
    out_of_range = CropPriceSummary(
        source.crop, source.state, source.as_of_date, source.market_snapshots,
        source.today_min_price, source.today_max_price, source.price_unit, {"Nashik APMC": 150},
    )
    decision = make_decision(out_of_range, quantity_kg=100, grade="B")
    assert len(decision.market_comparisons) == 1
    assert not decision.market_comparisons[0].is_feasible
    assert decision.distance_warning is not None
    assert "No markets within the 100 km feasible distance for tomato" in decision.distance_warning
