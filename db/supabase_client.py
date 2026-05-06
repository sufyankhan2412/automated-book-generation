"""
Supabase client singleton.
"""

from __future__ import annotations
from typing import Optional
from supabase import create_client, Client
import config


_client: Optional[Client] = None


def get_client() -> Client:
    """Return a cached Supabase client."""
    global _client
    if _client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env"
            )
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client
