from PIL import Image

from pipeline.models import VisionResult
from pipeline.orchestrator import MandiMitraPipeline


class StubVision:
    def analyze(self, _image, on_model_download=None):
        return VisionResult("tomato", 0.9, "A", False, ("Stub vision result.",))


def test_pipeline_chains_all_four_modules(tmp_path):
    pipeline = MandiMitraPipeline(vision=StubVision(), log_directory=tmp_path)
    result = pipeline.run(Image.new("RGB", (10, 10), "red"), 100, "Hindi", "nashik_demo_village")
    assert result.prices.crop == "tomato"
    assert result.decision.recommended_market
    assert result.message.language == "Hindi"
    assert [step["step"] for step in result.trail] == ["vision", "price_data", "decision", "message"]


def test_pipeline_recalculates_for_a_different_farm_location(tmp_path):
    pipeline = MandiMitraPipeline(vision=StubVision(), log_directory=tmp_path)
    image = Image.new("RGB", (10, 10), "red")
    coimbatore_result = pipeline.run(image, 100, "Tamil", "coimbatore_demo_village", manual_crop="paddy")
    bengaluru_result = pipeline.run(image, 100, "Tamil", "bengaluru_demo_village", manual_crop="paddy")
    assert len(bengaluru_result.decision.market_comparisons) == 5
    assert any(item.state == "Karnataka" for item in bengaluru_result.decision.market_comparisons)
    coimbatore_net = next(item.net_value_inr for item in coimbatore_result.decision.market_comparisons if item.market == "Coimbatore Market")
    bengaluru_net = next(item.net_value_inr for item in bengaluru_result.decision.market_comparisons if item.market == "Coimbatore Market")
    assert coimbatore_net > bengaluru_net


def test_pipeline_reports_completed_agent_stages(tmp_path):
    completed = []
    pipeline = MandiMitraPipeline(vision=StubVision(), log_directory=tmp_path)
    pipeline.run(
        Image.new("RGB", (10, 10), "red"), 100, "Hindi", "nashik_demo_village",
        on_step=lambda agent, summary: completed.append((agent, summary)),
    )
    assert [agent for agent, _ in completed] == [
        "Vision Agent", "Price Data Agent", "Decision Agent", "Message Agent"
    ]
