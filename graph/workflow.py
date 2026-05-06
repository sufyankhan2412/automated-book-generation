"""
LangGraph workflow — defines the full state-machine graph for the
Automated Book Generation System.

Flow:
  read_input → [check] → generate_outline → [check] → generate_chapters → [check] → compile
  With pause/notify branches at each gate.
"""

from __future__ import annotations
from langgraph.graph import StateGraph, END

from graph.state import BookState

# ── Node functions ───────────────────────────────────
from graph.nodes.input_reader import read_input
from graph.nodes.outline_generator import generate_outline
from graph.nodes.chapter_generator import generate_chapter
from graph.nodes.compiler import compile_book
from graph.nodes.notifier import notify

# ── Condition functions ──────────────────────────────
from graph.edges.conditions import (
    check_input_valid,
    check_outline_notes,
    check_chapter_notes,
    check_more_chapters,
    check_final_review,
)


# ═══════════════════════════════════════════════════════
#  Pause / status helper nodes
# ═══════════════════════════════════════════════════════

def pause_missing_notes_before(state: BookState) -> BookState:
    return {
        **state,
        "status": "paused",
        "message": (
            "⏸️  PAUSED: 'notes_on_outline_before' is required before generating "
            "an outline. Please add your notes to the Excel file and re-run."
        ),
    }


def pause_waiting_outline_notes(state: BookState) -> BookState:
    return {
        **state,
        "status": "paused",
        "message": (
            "⏸️  PAUSED: status_outline_notes='yes' but no notes_on_outline_after "
            "provided. Please add your post-outline notes and re-run."
        ),
    }


def pause_outline(state: BookState) -> BookState:
    return {
        **state,
        "status": "paused",
        "message": (
            "⏸️  PAUSED: status_outline_notes is 'no' or empty. "
            "Set to 'no_notes_needed' to proceed, or 'yes' to add notes."
        ),
    }


def pause_waiting_chapter_notes(state: BookState) -> BookState:
    ch = state.get("current_chapter", "?")
    return {
        **state,
        "status": "paused",
        "message": (
            f"⏸️  PAUSED at Chapter {ch}.\n"
            f"   To resume: python main.py --resume"
        ),
    }


def pause_chapter(state: BookState) -> BookState:
    return {
        **state,
        "status": "paused",
        "message": (
            f"⏸️  PAUSED: chapter_notes_status is 'no' or empty for "
            f"Chapter {state.get('current_chapter', '?')}. "
            "Set to 'no_notes_needed' to proceed."
        ),
    }


def pause_waiting_final_notes(state: BookState) -> BookState:
    return {
        **state,
        "status": "paused",
        "message": (
            "⏸️  PAUSED: final_review_notes_status='yes' but no final_review_notes "
            "provided. Please add notes and re-run."
        ),
    }


def pause_final(state: BookState) -> BookState:
    return {
        **state,
        "status": "paused",
        "message": (
            "⏸️  PAUSED: final_review_notes_status is 'no' or empty. "
            "Set to 'no_notes_needed' to compile the book."
        ),
    }


def start_chapters(state: BookState) -> BookState:
    """Transition node: mark that we're starting chapter generation."""
    return {
        **state,
        "current_chapter": 0,
        "chapters_completed": False,
        "status": "running",
        "message": "📚 Starting chapter generation...",
    }


def resume_chapters(state: BookState) -> BookState:
    """Transition node: resume chapter generation from where we left off."""
    ch = state.get("current_chapter", 0)
    total = state.get("total_chapters", 0)
    print(f"📚 Resuming chapter generation from Chapter {ch + 1}/{total}...")
    return {
        **state,
        "chapters_completed": False,
        "status": "running",
        "message": f"📚 Resuming chapter generation from Chapter {ch + 1}...",
    }


def regenerate_outline(state: BookState) -> BookState:
    """Proxy: just marks that we're regenerating (then flows to generate_outline)."""
    print("🔄 Regenerating outline with editor feedback...")
    return state


def regenerate_chapter(state: BookState) -> BookState:
    """Proxy: decrement current_chapter so generate_chapter re-does it."""
    ch = state.get("current_chapter", 1)
    print(f"🔄 Regenerating Chapter {ch} with editor notes...")
    return {
        **state,
        "current_chapter": ch - 1,  # will be incremented back in generate_chapter
    }


