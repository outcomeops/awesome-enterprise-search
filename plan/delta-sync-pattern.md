# Plan: `examples/delta-sync-pattern/`

The third runnable example. Goal: show the three real ways to keep a search index in sync with a source system after the initial backfill, and which to use when.

## Why this example

After the initial backfill, the question is no longer "how do I get all the docs" — it's "how do I make sure the index reflects the source within N seconds, including deletes, without re-indexing everything every time." Most RAG tutorials brute-force re-index. Real systems use a layered approach. This example shows the layers.

## Provider choice: Google Drive

Drive has all three sync patterns natively, which is rare. That makes it the cleanest single-provider demo:

| Pattern | Drive primitive |
| --- | --- |
| Poll by timestamp | `files.list?q=modifiedTime > 'YYYY-MM-DDTHH:MM:SS'` |
| Cursor / change feed | `changes.list?pageToken=<token>` (returns adds, edits, **deletes**) |
| Push webhooks | `changes.watch` opens a notification channel to a public callback URL |

Reusing Drive also lets this example **plug into the index already built by `permission-aware-search/`** — the user has the OAuth setup from #1. The example becomes the narrative bridge between #1 (initial backfill) and #2 (OAuth blueprint pattern that this fits into).

## What to build

```
examples/delta-sync-pattern/
  README.md
  requirements.txt
  .env.example
  .gitignore
  drive_connector.py   # DriveConnector(Connector), reusing the blueprint ABC from #2
  sync_poll.py         # pattern 1: timestamp polling, demonstrates the deletes blind spot
  sync_cursor.py       # pattern 2: changes.list with persisted pageToken
  sync_webhook.py      # pattern 3: changes.watch + Flask receiver
  sync_layered.py      # the recommended composition: webhook + periodic cursor reconcile
  state.py             # tiny JSON store for "last seen" timestamp / pageToken / channel ID
```

## The three patterns, briefly

### 1. Poll by `since` timestamp

```python
files.list(
    q=f"modifiedTime > '{last_sync_iso}' and mimeType='application/vnd.google-apps.document'",
    fields="files(id, name, modifiedTime)",
)
```

- Pros: trivial. Works on any provider with a sortable `updated_at`.
- Cons: **does not return deletes.** A doc deleted between polls vanishes from the source but stays in the index forever. Also: clock skew between client and server can cause silent skips at boundary.
- Where it's right: read-only sources where deletes are rare and high latency is OK.

### 2. Cursor-based change feed (`changes.list`)

```python
# initial: get a starting cursor
start = drive.changes().getStartPageToken().execute()["startPageToken"]
state.put("page_token", start)

# every poll cycle:
token = state.get("page_token")
resp = drive.changes().list(pageToken=token, includeRemoved=True).execute()
for change in resp["changes"]:
    if change["removed"]:
        index.delete(change["fileId"])
    else:
        index.upsert(change["file"])
state.put("page_token", resp["newStartPageToken"])
```

- Pros: returns deletes. Idempotent (re-replaying a token gives the same events). Cheap (only changes since `pageToken`).
- Cons: still polled — latency = poll interval. `pageToken` must be persisted across restarts; losing it forces a full reconcile.
- Where it's right: the default pattern. If your provider has a change feed, use it.

### 3. Push webhooks (`changes.watch`)

```python
channel = drive.changes().watch(
    pageToken=token,
    body={
        "id": str(uuid.uuid4()),
        "type": "web_hook",
        "address": webhook_callback_url,
        "token": webhook_secret,           # echoed back, used to verify
        "expiration": ms_since_epoch + 7 * 86400 * 1000,  # max 7 days
    },
).execute()
state.put("channel", {"id": channel["id"], "resource_id": channel["resourceId"], "expires": channel["expiration"]})
```

The receiver gets a thin notification (no payload — just "something changed for this channel"). It then calls `changes.list` with the persisted `pageToken` to fetch what changed.

- Pros: sub-second latency.
- Cons: requires a public HTTPS endpoint, signature/token verification, and a re-subscription job (Drive channels expire in 7 days). Webhook deliveries are best-effort — providers retry but eventually give up.
- Where it's right: when staleness above ~30s is unacceptable.

### 4. The recommended composition (`sync_layered.py`)

- **Webhook receiver** dispatches to a worker that calls `changes.list` with the saved `pageToken`. This is the low-latency path.
- **Periodic cron** (every ~10 min) calls `changes.list` directly with the same `pageToken`. This is the safety net — it catches anything the webhook missed.
- **Channel re-subscription** runs daily, well before the 7-day expiry.
- Both paths read and update the same `pageToken` in `state.py`, so they're idempotent and serializable.

This is the pattern real connectors run in production. Layered, not picked.

## Connection to the other examples

- Reuses the `Connector` ABC and `Token`/`OAuthClient`/`webhook.verify_*` machinery from **#2 oauth-connector-blueprint**. Imports those directly to demonstrate the blueprint actually being used.
- The DriveConnector emits `Document` objects with `acl_principals` populated (same encoding as **#1 permission-aware-search**) so the synced output can drop straight into the same S3 Vectors index.

This is what makes the trilogy coherent: #1 builds an index, #2 abstracts the connector pattern, #3 keeps the index fresh using both.

## Open questions / decisions to make at write time

1. **Cross-folder imports.** Should `delta-sync-pattern/` import from `oauth-connector-blueprint/` (sibling folder), or copy the `Connector` ABC inline? Sibling import is cleaner narratively but awkward in Python (need `sys.path` shim or a top-level package). Likely answer: copy `connector.py` inline and add a one-liner in the README pointing readers to #2. The duplication is ~50 lines and removes a real footgun.
2. **Where deltas land.** Easiest demo: print to stdout. Most useful demo: push into the same S3 Vectors index from #1 so re-running #1's `search.py` reflects the changes. Tradeoff: the latter requires #1 to be set up (extra prereq for the user) but makes the example *visibly* end-to-end. Recommend: optional — accept `--sink stdout|s3vectors`, default `stdout`.
3. **Webhook receiver server.** Reuse `oauth-connector-blueprint/serve.py` shape (Flask) for consistency, or go async (FastAPI/uvicorn) since webhook receivers are I/O-bound? Recommend: stay with Flask. Consistency over micro-performance for a teaching example.
4. **State store.** Same JSON-file pattern as `tokens.py` from #2, or add a SQLite version to show graduation? Recommend: JSON file. Same production-gaps callout. SQLite belongs in a separate "production-grade state" example if at all.

## Production gaps to call out in the README

- Webhook delivery is best-effort. Without the periodic cursor reconcile, you *will* drift.
- `pageToken` loss = full reconcile. Persist it transactionally with whatever index work you do, or you'll double-process.
- Drive channels expire in 7 days; calendar a renewal at ~6 days. Re-issuing a channel mid-life is fine.
- This example processes one channel for one user. Multi-tenant means one channel per (tenant, user, drive) — and a routing table from `channel_id` → tenant.
- No back-pressure: a high-edit document can flood the receiver. Real systems debounce per-document (e.g., coalesce changes to the same `fileId` within a 30-second window).
- This example doesn't show the **initial backfill ↔ delta handoff**. The clean pattern: start the channel *before* the backfill, queue webhook deliveries during backfill, drain the queue once backfill finishes. Otherwise edits made during the backfill window are lost.

## Estimated size

~400 LOC across 5 Python files. Largest single file ≤120 lines.

## After this example

Two left: `multi-tenant-isolation/` and `hybrid-search-scoring/`. Neither depends on this one. Either can come next.
