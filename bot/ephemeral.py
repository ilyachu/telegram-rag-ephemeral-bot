from __future__ import annotations

from dataclasses import dataclass

from .parse import AskContext
from .telegram_api import TelegramApiError, TelegramClient

PROGRESS = {
    "accepted": "Принял вопрос…",
    "search": "Ищу в базе…",
    "generate": "Собираю ответ…",
    "empty": "Напишите вопрос после команды: /ask ваш вопрос",
}


@dataclass(frozen=True)
class ProgressHandle:
    """ephemeral — скрытое сообщение в группе; dm — личка как запасной путь."""

    kind: str  # "ephemeral" | "dm"
    id: int


def send_private_status(client: TelegramClient, context: AskContext) -> ProgressHandle:
    """
    Ответ только автору. В группу публично не пишем.

    Правила Telegram (упрощённо):
    - есть ephemeral_message_id у команды (/ask из меню) → скрытый ответ доступен любому боту ~15с;
    - иначе скрытый ответ в группе обычно требует, чтобы бот был администратором;
    - если ephemeral в группе не прошёл — уходим в личку (пользователь должен был /start бота).
    """
    text = PROGRESS["accepted"] if context.query else PROGRESS["empty"]
    payload: dict = {
        "chat_id": context.chat_id,
        "text": text,
        "ephemeral_message_parameters": {"receiver_user_id": context.user_id},
        "link_preview_options": {"is_disabled": True},
    }
    if context.ephemeral_message_id is not None:
        payload["reply_parameters"] = {"ephemeral_message_id": context.ephemeral_message_id}

    try:
        result = client.send_message(payload)
        ephemeral_id = result.get("ephemeral_message_id")
        if isinstance(ephemeral_id, int):
            return ProgressHandle(kind="ephemeral", id=ephemeral_id)
        raise RuntimeError("Telegram did not return ephemeral_message_id")
    except (TelegramApiError, RuntimeError) as error:
        # Меню /ask уже дало ephemeral_message_id — если и оно упало, не маскируем ошибку.
        if context.ephemeral_message_id is not None:
            raise

        dm = client.send_message(
            {
                "chat_id": context.user_id,
                "text": (
                    f"{text}\n\n"
                    "Отвечаю в личке: скрытый ответ в группе доступен, "
                    "если бот — администратор."
                ),
                "link_preview_options": {"is_disabled": True},
            }
        )
        message_id = dm.get("message_id")
        if not isinstance(message_id, int):
            raise RuntimeError(f"Private DM fallback failed after: {error}") from error
        return ProgressHandle(kind="dm", id=message_id)


def update_private_status(
    client: TelegramClient,
    context: AskContext,
    handle: ProgressHandle,
    text: str,
    *,
    parse_mode: str | None = None,
) -> None:
    common: dict = {
        "text": text,
        "link_preview_options": {"is_disabled": True},
    }
    if parse_mode:
        common["parse_mode"] = parse_mode

    if handle.kind == "dm":
        client.edit_message_text(
            {
                "chat_id": context.user_id,
                "message_id": handle.id,
                **common,
            }
        )
        return

    client.edit_ephemeral_message_text(
        {
            "chat_id": context.chat_id,
            "receiver_user_id": context.user_id,
            "ephemeral_message_id": handle.id,
            **common,
        }
    )


def escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def format_answer_html(text: str, sources: list[tuple[str, str | None]]) -> str:
    body = escape_html(text.strip())
    if not sources:
        return body
    lines = [body, "", "<b>Источники</b>"]
    for index, (title, url) in enumerate(sources, start=1):
        label = escape_html(title or f"Источник {index}")
        if url:
            lines.append(f'{index}. <a href="{escape_html(url)}">{label}</a>')
        else:
            lines.append(f"{index}. {label}")
    return "\n".join(lines)
