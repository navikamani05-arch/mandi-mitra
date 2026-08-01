"""Load, validate, and query mock mandi-price history."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from config.settings import PRICE_UNIT, SUPPORTED_CROPS
from pipeline.models import CropPriceSummary, FarmLocation, MarketPriceSnapshot, PriceRecord

REQUIRED_PRICE_COLUMNS = {
    "date", "state", "market", "crop", "min_price", "max_price", "modal_price"
}


class PriceDataError(ValueError):
    """Raised when mock price data is invalid or cannot satisfy a query."""


def load_farm_locations(path: Path) -> dict[str, FarmLocation]:
    """Load location profiles keyed by their stable identifier."""
    # utf-8-sig accepts clean UTF-8 and safely strips a legacy UTF-8 BOM.
    with path.open(encoding="utf-8-sig") as file:
        payload = json.load(file)
    locations: dict[str, FarmLocation] = {}
    for row in payload:
        location = FarmLocation(
            id=row["id"],
            display_name=row["display_name"],
            state=row["state"],
            distances_km={market: float(distance) for market, distance in row["distances_km"].items()},
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
        )
        locations[location.id] = location
    if not locations:
        raise PriceDataError("No farm locations were supplied.")
    return locations


def load_price_records(path: Path) -> tuple[PriceRecord, ...]:
    """Read and validate the mock CSV without relying on a dataframe runtime."""
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        # Be tolerant of legacy UTF-8-with-BOM CSVs.  New generated fixtures
        # are BOM-free, but normalising here keeps this loader usable with
        # externally supplied or older mock datasets too.
        reader.fieldnames = [
            name.lstrip("\ufeff") if name else name
            for name in (reader.fieldnames or [])
        ]
        columns = set(reader.fieldnames)
        missing = REQUIRED_PRICE_COLUMNS - columns
        if missing:
            raise PriceDataError(f"Price CSV is missing required columns: {sorted(missing)}")

        records: list[PriceRecord] = []
        seen: set[tuple[date, str, str]] = set()
        for row_number, row in enumerate(reader, start=2):
            try:
                record = PriceRecord(
                    record_date=date.fromisoformat(row["date"]),
                    state=row["state"].strip(),
                    market=row["market"].strip(),
                    crop=row["crop"].strip().lower(),
                    min_price=float(row["min_price"]),
                    max_price=float(row["max_price"]),
                    modal_price=float(row["modal_price"]),
                )
            except (KeyError, TypeError, ValueError) as error:
                raise PriceDataError(f"Invalid price row {row_number}: {error}") from error
            if not record.market or not record.state or not record.crop:
                raise PriceDataError(f"Price row {row_number} has a blank state, market, or crop.")
            if record.min_price < 0 or record.modal_price < 0 or record.max_price < 0:
                raise PriceDataError(f"Price row {row_number} has a negative price.")
            if not record.min_price <= record.modal_price <= record.max_price:
                raise PriceDataError(f"Price row {row_number} must satisfy min <= modal <= max.")
            key = (record.record_date, record.market, record.crop)
            if key in seen:
                raise PriceDataError(f"Duplicate price row for {key}.")
            seen.add(key)
            records.append(record)
    if not records:
        raise PriceDataError("Price CSV has no records.")
    return tuple(records)


def get_crop_price_summary(
    records: tuple[PriceRecord, ...], crop: str, farm_location: FarmLocation, days: int = 7
) -> CropPriceSummary:
    """Return latest prices and contiguous recent history for a crop/location."""
    normalized_crop = crop.strip().lower()
    if normalized_crop not in SUPPORTED_CROPS:
        raise PriceDataError(f"Unsupported crop: {crop!r}.")
    if days < 2:
        raise PriceDataError("At least two days of price history are required.")

    matching = [
        record for record in records
        if record.crop == normalized_crop and record.market in farm_location.distances_km
    ]
    if not matching:
        raise PriceDataError(f"No prices found for {normalized_crop} in the selected market set.")

    as_of_date = max(record.record_date for record in matching)
    by_market: dict[str, list[PriceRecord]] = defaultdict(list)
    for record in matching:
        by_market[record.market].append(record)

    snapshots: list[MarketPriceSnapshot] = []
    for market in farm_location.distances_km:
        market_records = sorted(by_market.get(market, []), key=lambda record: record.record_date)
        recent_records = [record for record in market_records if record.record_date <= as_of_date][-days:]
        if len(recent_records) != days:
            raise PriceDataError(f"{market} has fewer than {days} days of {normalized_crop} data.")
        if recent_records[-1].record_date != as_of_date:
            raise PriceDataError(f"{market} has no latest price for {as_of_date.isoformat()}.")
        snapshots.append(MarketPriceSnapshot(
            market=market, latest=recent_records[-1], history=tuple(recent_records)
        ))

    latest_records = [snapshot.latest for snapshot in snapshots]
    return CropPriceSummary(
        crop=normalized_crop,
        state=farm_location.state,
        as_of_date=as_of_date,
        market_snapshots=tuple(snapshots),
        today_min_price=min(record.min_price for record in latest_records),
        today_max_price=max(record.max_price for record in latest_records),
        price_unit=PRICE_UNIT,
        distances_km=dict(farm_location.distances_km),
    )
