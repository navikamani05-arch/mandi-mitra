"""Run once while online to populate Hugging Face's local cache for demo day."""

from transformers import CLIPModel, CLIPProcessor

from config.settings import CLIP_MODEL_ID

CLIPModel.from_pretrained(CLIP_MODEL_ID)
CLIPProcessor.from_pretrained(CLIP_MODEL_ID)
print(f"Cached {CLIP_MODEL_ID}. The app now loads it with local_files_only=True.")
