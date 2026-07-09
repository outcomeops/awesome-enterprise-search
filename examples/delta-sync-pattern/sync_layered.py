"""The recommended composition — webhook + reconcile + renewal.

Three paths sharing one `pageToken`:

  1. `/webhook` — fired by Drive on changes. Low-latency.
  2. `reconcile_loop` — every RECONCILE_INTERVAL_SECONDS, drains anyway. The
     safety net for webhook deliveries Drive dropped.
  3. `renewal_loop` — checks hourly; when the channel has <24h to live, opens
     a new one (capturing a fresh starting token *before* stopping the old).

All three call the same `drain_changes` under a lock so concurrent webhook +
reconcile drains can't double-process or skip events. Replaying the same
`pageToken` is idempotent on Drive's side, so duplicate calls are safe — but
the lock keeps the on-disk state file consistent.

Run: flask --app sync_layered run --port 8000
The reconcile + renewal threads start with the Flask app.
"""
from __future__ import annotations

import os
import threading
import time

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from drive_connector import DOC_MIME, DriveConnector, change_to_document
from sinks import StdoutSink
from state import JSONFileState

load_dotenv()

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
WEBHOOK_CALLBACK_URL = os.environ["WEBHOOK_CALLBACK_URL"]
RECONCILE_INTERVAL = int(os.environ.get("RECONCILE_INTERVAL_SECONDS", "600"))
RENEWAL_LEAD_SECONDS = 24 * 60 * 60  # renew when <24h left.

state = JSONFileState()
sink = StdoutSink()
conn = DriveConnector()
state_lock = threading.Lock()


def drain_changes(label: str) -> None:
    with state_lock:
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
        app.logger.info("[%s] %d upsert(s), %d delete(s)", label, n_up, n_del)


def reconcile_loop() -> None:
    while True:
        time.sleep(RECONCILE_INTERVAL)
        try:
            drain_changes("reconcile")
        except Exception:
            app.logger.exception("reconcile failed")


def renewal_loop() -> None:
    while True:
        time.sleep(60 * 60)  # check hourly.
        try:
            ch = state.get("channel") or {}
            if not ch:
                continue
            ms_left = ch.get("expiration", 0) - int(time.time() * 1000)
            if ms_left > RENEWAL_LEAD_SECONDS * 1000:
                continue
            app.logger.info("renewing channel (%d ms left)", ms_left)
            new = conn.start_channel(WEBHOOK_CALLBACK_URL, WEBHOOK_SECRET)
            try:
                conn.stop_channel(ch["channel_id"], ch["resource_id"])
            except Exception:
                # If stop fails the old channel will expire on its own; the
                # new one is already live, so this isn't fatal.
                app.logger.exception("stop_channel failed")
            state.put("channel", new)
            # Don't overwrite page_token — we already have a more recent one.
        except Exception:
            app.logger.exception("renewal failed")


@app.post("/webhook")
def webhook():
    if request.headers.get("X-Goog-Channel-Token", "") != WEBHOOK_SECRET:
        return "bad token", 401
    if request.headers.get("X-Goog-Resource-State") == "sync":
        return jsonify(ok=True)
    drain_changes("webhook")
    return jsonify(ok=True)


@app.post("/channel/start")
def channel_start():
    info = conn.start_channel(WEBHOOK_CALLBACK_URL, WEBHOOK_SECRET)
    state.put("channel", info)
    state.put("page_token", info["page_token"])
    return jsonify(info)


# Flask's auto-reloader runs the module twice; only start threads in the
# worker child (or once when the reloader is disabled).
if not os.environ.get("FLASK_DEBUG") or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    threading.Thread(target=reconcile_loop, daemon=True, name="reconcile").start()
    threading.Thread(target=renewal_loop, daemon=True, name="renewal").start()
