import os
import re
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    QWEN_LIGHT: str = "qwen3.5:2b"
    QWEN_MEDIUM: str = "qwen3.5:4b"
    QWEN_HEAVY: str = "qwen3.5:9b"
    EMBED_MODEL: str = "embeddinggemma:300m"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    BASE_DIR: Path = Path(__file__).resolve().parent
    CHROMA_DIR: Path = BASE_DIR / "chroma_db"
    OUTPUTS_DIR: Path = BASE_DIR / "outputs"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

QWEN_LIGHT = settings.QWEN_LIGHT
QWEN_MEDIUM = settings.QWEN_MEDIUM
QWEN_HEAVY = settings.QWEN_HEAVY
EMBED_MODEL = settings.EMBED_MODEL
CHUNK_SIZE = settings.CHUNK_SIZE
CHUNK_OVERLAP = settings.CHUNK_OVERLAP
CHROMA_DIR = settings.CHROMA_DIR
OUTPUTS_DIR = settings.OUTPUTS_DIR

def slugify(text: str) -> str:
    """Convert text to a valid filename slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

# Ensure directories exist
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUTS_DIR / "notes").mkdir(parents=True, exist_ok=True)
(OUTPUTS_DIR / "research").mkdir(parents=True, exist_ok=True)
