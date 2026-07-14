"""Optional non-blocking Telegram notifications."""

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx

TelegramSender = Callable[[str, str, str], Awaitable[None]]
EventLogger = Callable[[dict[str, object]], None]


async def _default_sender(token: str, chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={"chat_id": chat_id, "text": message},
            timeout=5,
        )
        response.raise_for_status()


def _default_logger(event: dict[str, object]) -> None:
    print(json.dumps(event, separators=(",", ":"), sort_keys=True), flush=True)


@dataclass(frozen=True)
class TelegramNotifier:
    """Schedule Telegram calls without awaiting them in the recovery pipeline."""

    token: str | None = None
    chat_id: str | None = None
    sender: TelegramSender = _default_sender
    logger: EventLogger = _default_logger

    @classmethod
    def from_env(cls) -> "TelegramNotifier":
        return cls(
            token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
            chat_id=os.getenv("TELEGRAM_CHAT_ID") or None,
        )

    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    async def _send_safely(self, message: str) -> None:
        if self.token is None or self.chat_id is None:
            return
        try:
            await self.sender(self.token, self.chat_id, message)
        except Exception as exc:  # Telegram must never affect recovery.
            self.logger(
                {
                    "event_type": "notification_failed",
                    "level": "WARNING",
                    "message": "Telegram notification failed",
                    "error_type": type(exc).__name__,
                }
            )

    def send_async(self, message: str) -> asyncio.Task[None] | None:
        """Schedule a configured notification and return immediately."""

        if not self.is_configured():
            return None
        return asyncio.create_task(self._send_safely(message))
