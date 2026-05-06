"""
Node: notify — sends email notifications on key events.
Also logs the notification in Supabase.
"""

from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import config
from graph.state import BookState
from db import models


# ═══════════════════════════════════════════════════════
#  Notification node (called by the graph)
# ═══════════════════════════════════════════════════════

def notify(state: BookState) -> BookState:
    """
    Send an email notification based on the current state message.
    Logs the notification to Supabase.
    """
    book_id = state.get("book_id", "")
    title = state.get("title", "Untitled")
    message = state.get("message", "No details.")
    status = state.get("status", "running")

    # Determine event type from status
    event = _determine_event(state)

    subject = f"[Book Generator] {title} — {event}"
    body = (
        f"Book: {title}\n"
        f"Event: {event}\n"
        f"Status: {status}\n\n"
        f"Details:\n{message}\n"
    )

    # ── Send email ───────────────────────────────────
    email_sent = _send_email(subject, body)

    # ── Log to Supabase ──────────────────────────────
    if book_id:
        try:
            models.log_notification(book_id, event, message)
        except Exception as e:
            print(f"⚠️  Could not log notification to DB: {e}")

    if email_sent:
        print(f"📧 Notification sent: {event}")
    else:
        print(f"⚠️  Email not sent (check SMTP settings). Event: {event}")

    return state  # pass-through, don't modify state


# ═══════════════════════════════════════════════════════
#  Internal helpers
# ═══════════════════════════════════════════════════════

def _determine_event(state: BookState) -> str:
    """Infer a human-readable event name from the state."""
    status = state.get("status", "")
    message = state.get("message", "").lower()

    if "error" in status:
        return "Error / Missing Input"
    if "outline" in message and "generated" in message:
        return "Outline Ready for Review"
    if "chapter" in message and "generated" in message:
        ch = state.get("current_chapter", "?")
        return f"Chapter {ch} Ready for Review"
    if "compiled" in message or "completed" in status:
        return "Final Draft Compiled"
    if "pause" in status or "waiting" in message:
        return "Workflow Paused — Input Needed"
    return "Status Update"


def _send_email(subject: str, body: str) -> bool:
    """Send a plain-text email via SMTP. Returns True on success."""
    if not config.SMTP_USER or not config.SMTP_PASSWORD or not config.NOTIFICATION_EMAIL_TO:
        return False

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

        return True
    except Exception as e:
        print(f"⚠️  SMTP error: {e}")
        return False
