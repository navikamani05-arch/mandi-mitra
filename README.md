# Mandi Mitra

Mandi Mitra is a Streamlit hackathon demo that helps small farmers compare mandi prices before selling produce. It supports tomato, onion, potato, and paddy across 12 markets in Maharashtra, Tamil Nadu, Karnataka, Punjab, and Uttar Pradesh.

> **Important:** price recommendations are estimates only; verify live mandi prices, transport cost, and crop quality before selling. Tamil Nadu prices are illustrative demo data. The A/B/C grade is a demo heuristic, not a certified quality standard.

## Architecture

The application is an agentic pipeline because a dedicated orchestrator preserves context and chains independent specialist modules. Each module has one responsibility and creates a separately logged reasoning step:

1. `modules/vision.py` perceives the uploaded photo, using a pretrained classifier and a demo grading heuristic.
2. `modules/price_data.py` retrieves and validates relevant seven-day local price history.
3. `modules/forecasting.py` uses a local recency-weighted regression to estimate the next two days from seven historical/demo observations.
4. `modules/decision.py` filters markets by crop-specific feasible travel distance, then calculates net proceeds and makes a conservative sell-now/wait decision using that estimate.
5. `modules/messaging.py` acts by producing a deterministic Hindi or Tamil WhatsApp-style draft.

`pipeline/orchestrator.py` runs the chain and writes one JSON log event per module to `logs/pipeline_steps.jsonl`. The UI also displays a completed, four-stage visual workflow trace: Vision Agent, Price Data Agent, Decision Agent, then Message Agent.

## Vision model and offline demo safety

The vision module uses Hugging Face Transformers with `openai/clip-vit-base-patch32`, a pretrained CLIP zero-shot image classifier. It compares the uploaded image only against the four supported crop labels. This is a practical hackathon trade-off: no crop-specific training is required, though it is not an agricultural-grade classifier.

The app deliberately uses `local_files_only=True`; it never downloads model weights while serving a demo. Before demo day, run the cache script once on a connected machine, then launch the app with the populated Hugging Face cache available:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/cache_vision_model.py
streamlit run app.py
```

If CLIP confidence is below 60%, the pipeline stops and asks the presenter to choose the crop manually. This avoids pretending an uncertain image is correctly classified.

## Data and decision policy

`data/mandi_prices.csv` contains 7 days x 4 crops x 12 markets (336 rows), in INR per quintal. The markets are Nashik APMC, Pune Market Yard, Lasalgaon Mandi, Koyambedu Market (Chennai), Madurai Mandi, Coimbatore Market, KR Market (Bengaluru), Hubballi APMC, Ludhiana Grain Market, Jalandhar APMC, Lucknow APMC, and Kanpur Mandi. `data/farm_locations.json` contains representative demo locations only; every profile has a distance to every market so recommendations compare all reachable destinations across the expanded states.

### Price-data provenance

Maharashtra, Karnataka, Punjab, and Uttar Pradesh market prices are sourced from real historical mandi data from Kaggle, based on Agmarknet. Tamil Nadu prices remain illustrative demo data. We attempted to source Tamil Nadu records directly from [agmarknet.gov.in](https://agmarknet.gov.in) using the available 24–30 Jul 2026 reports, but they did not contain sufficient matching records for Koyambedu, Madurai, and Coimbatore across all four crops and seven days. Rather than import incomplete or misleading data, the Tamil Nadu rows remain clearly labeled synthetic in both the repository and app.

The location selector is state-first and intentionally uses demo coverage, not full nationwide precision. It keeps the offline demo honest while still exercising cross-state filtering.

Before comparison, the decision module limits options to realistic one-way travel distances: tomato 100 km, onion 200 km, potato 250 km, and paddy 500 km. These values are configurable in `config/settings.py`. If no market is feasible, the app shows only the nearest market with an explicit distance warning. The offline map uses local coordinates to display only feasible market routes.

For each market, the decision module calculates:

`net proceeds = modal price x grade adjustment x quantity in quintals - distance x Rs8/km`

It recommends **wait** only if the best-net market's two-day lightweight projection rises at least 8% and the projected net gain clears a Rs150 holding/risk buffer. The projection is an estimate based on recent mock history, not a guarantee. All values are configurable in `config/settings.py`.

## Tests

Run the complete unit suite with:

```powershell
python -m pytest -q
```

The test suite covers CSV/location validation, current price ranges, seven-day history, transport/trend decisions, Hindi/Tamil templates, and orchestration with a stubbed vision module. The real CLIP model is intentionally not downloaded by unit tests.
