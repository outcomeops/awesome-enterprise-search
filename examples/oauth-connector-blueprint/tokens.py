"""Token persistence — a Protocol so the storage backend is swappable.

This file provides a JSON-file implementation that's fine for a demo and
trivially replaceable with Redis/Postgres/Secrets-Manager in production.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class Token:
    access_token: str
    refresh_token: str | None = None
    expires_at: float | None = None  # unix epoch seconds
    raw: dict = field(default_factory=dict)

    def is_expired(self, leeway_seconds: int = 60) -> bool:
        if self.expires_at is None:
            return False
        return time.time() >= (self.expires_at - leeway_seconds)


class TokenStore(Protocol):
    def get(self, key: str) -> Token | None: ...
    def put(self, key: str, token: Token) -> None: ...
    def delete(self, key: str) -> None: ...


class JSONFileTokenStore:
    """One JSON file per process. File mode 0600 so other users on the host
    can't read tokens. Not safe for concurrent writers."""

    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path)

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text())

    def _write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2))
        os.chmod(self.path, 0o600)

    def get(self, key: str) -> Token | None:
        data = self._read().get(key)
        return Token(**data) if data else None

    def put(self, key: str, token: Token) -> None:
        data = self._read()
        data[key] = asdict(token)
        self._write(data)

    def delete(self, key: str) -> None:
        data = self._read()
        data.pop(key, None)
        self._write(data)
