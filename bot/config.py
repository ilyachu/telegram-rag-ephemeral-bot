from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    bot_username: str
    allowed_chat_ids: frozenset[int]
    rag_http_url: str | None = None
    rag_http_token: str | None = None
    rag_http_timeout_sec: float = 60.0


def _parse_chat_ids(raw: str) -> frozenset[int]:
    values: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        values.append(int(part))
    return frozenset(values)


def load_settings() -> Settings:
    load_dotenv()
    token = (os.getenv("BOT_TOKEN") or "").strip()
    username = (os.getenv("BOT_USERNAME") or "").strip().lstrip("@").lower()
    allowed_raw = (os.getenv("ALLOWED_CHAT_IDS") or "").strip()
    if not token or token.endswith("REPLACE_ME"):
        raise RuntimeError("Set BOT_TOKEN in .env (see .env.example)")
    if not username:
        raise RuntimeError("Set BOT_USERNAME in .env")
    if not allowed_raw:
        raise RuntimeError("Set ALLOWED_CHAT_IDS in .env")

    timeout_raw = (os.getenv("RAG_HTTP_TIMEOUT_SEC") or "60").strip()
    return Settings(
        bot_token=token,
        bot_username=username,
        allowed_chat_ids=_parse_chat_ids(allowed_raw),
        rag_http_url=(os.getenv("RAG_HTTP_URL") or "").strip() or None,
        rag_http_token=(os.getenv("RAG_HTTP_TOKEN") or "").strip() or None,
        rag_http_timeout_sec=float(timeout_raw),
    )
