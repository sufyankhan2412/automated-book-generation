"""
Chapter summarizer — generates a concise summary of a chapter
for context chaining to subsequent chapters.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import get_llm, invoke_with_retry


def summarize_chapter(chapter_title: str, chapter_text: str) -> str:
    """
    Produce a 3-5 sentence summary of the given chapter.
    This summary is used as context when generating later chapters.
    """
    llm = get_llm()
    messages = [
        SystemMessage(
            content=(
                "You are a book editor assistant. Your job is to produce a concise "
                "3-5 sentence summary of the chapter provided. The summary should "
                "capture the key themes, events, arguments, and any important details "
                "that a future chapter might need to reference for continuity."
            )
        ),
        HumanMessage(
            content=(
                f"Chapter Title: {chapter_title}\n\n"
                f"Chapter Content:\n{chapter_text}\n\n"
                "Please provide a concise summary."
            )
        ),
    ]
    return invoke_with_retry(llm, messages)
