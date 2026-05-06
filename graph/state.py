"""
LangGraph state definition — the single typed dictionary that flows
through every node in the workflow.
"""

from __future__ import annotations
from typing import TypedDict, Optional


class BookState(TypedDict, total=False):
    """
    Shared state for the book-generation workflow.
    Every node reads from and writes to this dictionary.
    """

    # ── Input fields (from Excel) ────────────────────
    title: str
    notes_on_outline_before: str
    notes_on_outline_after: str
    status_outline_notes: str           # yes | no | no_notes_needed

    # ── Outline ──────────────────────────────────────
    book_id: str                        # Supabase book UUID
    outline: str                        # generated outline text
    outline_version: int
    outline_chapters: list[str]         # parsed chapter titles from outline

    # ── Chapter generation ───────────────────────────
    current_chapter: int                # 1-based index being processed
    total_chapters: int
    chapter_notes_status: str           # yes | no | no_notes_needed
    chapter_notes: str                  # per-chapter editor notes
    chapters_completed: bool

    # ── Final compilation ────────────────────────────
    final_review_notes: str
    final_review_notes_status: str      # yes | no | no_notes_needed
    book_output_status: str             # pending | completed | paused

    # ── Control flow ─────────────────────────────────
    status: str                         # running | paused | completed | error
    message: str                        # human-readable status message
    error: str                          # error details if any
