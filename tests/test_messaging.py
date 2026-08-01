import pytest

from modules.messaging import draft_message


def test_hindi_template_includes_key_selling_fields():
    message = draft_message("Hindi", "tomato", 100, "A", "Nashik APMC", 1800)
    assert "tomato" in message.text
    assert "100" in message.text
    assert "Nashik APMC" in message.text


def test_tamil_template_is_selected():
    message = draft_message("Tamil", "onion", 50, "B", "Lasalgaon Mandi", 2400)
    assert "வணக்கம்" in message.text


def test_rejects_unsupported_language():
    with pytest.raises(ValueError, match="Hindi and Tamil"):
        draft_message("English", "tomato", 10, "A", "Nashik APMC", 1800)
