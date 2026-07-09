"""Tiny JSON state store for the three sync patterns.

Holds whichever of these the active pattern needs:
  - last_sync_iso : high-water timestamp from the polling pattern
  - page_token    : Drive changes-feed cursor (cursor + webhook patterns)
  - channel       : {channel_id, resource_id, expiration, page_token}
                    bookkeeping for an open notification channel

Same plaintext-file pattern as `oauth-connector-blueprint/tokens.py`. Fine for
a demo; replace with a real database (transactional with whatever does the
indexing — see the README) in production.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class JSONFileState:
    def __init__(self, path: str | os.PathLike[str] = "./state.json"):
        self.path = Path(path)

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text())

    def _write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2))
        os.chmod(self.path, 0o600)

    def get(self, key: str, default: Any = None) -> Any:
        return self._read().get(key, default)

    def put(self, key: str, value: Any) -> None:
        data = self._read()
        data[key] = value
        self._write(data)

    def delete(self, key: str) -> None:
        data = self._read()
        data.pop(key, None)
        self._write(data)
