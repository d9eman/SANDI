from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.ports.services import NotificationService


class LogNotificationService(NotificationService):
    """Demo notification adapter that appends messages to a local log."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, channel: str, recipient: str, message: str) -> None:
        line = f"{datetime.now(timezone.utc).isoformat()}\t{channel}\t{recipient}\t{message}\n"
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)