def next_chapter_or_done(state: BookState) -> BookState:
    """Check if we've finished all chapters or need to continue."""
    return state  # check_more_chapters will route appropriately


# ═══════════════════════════════════════════════════════
#  Build the LangGraph
# ═══════════════════════════════════════════════════════

def build_workflow() -> StateGraph:
    """Construct and return the compiled LangGraph workflow."""

    graph = StateGraph(BookState)

    # ── Add all nodes ────────────────────────────────
    graph.add_node("read_input", read_input)
    graph.add_node("generate_outline", generate_outline)
    graph.add_node("regenerate_outline", regenerate_outline)
    graph.add_node("start_chapters", start_chapters)
    graph.add_node("resume_chapters", resume_chapters)
    graph.add_node("generate_chapter", generate_chapter)
    graph.add_node("regenerate_chapter", regenerate_chapter)
    graph.add_node("next_chapter_or_done", next_chapter_or_done)
    graph.add_node("compile_book", compile_book)
    graph.add_node("notify", notify)

    # Pause nodes
    graph.add_node("pause_missing_notes_before", pause_missing_notes_before)
    graph.add_node("pause_waiting_outline_notes", pause_waiting_outline_notes)
    graph.add_node("pause_outline", pause_outline)
    graph.add_node("pause_waiting_chapter_notes", pause_waiting_chapter_notes)
    graph.add_node("pause_chapter", pause_chapter)
    graph.add_node("pause_waiting_final_notes", pause_waiting_final_notes)
    graph.add_node("pause_final", pause_final)
    graph.add_node("notify_and_end", notify)

    # ── Set entry point ──────────────────────────────
    graph.set_entry_point("read_input")

    # ── Edges: read_input → conditional ──────────────
    graph.add_conditional_edges(
        "read_input",
        check_input_valid,
        {
            "notify_and_end": "notify_and_end",
            "pause_missing_notes_before": "pause_missing_notes_before",
            "generate_outline": "generate_outline",
            "resume_chapters": "resume_chapters",
        },
    )

    # ── Edges: generate_outline → conditional ────────
    graph.add_conditional_edges(
        "generate_outline",
        check_outline_notes,
        {
            "start_chapters": "start_chapters",
            "regenerate_outline": "regenerate_outline",
            "pause_waiting_outline_notes": "pause_waiting_outline_notes",
            "pause_outline": "pause_outline",
        },
    )

    # regenerate_outline → generate_outline (loop)
    graph.add_edge("regenerate_outline", "generate_outline")

    # ── Edges: start_chapters → generate_chapter ─────
    graph.add_edge("start_chapters", "generate_chapter")

    # ── Edges: resume_chapters → generate_chapter ────
    graph.add_edge("resume_chapters", "generate_chapter")

    # ── Edges: generate_chapter → conditional ────────
    graph.add_conditional_edges(
        "generate_chapter",
        check_chapter_notes,
        {
            "next_chapter_or_done": "next_chapter_or_done",
            "regenerate_chapter": "regenerate_chapter",
            "pause_waiting_chapter_notes": "pause_waiting_chapter_notes",
            "pause_chapter": "pause_chapter",
        },
    )

    # regenerate_chapter → generate_chapter (loop)
    graph.add_edge("regenerate_chapter", "generate_chapter")

    # ── Edges: next_chapter_or_done → conditional ────
    graph.add_conditional_edges(
        "next_chapter_or_done",
        check_more_chapters,
        {
            "generate_chapter": "generate_chapter",
            "check_final_review": "notify",  # notify before final review check
        },
    )

    # ── Edges: after notify → check_final_review ─────
    # We use notify as a pass-through before compilation check
    graph.add_conditional_edges(
        "notify",
        check_final_review,
        {
            "compile_book": "compile_book",
            "pause_waiting_final_notes": "pause_waiting_final_notes",
            "pause_final": "pause_final",
        },
    )

    # ── Edges: compile_book → END ────────────────────
    graph.add_edge("compile_book", END)

    # ── All pause nodes → notify_and_end → END ───────
    for pause_node in [
        "pause_missing_notes_before",
        "pause_waiting_outline_notes",
        "pause_outline",
        "pause_waiting_chapter_notes",
        "pause_chapter",
        "pause_waiting_final_notes",
        "pause_final",
    ]:
        graph.add_edge(pause_node, "notify_and_end")

    graph.add_edge("notify_and_end", END)

    return graph.compile()
