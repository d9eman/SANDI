from __future__ import annotations

from abc import ABC, abstractmethod


class NotificationService(ABC):
    @abstractmethod
    def send(self, channel: str, recipient: str, message: str) -> None: ...


class SecureObjectStore(ABC):
    @abstractmethod
    def put(self, plaintext: bytes) -> str: ...

    @abstractmethod
    def get(self, object_ref: str) -> bytes: ...

    @abstractmethod
    def delete(self, object_ref: str) -> None: ...
