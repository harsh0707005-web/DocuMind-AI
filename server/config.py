"""Configuration for DocuMind AI backend."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "documind")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Google Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # App settings
    UPLOAD_DIR: str = os.path.join(os.path.dirname(__file__), "uploads")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".txt", ".py", ".js", ".ts", ".java", ".cpp", ".c", ".md", ".csv"}

    # RAG settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5

    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
