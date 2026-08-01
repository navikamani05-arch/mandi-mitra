"""Streamlit interface for the Mandi Mitra demo."""

from __future__ import annotations

import html
from datetime import timedelta

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st
from PIL import Image, UnidentifiedImageError

from config.settings import DEMO_STATES, FARM_LOCATION_PATH, MARKET_COORDINATES, SUPPORTED_CROPS, SUPPORTED_LANGUAGES
from modules.price_data import load_farm_locations
from pipeline.models import FarmLocation, MarketPriceSnapshot, MarketRecommendation
from pipeline.orchestrator import MandiMitraPipeline
from utils.presentation import feasible_snapshots_for_charts

st.set_page_config(page_title="Mandi Mitra", page_icon="🌾", layout="wide")
st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at 12% 15%, rgba(255, 255, 255, 0.52) 0%, rgba(255, 255, 255, 0.06) 19%, transparent 35%),
        radial-gradient(circle at 82% 10%, rgba(181, 208, 139, 0.18) 0%, transparent 30%),
        linear-gradient(120deg, #EAF3DE 0%, #F4F0DD 48%, #FAEEDA 100%);
    background-size: 220% 220%;
    animation: mandiGradient 14s ease-in-out infinite;
    will-change: background-position;
}
.stApp::before {
    content: "";
    position: fixed;
    top: 10vh;
    left: -18vw;
    width: 18rem;
    height: 5rem;
    background:
        radial-gradient(circle at 28% 62%, rgba(255, 255, 255, 0.55) 0 24%, transparent 25%),
        radial-gradient(circle at 50% 42%, rgba(255, 255, 255, 0.48) 0 30%, transparent 31%),
        radial-gradient(circle at 72% 62%, rgba(255, 255, 255, 0.55) 0 22%, transparent 23%);
    opacity: 0.42;
    filter: blur(1px);
    pointer-events: none;
    z-index: 0;
    animation: cloudDrift 13s ease-in-out infinite;
    will-change: transform;
}
.stApp::after {
    content: "";
    position: fixed;
    right: 1.25rem;
    bottom: 1.15rem;
    width: 5rem;
    height: 5rem;
    background:
        radial-gradient(circle at 45% 28%, rgba(63, 125, 77, 0.42) 0 10%, transparent 11%),
        linear-gradient(145deg, transparent 42%, rgba(63, 125, 77, 0.30) 43% 50%, transparent 51%),
        linear-gradient(35deg, transparent 42%, rgba(170, 128, 52, 0.22) 43% 50%, transparent 51%);
    border-radius: 58% 42% 56% 44%;
    opacity: 0.38;
    pointer-events: none;
    transform-origin: center bottom;
    z-index: 0;
    animation: leafSway 11s ease-in-out infinite;
    will-change: transform;
}
.agri-sun, .agri-sprout {
    pointer-events: none;
    position: fixed;
    z-index: 0;
}
.agri-sun {
    background:
        radial-gradient(circle, rgba(230, 177, 62, 0.48) 0 34%, transparent 35%),
        repeating-conic-gradient(from 0deg, rgba(207, 151, 43, 0.34) 0deg 8deg, transparent 8deg 30deg);
    border-radius: 50%;
    height: 5.4rem;
    opacity: 0.42;
    right: 2.2rem;
    top: 6.8rem;
    width: 5.4rem;
    animation: sunFloat 15s ease-in-out infinite;
    will-change: transform;
}
.agri-sprout {
    background:
        radial-gradient(ellipse at 32% 29%, rgba(62, 124, 75, 0.44) 0 20%, transparent 21%),
        radial-gradient(ellipse at 68% 29%, rgba(82, 145, 85, 0.40) 0 20%, transparent 21%),
        linear-gradient(90deg, transparent 47%, rgba(69, 120, 66, 0.42) 48% 53%, transparent 54%);
    bottom: 1.3rem;
    height: 5.2rem;
    left: 1.4rem;
    opacity: 0.40;
    transform-origin: bottom center;
    width: 4.3rem;
    animation: sproutSway 9s ease-in-out infinite;
    will-change: transform;
}
.block-container {
    position: relative;
    z-index: 1;
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid rgba(193, 210, 178, 0.34);
    border-radius: 24px;
    box-shadow: 0 10px 28px rgba(67, 91, 59, 0.06);
    padding-top: 1.2rem;
}
.stSidebar .block-container {
    background: rgba(255, 255, 255, 0.96);
}
div[data-testid="stDataFrame"], div[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.96);
    border-radius: 0.7rem;
}
.mandi-wordmark {
    align-items: center;
    background: linear-gradient(110deg, #e8f2df, #f7f3e7);
    border: 1px solid #d3e2cc;
    border-radius: 14px;
    display: flex;
    gap: 0.8rem;
    margin: 0.2rem 0 0.7rem;
    padding: 0.9rem 1.1rem;
}
.mandi-logo { font-size: 2.1rem; line-height: 1; }
.mandi-name { color: #285b35; font-size: 1.65rem; font-weight: 750; line-height: 1.1; }
.mandi-tagline { color: #5b6e5e; font-size: 0.9rem; margin-top: 0.15rem; }
.whatsapp-bubble {
    background: #dcf8c6;
    border-radius: 16px 16px 4px 16px;
    box-shadow: 0 1px 2px rgba(26, 56, 31, 0.18);
    color: #17351d;
    margin: 0.4rem 0;
    max-width: 92%;
    padding: 0.85rem 1rem;
}
.whatsapp-sender { color: #397a45; font-size: 0.78rem; font-weight: 700; margin-bottom: 0.28rem; }
.recommendation-badge { border-radius: 999px; display: inline-block; font-weight: 700; padding: 0.35rem 0.8rem; }
.sell-badge { background: #dcefdc; color: #1d6229; }
.wait-badge { background: #fff0c9; color: #895800; }

@keyframes mandiGradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes cloudDrift {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(7vw, -0.45rem); }
}
@keyframes leafSway {
    0%, 100% { transform: rotate(-8deg) translateY(0); }
    50% { transform: rotate(4deg) translateY(-4px); }
}
@keyframes sunFloat {
    0%, 100% { transform: translate(0, 0) rotate(0deg); }
    50% { transform: translate(-0.55rem, 0.45rem) rotate(8deg); }
}
@keyframes sproutSway {
    0%, 100% { transform: rotate(-3deg) translateY(0); }
    50% { transform: rotate(3deg) translateY(-0.35rem); }
}
@media (prefers-reduced-motion: reduce) {
    .stApp, .stApp::before, .stApp::after, .agri-sun, .agri-sprout { animation: none; }
}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="agri-sun" aria-hidden="true"></div><div class="agri-sprout" aria-hidden="true"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="mandi-wordmark">
  <div class="mandi-logo">🌾</div>
  <div><div class="mandi-name">Mandi Mitra</div><div class="mandi-tagline">Smarter, distance-aware produce selling</div></div>
</div>
""", unsafe_allow_html=True)
with st.expander("How this works"):
    st.write(
        "Mandi Mitra chains four specialist agents: Vision identifies the crop and a demo grade, "
        "Price Data retrieves local mandi history, Decision compares only feasible markets and estimates a short trend, "
        "and Message drafts an offline Hindi or Tamil sales message. Every recommendation is an estimate."
    )
st.warning("Price recommendations are estimates. Verify current mandi prices and actual transport costs before selling. Tamil Nadu market prices are illustrative demo data.")

locations = load_farm_locations(FARM_LOCATION_PATH)
locations_by_state: dict[str, tuple[FarmLocation, ...]] = {
    state: tuple(sorted((location for location in locations.values() if location.state == state), key=lambda item: item.display_name))
    for state in DEMO_STATES
    if any(location.state == state for location in locations.values())
}
state_options = [state for state in DEMO_STATES if state in locations_by_state]


@st.cache_resource
def get_pipeline() -> MandiMitraPipeline:
    """Keep the locally cached model loaded across Streamlit reruns."""
    return MandiMitraPipeline()


def forecast_chart(snapshot: MarketPriceSnapshot, comparison: MarketRecommendation) -> alt.Chart:
    """Render actual mock history and the local two-day projection distinctly."""
    historical = pd.DataFrame([
        {"Date": record.record_date, "Price (₹/quintal)": record.modal_price}
        for record in snapshot.history
    ])
    latest = snapshot.history[-1]
    projected = pd.DataFrame(
        [{"Date": latest.record_date, "Price (₹/quintal)": latest.modal_price}]
        + [
            {"Date": latest.record_date + timedelta(days=index + 1), "Price (₹/quintal)": price}
            for index, price in enumerate(comparison.forecast_prices)
        ]
    )
    encoding = {
        "x": alt.X("Date:T", title=None),
        "y": alt.Y("Price (₹/quintal):Q", title=None),
        "tooltip": [alt.Tooltip("Date:T", format="%d %b"), alt.Tooltip("Price (₹/quintal):Q", format=".0f")],
    }
    actual = alt.Chart(historical).mark_line(color="#3F7D4D", point=True).encode(**encoding)
    estimate = alt.Chart(projected).mark_line(color="#A66B2E", strokeDash=[6, 4], point=True).encode(**encoding)
    return alt.layer(actual, estimate).properties(height=190)


def feasible_market_map(farm: FarmLocation, comparisons: tuple[MarketRecommendation, ...]) -> pdk.Deck | None:
    """Build a no-tile, offline spatial view from only feasible markets."""
    feasible = [item for item in comparisons if item.is_feasible and item.market in MARKET_COORDINATES]
    if not feasible:
        return None
    markets = []
    routes = []
    labels = []
    for item in feasible:
        latitude, longitude = MARKET_COORDINATES[item.market]
        markets.append({
            "name": item.market,
            "state": item.state,
            "distance": f"{item.distance_km:.0f} km",
            "position": [longitude, latitude],
        })
        routes.append({"source": [farm.longitude, farm.latitude], "target": [longitude, latitude]})
        labels.append({
            "position": [(farm.longitude + longitude) / 2, (farm.latitude + latitude) / 2],
            "text": f"{item.distance_km:.0f} km",
        })
    layers = [
        pdk.Layer("ScatterplotLayer", [{"position": [farm.longitude, farm.latitude]}], get_position="position", get_fill_color=[56, 122, 73], get_radius=14000),
        pdk.Layer("ScatterplotLayer", markets, get_position="position", get_fill_color=[190, 122, 48], get_radius=11500),
        pdk.Layer("LineLayer", routes, get_source_position="source", get_target_position="target", get_color=[63, 125, 77], get_width=3),
        pdk.Layer("TextLayer", labels, get_position="position", get_text="text", get_color=[65, 83, 62], get_size=15, get_alignment_baseline="bottom"),
    ]
    return pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(latitude=farm.latitude, longitude=farm.longitude, zoom=5.2, pitch=0),
        layers=layers,
        tooltip={"html": "<b>{name}</b><br/>{state}<br/>{distance}"},
    )


with st.sidebar:
    st.header("Farmer inputs")
    upload = st.file_uploader("Produce photo", type=["jpg", "jpeg", "png"])
    quantity_kg = st.number_input("Quantity (kg)", min_value=1.0, value=100.0, step=1.0)
    language = st.selectbox("Message language", SUPPORTED_LANGUAGES)
    selected_state = st.selectbox("Demo state", state_options)
    state_locations = locations_by_state[selected_state]
    location_id = st.selectbox(
        "Demo village/district",
        [location.id for location in state_locations],
        format_func=lambda item: locations[item].display_name,
        key=f"location_{selected_state}",
    )
    st.caption("Representative demo locations only; not full nationwide geocoding.")
    manual_crop = st.selectbox("Crop override (use only if asked)", ["Auto-detect", *SUPPORTED_CROPS])
    run = st.button("Analyse produce", type="primary", use_container_width=True)

if run:
    if upload is None:
        st.error("Upload a produce photo to begin.")
    else:
        progress = st.status("Mandi Mitra agents are working…", expanded=True)
        try:
            image = Image.open(upload)

            def show_completed_step(agent: str, summary: str) -> None:
                progress.write(f"✅ **{agent}:** {summary}")

            with st.spinner("Running Vision, Price Data, Decision, and Message agents..."):
                result = get_pipeline().run(
                    image=image,
                    quantity_kg=quantity_kg,
                    language=language,
                    location_id=location_id,
                    manual_crop=None if manual_crop == "Auto-detect" else manual_crop,
                    on_step=show_completed_step,
                )
        except UnidentifiedImageError:
            progress.update(label="Workflow needs a clearer image", state="error")
            st.error("We could not read that image. Please upload a clear JPG or PNG photo of the produce.")
        except ValueError as error:
            progress.update(label="Workflow needs input", state="error")
            if "Choose a crop manually" in str(error):
                st.warning("We could not confidently identify the crop from this photo.")
                st.info("Choose the crop from the sidebar’s Crop override menu, then analyse again.")
            else:
                st.warning(f"Please review the inputs: {error}")
        except Exception as error:
            progress.update(label="Workflow could not complete", state="error")
            if "not cached locally" in str(error):
                st.error("The offline vision model has not been prepared on this device. Run the one-time model cache setup before the demo.")
            else:
                st.error("Mandi Mitra could not complete this analysis. Please try another clear image or review the selected inputs.")
        else:
            progress.update(label="✅ Agent workflow complete", state="complete", expanded=True)
            comparisons_by_market = {item.market: item for item in result.decision.market_comparisons}
            left, right = st.columns([1, 2])
            with left:
                st.image(image, caption="Uploaded produce")
                st.metric("Detected crop", result.vision.crop or "Manual selection")
                st.metric("Demo grade", result.vision.grade or "Not available")
                st.caption("Demo grading heuristic; not a certified quality standard.")
            with right:
                is_wait = result.decision.recommendation == "wait"
                badge = "⏳ WAIT" if is_wait else "🚜 SELL NOW"
                badge_class = "wait-badge" if is_wait else "sell-badge"
                st.markdown(f'<span class="recommendation-badge {badge_class}">{badge}</span>', unsafe_allow_html=True)
                st.subheader(f"🏪 {result.decision.recommended_market}")
                st.write(" ".join(result.decision.reasoning))
                with st.expander("Why this recommendation?"):
                    st.markdown("\n".join(result.decision.explanation))
                st.subheader("Market comparison")
                st.caption("Projected trend (estimate based on recent mock price history) — a lightweight statistical projection, not a guarantee.")
                if any(item.state == "Tamil Nadu" for item in result.decision.market_comparisons):
                    st.info(
                        "Data source note: Tamil Nadu markets use illustrative demo data. Other displayed states use historical mandi data. "
                        "Available Agmarknet reports did not contain complete matching records for these three Tamil Nadu demo markets."
                    )
                comparison_data = pd.DataFrame([
                    {
                        "State": item.state,
                        "Data source": "Illustrative demo data" if item.state == "Tamil Nadu" else "Historical mandi data",
                        "Market": f"🏪 {item.market}",
                        "Distance (km)": round(item.distance_km),
                        "Net proceeds (₹)": round(item.net_value_inr),
                        "2-day projected price (₹/q)": round(item.projected_price_inr_per_quintal),
                        "Projected trend (estimate)": f"{item.projected_change_percent:+.1f}%",
                        "Transport (₹)": round(item.transport_cost_inr),
                    }
                    for item in result.decision.market_comparisons
                ]).sort_values(["State", "Net proceeds (₹)"], ascending=[True, False])
                st.dataframe(comparison_data, use_container_width=True, hide_index=True)

                if result.decision.distance_warning:
                    st.warning(f"⚠️ {result.decision.distance_warning}")

            st.subheader("Feasible market map")
            st.caption("Only markets within this crop's feasible distance are shown. Lines are a visual guide; labels use configured road-distance estimates.")
            market_map = feasible_market_map(locations[location_id], result.decision.market_comparisons)
            if market_map:
                st.pydeck_chart(market_map, use_container_width=True, height=350)
            else:
                st.info("No market is within the feasible distance for this crop, so no market route is shown.")

            chart_left, chart_right = st.columns(2)
            with chart_left:
                st.subheader("Net proceeds by market")
                net_chart = pd.DataFrame([
                    {"Market": f"🏪 {item.market}", "Net proceeds (₹)": round(item.net_value_inr)}
                    for item in result.decision.market_comparisons
                ]).set_index("Market")
                st.bar_chart(net_chart, color="#3F7D4D")
            with chart_right:
                recommended_snapshot = next(
                    snapshot for snapshot in result.prices.market_snapshots
                    if snapshot.market == result.decision.recommended_market
                )
                st.subheader(f"7-day history + 2-day estimate: {result.decision.recommended_market}")
                st.altair_chart(forecast_chart(recommended_snapshot, comparisons_by_market[recommended_snapshot.market]), use_container_width=True)

            st.subheader("Market-by-market trend estimates")
            st.caption("Solid green: historical mock price. Dashed brown: projected trend estimate based on recent mock history; not a guarantee.")
            market_charts = st.columns(2)
            feasible_snapshots = feasible_snapshots_for_charts(
                result.prices.market_snapshots,
                comparisons_by_market,
            )
            for index, snapshot in enumerate(feasible_snapshots):
                with market_charts[index % 2]:
                    st.markdown(f"**🏪 {snapshot.market}** · {snapshot.latest.state}")
                    st.altair_chart(forecast_chart(snapshot, comparisons_by_market[snapshot.market]), use_container_width=True)

            st.subheader("WhatsApp-style message")
            safe_message = html.escape(result.message.text).replace("\n", "<br>")
            st.markdown(
                f'<div class="whatsapp-bubble"><div class="whatsapp-sender">Mandi Mitra • Draft</div>{safe_message}</div>',
                unsafe_allow_html=True,
            )
            with st.expander("Full agent reasoning trail", expanded=True):
                for item in result.trail:
                    st.json(item)
else:
    st.info("Upload a photo and choose the inputs to see the complete four-step reasoning trail.")
