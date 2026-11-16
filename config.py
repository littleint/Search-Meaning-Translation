"""
=============================================================================
Application Configuration & Settings
=============================================================================
Modify settings here to customize the application behavior:
- Add or remove supported languages in SUPPORTED_LANGUAGES.
- Change default AI model or fallback models.
- Adjust session cookie expiration times.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Security & Session ---
SECRET_KEY = os.getenv("SECRET_KEY", "vocab_super_secret_jwt_key_2026_change_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# --- Groq AI Settings ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

# --- Database Path & URL ---
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab.db")

# --- Supported Languages for Dropdowns & Translation ---
# To add a new language, simply append it to this list!
SUPPORTED_LANGUAGES = [
    "English",
    "Spanish",
    "French",
    "German",
    "Hindi",
    "Japanese",
    "Chinese",
    "Arabic",
    "Russian",
    "Portuguese",
    "Italian",
    "Korean",
    "Dutch",
    "Turkish",
    "Swedish"
]

DEFAULT_SOURCE_LANG = "auto"
DEFAULT_TARGET_LANG = "English"
