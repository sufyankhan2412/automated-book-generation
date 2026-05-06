"""
Node: generate_outline — uses the LLM to produce a book outline
from the title and editor notes, stores it in Supabase.
"""

from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage

from graph.state import BookState
from utils.llm import get_llm, invoke_with_retry
from db import models


def generate_outline(state: BookState) -> BookState:
    """
    Generate (or regenerate) a book outline.
    Uses: title + notes_on_outline_before + notes_on_outline_after (if any).
    """
    title = state.get("title", "")
    notes_before = state.get("notes_on_outline_before", "")
    notes_after = state.get("notes_on_outline_after", "")

    # ── Build prompt ─────────────────────────────────
    prompt_parts = [
        f"Book Title: {title}",
        f"\nEditor Notes (before outline): {notes_before}",
    ]
    if notes_after:
        prompt_parts.append(
            f"\nEditor Notes (after reviewing previous outline): {notes_after}"
        )
        prompt_parts.append(
            "\nPlease incorporate the editor's feedback into the revised outline."
        )

    llm = get_llm()
    messages = [
        SystemMessage(
            content=(
                "You are a professional book outline generator. "
                "Given a book title and editorial notes, produce a detailed "
                "chapter-by-chapter outline. Each chapter should have a clear "
                "title and a 2-3 sentence description of what it covers. "
                "Format each chapter EXACTLY as (no bold, no markdown):\n"
                "Chapter N: <Title>\n"
                "Description: <what this chapter covers>\n\n"
                "Do NOT use ** or ## or any markdown formatting.\n"
                "Produce between 5-10 chapters depending on the scope of the book."
            )
        ),
        HumanMessage(content="\n".join(prompt_parts)),
    ]
    response_text = invoke_with_retry(llm, messages)
    outline_text = response_text

    # ── Parse chapter titles from outline ────────────
    chapter_titles = _parse_chapter_titles(outline_text)

    # ── Persist in Supabase ──────────────────────────
    book_id = state.get("book_id", "")

    # Create or update book record
    if not book_id:
        book = models.create_book(title, notes_before)
        book_id = book["id"]
    else:
        models.update_book(
            book_id,
            notes_on_outline_before=notes_before,
            notes_on_outline_after=notes_after,
        )

    # Save outline version
    version = models.get_outline_version_count(book_id) + 1
    models.save_outline(book_id, outline_text, version)

    print(f"\n📝 Outline v{version} generated ({len(chapter_titles)} chapters)")
    print(f"{'─' * 50}")
    print(outline_text[:500] + ("..." if len(outline_text) > 500 else ""))
    print(f"{'─' * 50}\n")

    return {
        **state,
        "book_id": book_id,
        "outline": outline_text,
        "outline_version": version,
        "outline_chapters": chapter_titles,
        "total_chapters": len(chapter_titles),
        "current_chapter": 0,
        "chapters_completed": False,
        "status": "running",
        "message": f"📝 Outline v{version} generated with {len(chapter_titles)} chapters.",
    }


def _parse_chapter_titles(outline_text: str) -> list[str]:
    """
    Extract chapter titles from the outline text.
    Handles formats like:
      Chapter 1: The Beginning
      **Chapter 1: The Beginning**
      ## Chapter 1 - The Beginning
    """
    import re
    titles: list[str] = []
    for line in outline_text.split("\n"):
        # Strip markdown bold **, *, and heading ## markers
        cleaned = re.sub(r'[\*#]+', '', line).strip()
        match = re.match(r"(?:chapter\s+\d+)\s*[:\-\u2013\u2014]\s*(.+)", cleaned, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Remove any trailing ** or formatting artifacts
            title = re.sub(r'[\*#]+', '', title).strip()
            if title:
                titles.append(title)
    # Fallback: if no titles parsed, create generic ones
    if not titles:
        titles = [f"Chapter {i+1}" for i in range(8)]
    return titles
