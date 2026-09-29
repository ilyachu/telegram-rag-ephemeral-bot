from __future__ import annotations

from typing import Any

import httpx


class TelegramApiError(RuntimeError):
    def __init__(self, method: str, description: str):
        super().__init__(f"Telegram {method} failed: {description}")
        self.method = method
        self.description = description


class TelegramClient:
    def __init__(self, token: str, timeout: float = 30.0):
        self._base = f"https://api.telegram.org/bot{token}"
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def call(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        response = self._client.post(f"{self._base}/{method}", json=payload or {})
        data = response.json()
        if not data.get("ok"):
            raise TelegramApiError(method, str(data.get("description") or response.status_code))
        return data.get("result")

    def get_updates(self, offset: int, timeout: int = 25) -> list[dict[str, Any]]:
        result = self.call(
            "getUpdates",
            {
                "offset": offset,
                "timeout": timeout,
                "allowed_updates": ["message"],
            },
        )
        return list(result or [])

    def delete_webhook(self, *, drop_pending_updates: bool = False) -> None:
        self.call("deleteWebhook", {"drop_pending_updates": drop_pending_updates})

    def send_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.call("sendMessage", payload)

    def edit_message_text(self, payload: dict[str, Any]) -> Any:
        return self.call("editMessageText", payload)

    def edit_ephemeral_message_text(self, payload: dict[str, Any]) -> Any:
        return self.call("editEphemeralMessageText", payload)

    def set_my_commands(self, payload: dict[str, Any]) -> Any:
        return self.call("setMyCommands", payload)
