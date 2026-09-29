from __future__ import annotations

import logging
import sys
from pathlib import Path

from .config import load_settings
from .handlers import handle_ask
from .parse import parse_ask_update
from .telegram_api import TelegramClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("bot")


def main() -> int:
    settings = load_settings()
    client = TelegramClient(settings.bot_token)
    state_dir = Path("state")
    state_dir.mkdir(exist_ok=True)
    offset_file = state_dir / "offset"

    # Polling and webhook cannot share one bot token.
    client.delete_webhook(drop_pending_updates=False)

    offset = int(offset_file.read_text()) if offset_file.exists() else 0
    log.info(
        "polling as @%s; allowlist=%s",
        settings.bot_username,
        sorted(settings.allowed_chat_ids),
    )

    try:
        while True:
            updates = client.get_updates(offset=offset, timeout=25)
            for update in updates:
                offset = int(update["update_id"]) + 1
                tmp = state_dir / "offset.new"
                tmp.write_text(str(offset))
                tmp.replace(offset_file)

                context = parse_ask_update(
                    update,
                    allowed_chat_ids=settings.allowed_chat_ids,
                    bot_username=settings.bot_username,
                )
                if context is None:
                    continue
                log.info("ask from user=%s chat=%s", context.user_id, context.chat_id)
                handle_ask(client, context, settings)
    except KeyboardInterrupt:
        log.info("stopped")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
