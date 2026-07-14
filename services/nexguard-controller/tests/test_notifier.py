"""Tests for optional non-blocking Telegram notifications."""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from app.notifier import TelegramNotifier
else:
    package_name = "nexguard_controller_app"
    app_dir = Path(__file__).resolve().parents[1] / "app"
    if package_name not in sys.modules:
        package_spec = importlib.util.spec_from_file_location(
            package_name,
            app_dir / "__init__.py",
            submodule_search_locations=[str(app_dir)],
        )
        if package_spec is None or package_spec.loader is None:
            raise RuntimeError("unable to load controller application package")
        package = importlib.util.module_from_spec(package_spec)
        sys.modules[package_name] = package
        package_spec.loader.exec_module(package)
    notifier_module = importlib.import_module(f"{package_name}.notifier")
    TelegramNotifier = notifier_module.TelegramNotifier


@pytest.mark.asyncio
async def test_notifier_skipped_without_token() -> None:
    calls = 0

    async def sender(_token: str, _chat_id: str, _message: str) -> None:
        nonlocal calls
        calls += 1

    notifier = TelegramNotifier(chat_id="chat", sender=sender)

    assert notifier.send_async("incident") is None
    assert calls == 0


@pytest.mark.asyncio
async def test_notifier_failure_is_non_blocking() -> None:
    events: list[dict[str, object]] = []

    async def failing_sender(_token: str, _chat_id: str, _message: str) -> None:
        raise RuntimeError("network down")

    notifier = TelegramNotifier(
        token="test-token",
        chat_id="test-chat",
        sender=failing_sender,
        logger=events.append,
    )

    task = notifier.send_async("incident")

    assert task is not None
    await task
    assert events[0]["event_type"] == "notification_failed"


@pytest.mark.asyncio
async def test_notifier_schedules_successfully() -> None:
    messages: list[str] = []

    async def sender(_token: str, _chat_id: str, message: str) -> None:
        messages.append(message)

    notifier = TelegramNotifier(token="test-token", chat_id="test-chat", sender=sender)
    task = notifier.send_async("recovered")

    assert task is not None
    await task
    assert messages == ["recovered"]
