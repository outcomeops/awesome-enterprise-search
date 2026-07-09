# Delta sync pattern

After the initial backfill, the question is no longer "how do I get all the docs" — it's "how do I make sure the index reflects the source within N seconds, **including deletes**, without re-indexing everything every time."

Most RAG tutorials skip this. They re-embed the world on a cron and call it sync. Real connectors run a layered approach. This example shows the three layers, and what each one is wrong at.

It uses **Google Drive** because Drive has all three sync primitives natively, which is rare. The same pattern shape applies to any provider with a change feed (Confluence, Notion, GitHub, Box, …).

## The three patterns, in one table

| Pattern | Drive primitive | Returns deletes? | Latency | When to use |
| --- | --- | --- | --- | --- |
| Poll by `since` timestamp | `files.list?q=modifiedTime > '...'` | **No** | poll interval | Read-only sources where deletes are rare and high latency is OK. |
| Cursor change feed | `changes.list?pageToken=...` | Yes | poll interval | The default. If your provider has a change feed, use it. |
| Push webhooks | `changes.watch` | Yes (via cursor) | sub-second | When staleness above ~30s is unacceptable. |

You don't pick one. You compose them — see `sync_layered.py`.

## Files

| File | What it does |
| --- | --- |
| `connector.py` | The `Connector` ABC + `Document` / `WebhookSubscription` dataclasses. Copied verbatim from [`oauth-connector-blueprint/`](../oauth-connector-blueprint) so this folder stands alone. |
| `drive_connector.py` | `DriveConnector(Connector)` plus the two Drive-specific helpers the cursor + webhook patterns need: `get_start_page_token()` and `list_changes(token)`. |
| `state.py` | `JSONFileState` — a tiny JSON store for the high-water timestamp, the `pageToken`, and the open channel's bookkeeping. Same demo-grade pattern as `oauth-connector-blueprint/tokens.py`. |
| `sinks.py` | `Sink` protocol + `StdoutSink`. Where deltas land. Replace with an S3 Vectors / Pinecone / Postgres writer to wire into a real index. |
| `sync_poll.py` | Pattern 1. Demonstrates the deletes blind spot. |
| `sync_cursor.py` | Pattern 2. The default. |
| `sync_webhook.py` | Pattern 3. Flask app with `/webhook`, `/channel/start`, `/channel/stop`. |
| `sync_layered.py` | The recommended composition: webhook + periodic reconcile + daily channel renewal. |

## Setup

```bash
cd examples/delta-sync-pattern
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill it in
```

OAuth re-uses the Desktop OAuth flow from [`permission-aware-search/`](../permission-aware-search). If you ran that example, copy `credentials.json` and `token.json` over and you're done. Otherwise:

1. In Google Cloud Console, enable the **Drive API** and create an **OAuth client ID** of type **Desktop app**. Download as `credentials.json` into this folder.
2. The first run of any sync script will open a browser for consent and write `token.json`.

For the webhook patterns (`sync_webhook.py`, `sync_layered.py`) you also need:

3. A public HTTPS URL. In dev, run `ngrok http 8000`, take the `https://...ngrok.app` URL, and put `https://...ngrok.app/webhook` in `WEBHOOK_CALLBACK_URL`.
4. **Domain verification.** Drive will not accept `changes.watch` calls until the callback domain is verified. In Google Cloud Console: *APIs & Services → Domain verification → Add domain*. ngrok domains can be verified by serving the file Google gives you.

## Run

### Pattern 1 — poll, watch the bug

```bash
python sync_poll.py
# create or edit a Drive doc
python sync_poll.py
# delete a Drive doc
python sync_poll.py    # the delete is invisible — that's the blind spot.
```

### Pattern 2 — cursor

```bash
python sync_cursor.py     # first run captures a starting pageToken; reports nothing
# create / edit / delete docs in Drive
python sync_cursor.py     # reports each, including the delete
python sync_cursor.py --interval 30   # stay running, tick every 30s
```

