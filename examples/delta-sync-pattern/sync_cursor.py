"""Pattern 2 — cursor-based change feed (`changes.list`).

Returns deletes. Idempotent (replaying a token gives the same events). Cheap
(only changes since `pageToken`). Still polled, so latency = poll interval.

The default pattern when the provider has a change feed — and most do.

First run gets a starting `pageToken` from `getStartPageToken()` and persists
it. Subsequent runs read it back, fetch changes, and persist the new
`newStartPageToken`. Lose the token and you have to do a full reconcile from
scratch — see `sync_poll.py`.

Usage:
    python sync_cursor.py                  # one tick, then exit
    python sync_cursor.py --interval 30    # tick every 30 seconds
"""
from __future__ import annotations

import argparse
import time

from drive_connector import DOC_MIME, DriveConnector, change_to_document
from sinks import Sink, StdoutSink
from state import JSONFileState

PAGE_TOKEN_KEY = "page_token"


def tick(conn: DriveConnector, sink: Sink, state: JSONFileState) -> None:
    token = state.get(PAGE_TOKEN_KEY)
    if token is None:
        token = conn.get_start_page_token()
        state.put(PAGE_TOKEN_KEY, token)
        print(f"[cursor] no token — starting from {token} (no events before this)")
        return

    changes, new_token = conn.list_changes(token)
    n_up = n_del = 0
    for change in changes:
        f = change.get("file") or {}
        if change.get("removed") or f.get("trashed"):
            sink.delete(f"drive:{change['fileId']}")
            n_del += 1
            continue
        if f.get("mimeType") != DOC_MIME:
            continue  # ignore non-Doc edits in this demo (sheets, slides, etc).
        sink.upsert(change_to_document(f))
        n_up += 1
    state.put(PAGE_TOKEN_KEY, new_token)
    print(f"[cursor] {n_up} upsert(s), {n_del} delete(s); next token persisted")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--interval", type=float, default=0,
                   help="seconds between ticks (0 = run once and exit)")
    args = p.parse_args()

    conn = DriveConnector()
    sink = StdoutSink()
    state = JSONFileState()

    while True:
        tick(conn, sink, state)
        if args.interval <= 0:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
