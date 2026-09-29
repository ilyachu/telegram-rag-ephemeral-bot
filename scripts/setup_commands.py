#!/usr/bin/env python3
"""Register /ask as an ephemeral bot command for allowlisted chats."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot.config import load_settings  # noqa: E402
from bot.telegram_api import TelegramClient  # noqa: E402


def main() -> int:
    settings = load_settings()
    client = TelegramClient(settings.bot_token)

    # Global fallback (visible command list in private chats with the bot).
    client.set_my_commands(
        {
            "commands": [
                {"command": "ask", "description": "Спросить базу знаний"},
                {"command": "start", "description": "Открыть личку с ботом"},
            ]
        }
    )

    # Per-chat ephemeral /ask — вопрос из меню команд скрыт от остальных.
    # Поле ephemeral / scopes зависят от актуальной версии Bot API;
    # если ваш клиент Bot API ещё без ephemeral commands, команда всё равно
    # зарегистрируется как обычная /ask в чате.
    for chat_id in sorted(settings.allowed_chat_ids):
        payload = {
            "commands": [
                {
                    "command": "ask",
                    "description": "Спросить базу (ответ только вам)",
                }
            ],
            "scope": {"type": "chat", "chat_id": chat_id},
        }
        # Best-effort ephemeral flag for Bot API builds that support it.
        payload["commands"][0]["ephemeral"] = True  # type: ignore[index]
        try:
            client.set_my_commands(payload)
            print(f"ok chat={chat_id}")
        except Exception as error:
            # Retry without ephemeral flag for older API surfaces.
            del payload["commands"][0]["ephemeral"]  # type: ignore[index]
            client.set_my_commands(payload)
            print(f"ok chat={chat_id} (without ephemeral flag: {error})")

    client.close()
    print("Done. Add the bot to the group, make it admin, users should /start in DM.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