### Pattern 3 — webhook

```bash
# terminal 1
ngrok http 8000

# terminal 2 — put the ngrok HTTPS URL into .env as WEBHOOK_CALLBACK_URL
flask --app sync_webhook run --port 8000

# terminal 3 — open a notification channel
curl -X POST http://localhost:8000/channel/start
# now edit / delete docs in Drive; watch terminal 2 for "webhook drain: ..."

# when done
curl -X POST http://localhost:8000/channel/stop
```

### Pattern 4 — layered (the recommended one)

```bash
flask --app sync_layered run --port 8000
curl -X POST http://localhost:8000/channel/start
```

Same `/webhook` endpoint as #3, plus two background threads:
- **reconcile** drains every `RECONCILE_INTERVAL_SECONDS` (default 10 min) regardless of whether webhooks fired. This catches anything Drive failed to deliver.
- **renewal** opens a fresh channel when the current one has <24h to live, so the 7-day expiry never lapses unnoticed.

All three drain paths share one `pageToken` under a lock, so they're safe to run concurrently.

## Why "layered, not picked"

- **Webhook delivery is best-effort.** Providers retry, then give up. Without the periodic cursor reconcile, you *will* drift. Set the reconcile interval based on how stale you can tolerate things being if the webhook stops working entirely (e.g., a misconfigured firewall blocks deliveries silently for two hours).
- **`pageToken` loss = full reconcile.** Persist it transactionally with whatever index work you do — write the new token in the same transaction as the index updates it represents — or you'll double-process on a crash.
- **Channels expire.** Drive caps at 7 days; calendar a renewal at ~24h before expiry. Re-issuing mid-life is fine — the old channel still delivers until you stop it.

## What this example skips that production needs

- **Multi-tenant routing.** This processes one channel for one user. Real systems run one channel per `(tenant, user, drive)`, plus a routing table from `channel_id` → tenant in the receiver.
- **Backfill ↔ delta handoff.** Webhooks tell you about *future* changes. The clean pattern: open the channel and start collecting `pageToken`-driven changes *before* the backfill, queue them, drain the queue once backfill finishes. Otherwise edits made during the backfill window are lost.
- **Per-document debounce.** A high-edit doc can flood the receiver. Real systems coalesce changes to the same `fileId` within a short window (e.g., 30s).
- **Body fetch.** `iter_documents` and `change_to_document` here yield metadata only — no doc body. To wire into an index you need to call `files().export()` for each upserted file (see `permission-aware-search/ingest.py:fetch_text`). Cache by `(file_id, modifiedTime)` so re-runs don't re-export unchanged docs.
- **ACLs.** Permissions can change without the file's content changing; Drive emits a change event for that, but you have to call `permissions().list` to see what changed. `DriveConnector.fetch_permissions` is here for that — call it on each upsert if you store ACL metadata.
- **Webhook secret rotation.** Drive notifications are authenticated only by `X-Goog-Channel-Token`. Rotating the secret means opening a new channel under the new secret and stopping the old one — there's no period of dual acceptance.
- **State store.** `JSONFileState` is fine for a single-process demo. Multi-process or multi-host needs a real database with row-level locking.

## How this fits the other examples

- Reuses the `Connector` ABC and the same Drive OAuth flow as **[`oauth-connector-blueprint/`](../oauth-connector-blueprint)** and **[`permission-aware-search/`](../permission-aware-search)**. Documents emitted by `DriveConnector` use the same ID and ACL encoding as `permission-aware-search/ingest.py`, so the upsert/delete events here can drop straight into that S3 Vectors index — replace `StdoutSink` with a sink that calls the embed + `put_vectors` / `delete_vectors` machinery from `s3vectors_client.py`.
- **#1** builds the index. **#2** abstracts the provider. **#3** (this) keeps the index fresh. The trilogy.

## License

Same as the parent repo.
