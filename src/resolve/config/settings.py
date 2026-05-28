"""Verify — centralised settings loaded from environment variables."""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")

AUTO_RESOLVE_THRESHOLD = float(os.getenv("AUTO_RESOLVE_THRESHOLD", "0.95"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "voyage-3-lite")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
