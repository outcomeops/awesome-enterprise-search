"""Pattern 1 — poll by `since` timestamp.

Trivial. Works on any source with a sortable `updated_at` field. **Does not
return deletes**: a doc deleted between polls vanishes from the source but
stays in the index forever. To see the bug: index a doc, run this, delete the
doc in Drive, run this again — the upsert is gone but the index still has it.

Also: clock skew between client and server can cause silent skips at the
boundary. Real systems use `>=` and dedupe by ID; this uses `>` to keep the
loop simple.

Usage:
    python sync_poll.py                   # one tick, then exit
    python sync_poll.py --interval 30     # tick every 30 seconds
"""
from __future__ import annotations

import argparse
import time

from drive_connector import DriveConnector
from sinks import Sink, StdoutSink
from state import JSONFileState

LAST_SYNC_KEY = "last_sync_iso"


def tick(conn: DriveConnector, sink: Sink, state: JSONFileState) -> None:
    since = state.get(LAST_SYNC_KEY)
    print(f"[poll] since={since or '<beginning>'}")
    n = 0
    high_water = since
    for doc in conn.iter_documents(since=since):
        sink.upsert(doc)
        n += 1
        # ISO-8601 with consistent precision sorts lexicographically.
        if high_water is None or doc.updated_at > high_water:
            high_water = doc.updated_at
    if high_water and high_water != since:
        state.put(LAST_SYNC_KEY, high_water)
    print(f"[poll] {n} upsert(s); deletes: not detected (this is the blind spot)")


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
