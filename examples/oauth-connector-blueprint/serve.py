"""Tiny Flask app that wires the blueprint together end-to-end.

Three routes:
  GET  /oauth/start    — start the authorize-code flow, redirect to GitHub
  GET  /oauth/callback — finish the flow, persist the token
  POST /webhook        — receive change-notifications, verify signature

Run: `flask --app serve run --port 8000`
For webhook delivery in development: `ngrok http 8000` and use the public URL
as OAUTH_REDIRECT_URI / WEBHOOK_CALLBACK_URL in your GitHub OAuth App and hook.
"""
from __future__ import annotations

import os
import secrets

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, session

from github import GitHubConnector, github_oauth_client
from oauth import authorized_token
from tokens import JSONFileTokenStore
from webhook import verify_github_signature

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
TOKEN_KEY = "github"
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

store = JSONFileTokenStore("./tokens.json")
oauth = github_oauth_client()


@app.get("/oauth/start")
def oauth_start():
    state = secrets.token_urlsafe(16)
    auth_url, verifier = oauth.begin(state)
    session["oauth_state"] = state
    session["pkce_verifier"] = verifier
    return redirect(auth_url)


@app.get("/oauth/callback")
def oauth_callback():
    if request.args.get("state") != session.pop("oauth_state", None):
        return "bad state", 400
    code = request.args.get("code")
    if not code:
        return f"oauth error: {request.args.get('error', 'no code')}", 400
    token = oauth.exchange_code(code, code_verifier=session.pop("pkce_verifier", None))
    store.put(TOKEN_KEY, token)
    return "authorized — you can close this tab."


@app.post("/webhook")
def webhook():
    sig = request.headers.get("X-Hub-Signature-256", "")
    if not verify_github_signature(WEBHOOK_SECRET, request.get_data(), sig):
        return "bad signature", 401
    event = request.headers.get("X-GitHub-Event", "unknown")
    payload = request.get_json(silent=True) or {}
    # In a real connector, dispatch to your delta-sync worker here.
    app.logger.info("received %s for %s", event, payload.get("repository", {}).get("full_name"))
    return jsonify(ok=True)


@app.get("/whoami")
def whoami():
    """Sanity check: list issues from a repo to confirm the OAuth+connector path works."""
    owner = request.args.get("owner")
    repo = request.args.get("repo")
    if not (owner and repo):
        return "pass ?owner=...&repo=...", 400
    token = authorized_token(oauth, store, TOKEN_KEY)
    conn = GitHubConnector(token, owner, repo)
    docs = []
    for d in conn.iter_documents():
        docs.append({"id": d.id, "title": d.title, "url": d.url})
        if len(docs) >= 5:
            break
    return jsonify(docs)
