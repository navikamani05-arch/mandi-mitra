"""Offline, deterministic WhatsApp-style drafts."""

from __future__ import annotations

from pipeline.models import MessageDraft


def draft_message(language: str, crop: str, quantity_kg: float, grade: str, market: str, asking_price: float) -> MessageDraft:
    if language == "Hindi":
        text = (f"नमस्ते, मेरे पास {grade} ग्रेड {crop} की {quantity_kg:.0f} किलो उपज उपलब्ध है। "
                f"सुझाया गया बाजार: {market}। अपेक्षित भाव ₹{asking_price:,.0f} प्रति क्विंटल है। खरीद में रुचि हो तो कृपया संदेश करें।")
    elif language == "Tamil":
        text = (f"வணக்கம், என்னிடம் {grade} தரம் {crop} {quantity_kg:.0f} கிலோ உள்ளது. "
                f"பரிந்துரைக்கப்படும் சந்தை: {market}. எதிர்பார்க்கும் விலை குவிண்டாலுக்கு ₹{asking_price:,.0f}. வாங்க விருப்பமிருந்தால் செய்தி அனுப்பவும்.")
    else:
        raise ValueError("Only Hindi and Tamil are supported in this demo.")
    return MessageDraft(language=language, text=text)
