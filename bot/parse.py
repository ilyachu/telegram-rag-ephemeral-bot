from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MAX_QUERY_LENGTH = 1200


@dataclass(frozen=True)
class AskContext:
    chat_id: int
    user_id: int
    query: str
    ephemeral_message_id: int | None
    message_id: int | None


def _entity_text(text: str, entity: dict[str, Any]) -> str:
    # Telegram entity offset/length are UTF-16 code units.
    encoded = text.encode("utf-16-le")
    start = entity["offset"] * 2
    end = start + entity["length"] * 2
    return encoded[start:end].decode("utf-16-le")


def message_mentions_bot(message: dict[str, Any], bot_username: str) -> bool:
    text = str(message.get("text") or "")
    username = bot_username.lower()
    for entity in message.get("entities") or []:
        etype = entity.get("type")
        if etype == "mention":
            mention = _entity_text(text, entity).lstrip("@").lower()
            if mention == username:
                return True
        if etype == "text_mention":
            user = entity.get("user") or {}
            if user.get("is_bot") and str(user.get("username") or "").lower() == username:
                return True
    return bool(re.search(rf"(^|\s)@{re.escape(username)}\b", text, flags=re.I))


def strip_bot_mentions(text: str, bot_username: str) -> str:
    cleaned = re.sub(rf"@{re.escape(bot_username)}\b", " ", text, flags=re.I)
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_ask_query(message: dict[str, Any], bot_username: str) -> str | None:
    text = str(message.get("text") or "").strip()
    if not text:
        return None

    command = re.match(rf"^/ask(?:@{re.escape(bot_username)})?(?:\s+([\s\S]+))?$", text, flags=re.I)
    if command:
        return (command.group(1) or "").strip()[:MAX_QUERY_LENGTH]

    reply = message.get("reply_to_message") or {}
    reply_from = reply.get("from") or {}
    reply_to_bot = bool(
        reply_from.get("is_bot")
        and str(reply_from.get("username") or "").lstrip("@").lower() == bot_username.lower()
    )
    mentions_bot = message_mentions_bot(message, bot_username)
    if not mentions_bot and not reply_to_bot:
        return None

    without_mention = strip_bot_mentions(text, bot_username)
    if not without_mention:
        return ""

    ask_prefix = re.match(r"^ask(?:@\w+)?(?:\s+|:\s*|[\u2014-]\s*)([\s\S]+)$", without_mention, flags=re.I)
    if ask_prefix:
        return (ask_prefix.group(1) or "").strip()[:MAX_QUERY_LENGTH]

    if re.match(r"^/\w+", without_mention):
        return None
    return without_mention[:MAX_QUERY_LENGTH]


def parse_ask_update(
    update: dict[str, Any],
    *,
    allowed_chat_ids: set[int] | frozenset[int],
    bot_username: str,
) -> AskContext | None:
    message = update.get("message")
    if not isinstance(message, dict):
        return None

    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    chat_id = chat.get("id")
    user_id = sender.get("id")
    chat_type = str(chat.get("type") or "")

    if not isinstance(chat_id, int) or chat_id not in allowed_chat_ids:
        return None
    if not isinstance(user_id, int) or sender.get("is_bot"):
        return None
    if chat_type not in {"group", "supergroup"}:
        return None

    query = extract_ask_query(message, bot_username.lower())
    if query is None:
        return None

    ephemeral_raw = message.get("ephemeral_message_id")
    message_raw = message.get("message_id")
    ephemeral_message_id = ephemeral_raw if isinstance(ephemeral_raw, int) else None
    message_id = message_raw if isinstance(message_raw, int) else None

    return AskContext(
        chat_id=chat_id,
        user_id=user_id,
        query=query,
        ephemeral_message_id=ephemeral_message_id,
        message_id=message_id,
    )
