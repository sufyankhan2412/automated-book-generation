"""
Node: generate_chapter — generates one chapter at a time,
using previous chapter summaries for context chaining.
Includes interactive terminal review: user approves or gives
feedback after each chapter without leaving the terminal.
"""

from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage

from graph.state import BookState
from utils.llm import get_llm, invoke_with_retry
from utils.summarizer import summarize_chapter
from db import models
import config


def _build_messages(title, outline, summary_context, current, chapter_title, chapter_notes=""):
    """Build the LLM messages for chapter generation."""
    prompt_parts = [
        f"Book Title: {title}",
        f"\nFull Book Outline:\n{outline}",
        f"\nPrevious Chapter Summaries:\n{summary_context}",
        f"\nNow write Chapter {current}: {chapter_title}",
        "\nWrite an extremely detailed, in-depth, and engaging chapter of at least 3500-4000 words (approximately 7 pages).",
        "Include multiple subsections with clear headings.",
        "Use real-world examples, case studies, data points, and expert perspectives.",
        "Maintain continuity with the previous chapters based on the summaries provided.",
        "Do NOT use markdown bold (**) or heading (#) formatting. Use plain text only.",
        "For subsection titles, just write the title on its own line without any special formatting.",
    ]
    if chapter_notes:
        prompt_parts.append(f"\nEditor notes for this chapter: {chapter_notes}")

    return [
        SystemMessage(
            content=(
                "You are a professional book writer. You write detailed, engaging, "
                "well-structured chapters of at least 3500 words each. "
                "Maintain narrative continuity by using the provided summaries of previous chapters. "
                "Follow the outline structure closely. Write in a clear, professional style. "
                "IMPORTANT FORMATTING RULES: "
                "1. Do NOT use any markdown formatting like ** or # or ## anywhere. "
                "2. Write section headings as plain text on their own line. "
                "3. Do NOT start with 'Chapter N:' title - just begin the chapter content directly. "
                "4. Use clear paragraph breaks between sections. "
                "5. The chapter must be at least 3500 words long with rich detail."
            )
        ),
        HumanMessage(content="\n".join(prompt_parts)),
    ]


def _show_chapter_preview(current, total, chapter_title, chapter_text, summary, version):
    """Print a chapter preview to the terminal."""
    word_count = len(chapter_text.split())
    preview = chapter_text[:1500]

    print(f"\n{'=' * 60}")
    print(f"  📖 Chapter {current}/{total}: '{chapter_title}' (v{version})")
    print(f"  Word count: ~{word_count} words")
    print(f"{'=' * 60}")
    print(f"\n📋 SUMMARY: {summary}\n")
    print(f"{'─' * 60}")
    print(f"PREVIEW (first 1500 chars):\n")
    print(preview)
    if len(chapter_text) > 1500:
        print(f"\n  ... [{len(chapter_text) - 1500} more characters] ...")
    print(f"{'─' * 60}")


def _ask_user_review(current, total, chapter_title):
    """
    Ask the user in the terminal whether to approve or revise.
    Returns (approved: bool, notes: str).
    """
    print(f"\n🔍 REVIEW Chapter {current}/{total}: '{chapter_title}'")
    print(f"   [y] Approve and continue to next chapter")
    print(f"   [n] Revise — provide feedback to regenerate")
    print()

    while True:
        choice = input("   ➤ Approve this chapter? (y/n): ").strip().lower()
        if choice in ("y", "yes"):
            print(f"   ✅ Chapter {current} approved!\n")
            return True, ""
        elif choice in ("n", "no"):
            print(f"\n   📝 What changes would you like for this chapter?")
            print(f"      (Type your feedback, then press Enter)")
            notes = input("   ➤ Your notes: ").strip()
            if not notes:
                print("   ⚠️  No notes provided. Let's try again.")
                continue
            print(f"   🔄 Regenerating Chapter {current} with your feedback...\n")
            return False, notes
        else:
            print("   ⚠️  Please enter 'y' or 'n'.")


def generate_chapter(state: BookState) -> BookState:
    """
    Generate the next chapter with interactive terminal review.
    After generating, shows a preview and asks the user to approve or
    provide notes. Loops until the user approves.
    """
    title = state.get("title", "")
    outline = state.get("outline", "")
    chapter_titles = state.get("outline_chapters", [])
    current = state.get("current_chapter", 0) + 1  # advance to next
    total = state.get("total_chapters", len(chapter_titles))
    book_id = state.get("book_id", "")
    chapter_notes = state.get("chapter_notes", "")

    if current > total:
        return {
            **state,
            "current_chapter": current,
            "chapters_completed": True,
            "status": "running",
            "message": "✅ All chapters generated.",
        }

    chapter_title = chapter_titles[current - 1] if current <= len(chapter_titles) else f"Chapter {current}"

    # ── Gather previous chapter summaries ────────────
    previous_summaries = models.get_previous_summaries(book_id, current)
    summary_context = "\n".join(previous_summaries) if previous_summaries else "This is the first chapter."

    llm = get_llm()
    version = 0

    # ── Generate → Review → Approve loop ─────────────
    while True:
        messages = _build_messages(title, outline, summary_context, current, chapter_title, chapter_notes)
        chapter_text = invoke_with_retry(llm, messages)

        # Generate summary
        summary = summarize_chapter(chapter_title, chapter_text)

        # Save to Supabase
        existing = models.get_chapter(book_id, current)
        version = (existing["version"] + 1) if existing else 1

        models.save_chapter(
            book_id=book_id,
            chapter_number=current,
            chapter_title=chapter_title,
            chapter_text=chapter_text,
            summary=summary,
            version=version,
        )

        # Show preview to user
        _show_chapter_preview(current, total, chapter_title, chapter_text, summary, version)

        # Send email notification
        _notify_chapter_ready(state, current, total, chapter_title, chapter_text, summary)

        # Ask user for review
        approved, notes = _ask_user_review(current, total, chapter_title)

        if approved:
            break
        else:
            # User wants revisions — loop with their notes
            chapter_notes = notes

    # ── Chapter approved ─────────────────────────────
    all_done = current >= total

    return {
        **state,
        "current_chapter": current,
        "chapters_completed": all_done,
        "chapter_notes": "",
        "chapter_notes_status": "no_notes_needed",
        "status": "running",
        "message": f"\U0001f4d6 Chapter {current}/{total} approved: '{chapter_title}'",
    }


def _notify_chapter_ready(state, chapter_num, total, chapter_title, chapter_text, summary):
    """Send an email notification when a chapter is ready for review."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    title = state.get("title", "Untitled")
    preview = chapter_text[:2000]
    word_count = len(chapter_text.split())

    subject = f"[Book Generator] Chapter {chapter_num}/{total} Ready: {chapter_title}"
    body = (
        f"Book: {title}\n"
        f"Chapter {chapter_num} of {total}: {chapter_title}\n"
        f"Word Count: ~{word_count} words\n"
        f"{'=' * 50}\n\n"
        f"SUMMARY:\n{summary}\n\n"
        f"{'=' * 50}\n\n"
        f"CHAPTER PREVIEW (first 2000 chars):\n\n{preview}\n\n"
        f"{'=' * 50}\n\n"
        f"Chapter has been generated and is awaiting your review in the terminal.\n"
    )

    try:
        msg = MIMEMultipart()
        msg["From"] = config.SMTP_USER
        msg["To"] = config.NOTIFICATION_EMAIL_TO
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
        print(f"   \U0001f4e7 Email sent: Chapter {chapter_num} ready for review")
    except Exception as e:
        print(f"   \u26a0\ufe0f Email failed: {e}")
