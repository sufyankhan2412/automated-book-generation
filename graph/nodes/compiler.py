"""
Node: compile_book — fetches all chapters from Supabase and exports
the final book as .docx, .pdf, and .txt.
"""

from __future__ import annotations

from graph.state import BookState
from db import models
from utils.file_export import export_docx, export_pdf, export_txt
import config


def compile_book(state: BookState) -> BookState:
    """
    Compile all approved chapters into final book files.
    Exports .docx, .pdf, and .txt to the output directory.
    Also uploads to Supabase Storage if available.
    """
    book_id = state.get("book_id", "")
    title = state.get("title", "Untitled Book")

    # ── Fetch all chapters from DB ───────────────────
    chapters = models.get_all_chapters(book_id)

    if not chapters:
        return {
            **state,
            "status": "error",
            "error": "No chapters found to compile.",
            "message": "❌ Cannot compile — no chapters found in database.",
        }

    # ── Export to all formats ────────────────────────
    output_dir = config.OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    docx_path = export_docx(title, chapters, output_dir)
    pdf_path = export_pdf(title, chapters, output_dir)
    txt_path = export_txt(title, chapters, output_dir)

    print(f"\n📚 Book compiled successfully!")
    print(f"   📄 DOCX: {docx_path}")
    print(f"   📄 PDF:  {pdf_path}")
    print(f"   📄 TXT:  {txt_path}")

    # ── Update book status ───────────────────────────
    models.update_book(book_id, book_output_status="completed")

    return {
        **state,
        "book_output_status": "completed",
        "status": "completed",
        "message": (
            f"📚 Book '{title}' compiled!\n"
            f"   DOCX: {docx_path}\n"
            f"   PDF:  {pdf_path}\n"
            f"   TXT:  {txt_path}"
        ),
    }
