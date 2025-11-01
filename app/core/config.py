import os
from dataclasses import dataclass
from dotenv import load_dotenv, find_dotenv

_env_file = os.getenv("ENV_FILE", ".env.local")
if os.path.exists(_env_file):
    load_dotenv(_env_file)
else:
    _found = find_dotenv(".env")
    if _found:
        load_dotenv(_found)


def _to_int(value: str, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


@dataclass
class Settings:
    DATA_DIR: str = os.getenv("DATA_DIR", os.path.join(os.getcwd(), "data"))
    DB_PATH: str = os.getenv("DB_PATH", os.path.join(DATA_DIR, "db.sqlite3"))
    INDEX_PATH: str = os.getenv("INDEX_PATH", os.path.join(DATA_DIR, "index.faiss"))
    INDEX_META_PATH: str = os.getenv("INDEX_META_PATH", os.path.join(DATA_DIR, "index_meta.json"))

    MODEL_NAME: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    DEVICE: str = os.getenv("DEVICE", "cpu")

    CHUNK_SIZE_CHARS: int = _to_int(os.getenv("CHUNK_SIZE_CHARS", "1000"), 1000)
    CHUNK_OVERLAP_CHARS: int = _to_int(os.getenv("CHUNK_OVERLAP_CHARS", "200"), 200)

    TOP_K_DEFAULT: int = _to_int(os.getenv("TOP_K_DEFAULT", "5"), 5)

    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")


settings = Settings()

os.makedirs(settings.DATA_DIR, exist_ok=True)
