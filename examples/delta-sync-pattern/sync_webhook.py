"""Pattern 3 — push webhooks (`changes.watch`).

Drive opens a notification channel pointed at our public callback URL. When
something changes, Drive POSTs a thin notification (no payload — just "this
channel had activity") to /webhook. We verify it came from our channel by
comparing the `X-Goog-Channel-Token` header against our shared secret, then
call `changes.list` with the persisted `pageToken` to fetch what actually
changed.

Requires:
  - A public HTTPS endpoint. Use `ngrok http 8000` during dev.
  - The callback domain must be verified in Google Cloud Console (Domain
    Verification under "APIs & Services > Domain verification") before Drive
    will accept the watch call.

Channels expire in 7 days — re-issue before then. `sync_layered.py` is the
version that runs the renewal job.

Routes:
    POST /webhook        — receive Drive notifications
    POST /channel/start  — open a new channel and persist its bookkeeping
    POST /channel/stop   — close the current channel

Run: flask --app sync_webhook run --port 8000
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from drive_connector import DOC_MIME, DriveConnector, change_to_document
from sinks import StdoutSink
from state import JSONFileState

load_dotenv()

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
WEBHOOK_CALLBACK_URL = os.environ["WEBHOOK_CALLBACK_URL"]

state = JSONFileState()
sink = StdoutSink()
conn = DriveConnector()


def drain_changes() -> tuple[int, int]:
    token = state.get("page_token") or conn.get_start_page_token()
    changes, new_token = conn.list_changes(token)
    n_up = n_del = 0
    for change in changes:
        f = change.get("file") or {}
        if change.get("removed") or f.get("trashed"):
            sink.delete(f"drive:{change['fileId']}")
            n_del += 1
            continue
        if f.get("mimeType") != DOC_MIME:
            continue
        sink.upsert(change_to_document(f))
        n_up += 1
    state.put("page_token", new_token)
    return n_up, n_del


@app.post("/webhook")
def webhook():
    # Drive's only authentication is the channel token we set on watch().
    # Constant-time compare isn't strictly necessary (this isn't an HMAC), but
    # treat it as a shared secret either way.
    if request.headers.get("X-Goog-Channel-Token", "") != WEBHOOK_SECRET:
        return "bad token", 401
    if request.headers.get("X-Goog-Resource-State") == "sync":
        # One-shot ping when the channel opens. Nothing to drain yet.
        return jsonify(ok=True)
    n_up, n_del = drain_changes()
    app.logger.info("webhook drain: %d upsert(s), %d delete(s)", n_up, n_del)
    return jsonify(ok=True, upserts=n_up, deletes=n_del)


@app.post("/channel/start")
def channel_start():
    info = conn.start_channel(WEBHOOK_CALLBACK_URL, WEBHOOK_SECRET)
    state.put("channel", info)
    state.put("page_token", info["page_token"])
    return jsonify(info)


@app.post("/channel/stop")
def channel_stop():
    ch = state.get("channel")
    if not ch:
        return jsonify(ok=False, reason="no channel"), 404
    conn.stop_channel(ch["channel_id"], ch["resource_id"])
    state.delete("channel")
    return jsonify(ok=True)
