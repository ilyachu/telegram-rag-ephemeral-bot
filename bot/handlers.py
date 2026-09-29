from __future__ import annotations

import logging

from .config import Settings
from .ephemeral import (
    PROGRESS,
    format_answer_html,
    send_private_status,
    update_private_status,
)
from .parse import AskContext
from .rag import ask_rag
from .telegram_api import TelegramClient

log = logging.getLogger(__name__)

MAX_TELEGRAM_TEXT = 4096


def _fit(text: str, limit: int = MAX_TELEGRAM_TEXT) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def handle_ask(client: TelegramClient, context: AskContext, settings: Settings) -> None:
    handle = send_private_status(client, context)

    if not context.query:
        update_private_status(client, context, handle, PROGRESS["empty"])
        return

    try:
        update_private_status(client, context, handle, PROGRESS["search"])
        # Здесь можно разделить search/generate, если ваш RAG отдаёт этапы.
        update_private_status(client, context, handle, PROGRESS["generate"])
        answer = ask_rag(context.query, settings)
        sources = [(s.title, s.url) for s in answer.sources[:5]]
        html = _fit(format_answer_html(answer.text, sources))
        update_private_status(client, context, handle, html, parse_mode="HTML")
    except Exception:
        log.exception("ask failed chat=%s user=%s", context.chat_id, context.user_id)
        update_private_status(
            client,
            context,
            handle,
            "Не удалось получить ответ из базы. Попробуйте ещё раз чуть позже.",
        )
