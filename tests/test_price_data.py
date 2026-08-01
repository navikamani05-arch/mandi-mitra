from datetime import date
from pathlib import Path

import pytest

from config.settings import FARM_LOCATION_PATH, PRICE_DATA_PATH
from modules.price_data import PriceDataError, get_crop_price_summary, load_farm_locations, load_price_records


def test_loads_complete_seven_day_data_for_all_crops_and_markets():
    records = load_price_records(PRICE_DATA_PATH)
    assert len(records) == 336
    assert {record.crop for record in records} == {"tomato", "onion", "potato", "paddy"}
    assert {record.state for record in records} == {
        "Maharashtra",
        "Tamil Nadu",
        "Karnataka",
        "Punjab",
        "Uttar Pradesh",
    }


def test_returns_current_price_range_and_history_for_tomato():
    records = load_price_records(PRICE_DATA_PATH)
    farm = load_farm_locations(FARM_LOCATION_PATH)["nashik_demo_village"]

    summary = get_crop_price_summary(records, "Tomato", farm)

    assert summary.as_of_date == date(2026, 7, 25)
    assert summary.today_min_price < summary.today_max_price
    # The 12-market mock fixture can include a lower regional tomato price;
    # this guards against implausibly low data without pinning an old value.
    assert summary.today_min_price > 1000
    assert [snapshot.market for snapshot in summary.market_snapshots] == [
        "Nashik APMC",
        "Pune Market Yard",
        "Lasalgaon Mandi",
        "Koyambedu Market, Chennai",
        "Madurai Mandi",
        "Coimbatore Market",
        "KR Market, Bengaluru",
        "Hubballi APMC",
        "Ludhiana Grain Market",
        "Jalandhar APMC",
        "Lucknow APMC",
        "Kanpur Mandi",
    ]
    assert all(len(snapshot.history) == 7 for snapshot in summary.market_snapshots)


def test_tamil_nadu_location_compares_all_twelve_markets():
    records = load_price_records(PRICE_DATA_PATH)
    farm = load_farm_locations(FARM_LOCATION_PATH)["coimbatore_demo_village"]
    summary = get_crop_price_summary(records, "onion", farm)
    assert len(summary.market_snapshots) == 12
    assert {snapshot.latest.state for snapshot in summary.market_snapshots} == {
        "Maharashtra",
        "Tamil Nadu",
        "Karnataka",
        "Punjab",
        "Uttar Pradesh",
    }
    assert summary.distances_km["Coimbatore Market"] == 15


def test_paddy_mock_histories_have_distinct_non_flat_market_variation():
    records = load_price_records(PRICE_DATA_PATH)
    farm = load_farm_locations(FARM_LOCATION_PATH)["nashik_demo_village"]
    summary = get_crop_price_summary(records, "paddy", farm)
    series = [tuple(record.modal_price for record in snapshot.history) for snapshot in summary.market_snapshots]
    assert len(set(series)) == 12
    assert all(max(values) > min(values) for values in series)
    assert any(values[-1] < values[0] for values in series)
    assert any(values[-1] > values[0] for values in series)


def test_rejects_unknown_crop():
    records = load_price_records(PRICE_DATA_PATH)
    farm = load_farm_locations(FARM_LOCATION_PATH)["nashik_demo_village"]
    with pytest.raises(PriceDataError, match="Unsupported crop"):
        get_crop_price_summary(records, "banana", farm)


def test_rejects_malformed_csv(tmp_path: Path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("date,state\n2026-07-25,Maharashtra\n", encoding="utf-8")
    with pytest.raises(PriceDataError, match="missing required columns"):
        load_price_records(bad_csv)


def test_loads_legacy_csv_with_a_utf8_bom_in_the_date_header(tmp_path: Path):
    legacy_csv = tmp_path / "legacy_bom.csv"
    legacy_csv.write_text(
        "\ufeffdate,state,market,crop,min_price,max_price,modal_price\n"
        "2026-07-25,Maharashtra,Nashik APMC,tomato,1200,1600,1400\n",
        encoding="utf-8",
    )

    records = load_price_records(legacy_csv)

    assert len(records) == 1
    assert records[0].record_date == date(2026, 7, 25)


def test_loads_legacy_farm_locations_json_with_a_utf8_bom(tmp_path: Path):
    legacy_locations = tmp_path / "legacy_locations.json"
    legacy_locations.write_text(
        "\ufeff[\n"
        "  {\n"
        "    \"id\": \"demo\",\n"
        "    \"display_name\": \"Demo village\",\n"
        "    \"state\": \"Maharashtra\",\n"
        "    \"latitude\": 19.9,\n"
        "    \"longitude\": 73.8,\n"
        "    \"distances_km\": {\"Nashik APMC\": 5}\n"
        "  }\n"
        "]\n",
        encoding="utf-8",
    )

    locations = load_farm_locations(legacy_locations)

    assert locations["demo"].distances_km == {"Nashik APMC": 5.0}
