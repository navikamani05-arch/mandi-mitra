"""Central, editable defaults for the Mandi Mitra demo."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PRICE_DATA_PATH = DATA_DIR / "mandi_prices.csv"
FARM_LOCATION_PATH = DATA_DIR / "farm_locations.json"

SUPPORTED_CROPS = ("tomato", "onion", "potato", "paddy")
SUPPORTED_LANGUAGES = ("Hindi", "Tamil")
PRICE_UNIT = "INR/quintal"
DEMO_STATES = ("Maharashtra", "Tamil Nadu", "Karnataka", "Punjab", "Uttar Pradesh")

# Decision defaults. They will be consumed by the decision module.
TRANSPORT_RATE_PER_KM = 8.0
WAIT_TREND_THRESHOLD_PERCENT = 8.0
WAIT_RISK_BUFFER_INR = 150.0

# Maximum practical one-way road distance by crop, used before ranking markets.
MAX_FEASIBLE_DISTANCE_KM_BY_CROP = {
    "tomato": 100.0,
    "onion": 200.0,
    "potato": 250.0,
    "paddy": 500.0,
}

# Approximate coordinates used only for the static, offline feasibility map.
MARKET_COORDINATES = {
    "Nashik APMC": (20.0059, 73.7890),
    "Pune Market Yard": (18.5204, 73.8567),
    "Lasalgaon Mandi": (20.1420, 74.2360),
    "Koyambedu Market, Chennai": (13.0690, 80.1940),
    "Madurai Mandi": (9.9190, 78.1240),
    "Coimbatore Market": (11.0168, 76.9558),
    "KR Market, Bengaluru": (12.9716, 77.5761),
    "Hubballi APMC": (15.3647, 75.1240),
    "Ludhiana Grain Market": (30.9010, 75.8573),
    "Jalandhar APMC": (31.3260, 75.5762),
    "Lucknow APMC": (26.8467, 80.9462),
    "Kanpur Mandi": (26.4499, 80.3319),
}

# Vision defaults. The model must be cached before a network-free demo.
CLIP_MODEL_ID = "openai/clip-vit-base-patch32"
VISION_CONFIDENCE_THRESHOLD = 0.60
