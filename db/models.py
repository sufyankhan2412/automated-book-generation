"""
Database helper functions — CRUD for books, outlines, chapters, notifications.
"""

from __future__ import annotations
from typing import Any
from db.supabase_client import get_client


# ═══════════════════════════════════════════════════════
#  BOOKS
# ═══════════════════════════════════════════════════════

def create_book(title: str, notes_before: str = "") -> dict:
    """Insert a new book record and return it."""
    data = {
        "title": title,
        "notes_on_outline_before": notes_before,
        "book_output_status": "pending",
    }
    result = get_client().table("books").insert(data).execute()
    return result.data[0]


def get_book(book_id: str) -> dict | None:
    """Fetch a single book by ID."""
    result = get_client().table("books").select("*").eq("id", book_id).execute()
    return result.data[0] if result.data else None


def update_book(book_id: str, **fields) -> dict:
    """Update book fields."""
    result = (
        get_client()
        .table("books")
        .update(fields)
        .eq("id", book_id)
        .execute()
    )
    return result.data[0]


# ═══════════════════════════════════════════════════════
#  OUTLINES
# ═══════════════════════════════════════════════════════

def save_outline(book_id: str, outline_text: str, version: int = 1) -> dict:
    """Insert a new outline version."""
    data = {
        "book_id": book_id,
        "outline_text": outline_text,
        "version": version,
    }
    result = get_client().table("outlines").insert(data).execute()
    return result.data[0]


def get_latest_outline(book_id: str) -> dict | None:
    """Get the most recent outline for a book."""
    result = (
        get_client()
        .table("outlines")
        .select("*")
        .eq("book_id", book_id)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_outline_version_count(book_id: str) -> int:
    """How many outline versions exist for this book."""
    result = (
        get_client()
        .table("outlines")
        .select("id", count="exact")
        .eq("book_id", book_id)
        .execute()
    )
    return result.count or 0


# ═══════════════════════════════════════════════════════
#  CHAPTERS
# ═══════════════════════════════════════════════════════

def save_chapter(
    book_id: str,
    chapter_number: int,
    chapter_title: str,
    chapter_text: str,
    summary: str,
    version: int = 1,
) -> dict:
    """Insert or upsert a chapter."""
    # Check if chapter already exists
    existing = (
        get_client()
        .table("chapters")
        .select("id")
        .eq("book_id", book_id)
        .eq("chapter_number", chapter_number)
        .execute()
    )
    data = {
        "book_id": book_id,
        "chapter_number": chapter_number,
        "chapter_title": chapter_title,
        "chapter_text": chapter_text,
        "summary": summary,
        "version": version,
    }
    if existing.data:
        result = (
            get_client()
            .table("chapters")
            .update(data)
            .eq("id", existing.data[0]["id"])
            .execute()
        )
    else:
        result = get_client().table("chapters").insert(data).execute()
    return result.data[0]


def get_chapter(book_id: str, chapter_number: int) -> dict | None:
    """Get a specific chapter."""
    result = (
        get_client()
        .table("chapters")
        .select("*")
        .eq("book_id", book_id)
        .eq("chapter_number", chapter_number)
        .execute()
    )
    return result.data[0] if result.data else None


def get_all_chapters(book_id: str) -> list[dict]:
    """Get all chapters for a book, ordered by chapter_number."""
    result = (
        get_client()
        .table("chapters")
        .select("*")
        .eq("book_id", book_id)
        .order("chapter_number")
        .execute()
    )
    return result.data


def get_previous_summaries(book_id: str, up_to_chapter: int) -> list[str]:
    """Return summaries of chapters 1 .. up_to_chapter-1."""
    result = (
        get_client()
        .table("chapters")
        .select("chapter_number, summary")
        .eq("book_id", book_id)
        .lt("chapter_number", up_to_chapter)
        .order("chapter_number")
        .execute()
    )
    return [
        f"Chapter {r['chapter_number']}: {r['summary']}"
        for r in result.data
        if r.get("summary")
    ]


def update_chapter(book_id: str, chapter_number: int, **fields) -> dict:
    """Update specific fields on a chapter."""
    result = (
        get_client()
        .table("chapters")
        .update(fields)
        .eq("book_id", book_id)
        .eq("chapter_number", chapter_number)
        .execute()
    )
    return result.data[0]


# ═══════════════════════════════════════════════════════
#  NOTIFICATIONS LOG
# ═══════════════════════════════════════════════════════

def log_notification(book_id: str, event: str, message: str) -> dict:
    """Log a notification event in Supabase."""
    data = {
        "book_id": book_id,
        "event": event,
        "message": message,
    }
    result = get_client().table("notifications").insert(data).execute()
    return result.data[0]
