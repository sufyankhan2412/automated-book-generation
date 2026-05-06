"""
Conditional edge functions for LangGraph routing.
Each function inspects the state and returns the name of the next node.
"""

from __future__ import annotations
from graph.state import BookState


def check_input_valid(state: BookState) -> str:
    """After reading input, check if we can proceed."""
    if state.get("status") == "error":
        return "notify_and_end"

    # If we're resuming (already have book_id + outline), skip to chapters
    if state.get("book_id") and state.get("outline"):
        return "resume_chapters"

    # notes_on_outline_before is required before generating outline
    if not state.get("notes_on_outline_before", "").strip():
        return "pause_missing_notes_before"

    return "generate_outline"


def check_outline_notes(state: BookState) -> str:
    """
    After outline generation, check status_outline_notes
    to decide whether to wait, proceed, or pause.
    """
    status = state.get("status_outline_notes", "").strip().lower()

    if status == "no_notes_needed":
        return "start_chapters"
    elif status == "yes":
        # Editor wants to provide notes — check if they exist
        if state.get("notes_on_outline_after", "").strip():
            return "regenerate_outline"
        else:
            return "pause_waiting_outline_notes"
    else:
        # "no" or empty → pause
        return "pause_outline"


def check_chapter_notes(state: BookState) -> str:
    """
    After generating a chapter, always proceed.
    Chapter review now happens interactively inside the generate_chapter node.
    """
    return "next_chapter_or_done"


def check_more_chapters(state: BookState) -> str:
    """Check if there are more chapters to generate."""
    if state.get("chapters_completed", False):
        return "check_final_review"
    return "generate_chapter"


def check_final_review(state: BookState) -> str:
    """
    Before compilation, check final_review_notes_status.
    """
    status = state.get("final_review_notes_status", "").strip().lower()

    if status == "no_notes_needed":
        return "compile_book"
    elif status == "yes":
        if state.get("final_review_notes", "").strip():
            return "compile_book"  # proceed with notes applied
        else:
            return "pause_waiting_final_notes"
    else:
        # "no" or empty → pause
        return "pause_final"
