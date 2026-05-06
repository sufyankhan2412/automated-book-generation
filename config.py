"""
Configuration loader — reads .env and exposes all settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)


# ── LLM ──────────────────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# ── Supabase ─────────────────────────────────────────
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# ── Email (SMTP) ─────────────────────────────────────
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
NOTIFICATION_EMAIL_TO: str = os.getenv("NOTIFICATION_EMAIL_TO", "")

# ── Paths ────────────────────────────────────────────
PROJECT_ROOT: Path = Path(__file__).resolve().parent
INPUT_EXCEL_PATH: Path = PROJECT_ROOT / os.getenv("INPUT_EXCEL_PATH", "input/book_input.xlsx")
OUTPUT_DIR: Path = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "output")

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
