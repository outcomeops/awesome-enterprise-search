# OAuth connector blueprint

A provider-agnostic template for the four things every enterprise-search connector has to do:

1. **Authenticate** the user via OAuth 2.0 authorization code flow (with PKCE).
2. **Persist and refresh** tokens.
3. **List, fetch, and read permissions** on documents in a uniform `Document`/`principal` shape, so the search layer downstream is the same regardless of provider.
4. **Subscribe to change notifications** via webhooks, with signature verification on every delivery.

The blueprint files (`oauth.py`, `tokens.py`, `webhook.py`, `connector.py`) know nothing about any specific provider. `github.py` is a ~110-line concrete implementation against GitHub that you read alongside them — it shows what's actually involved in plugging a provider in. To add Confluence, Notion, Slack, Box, etc., copy `github.py` and replace the URLs and parsing.

## Why this is here

Most public OAuth tutorials show you one provider end-to-end and leave you to generalize. Most "build your own RAG" tutorials skip OAuth entirely. This template fills that gap: a runnable, single-folder pattern you can fork once per provider.

## Files

| File | What it does |
| --- | --- |
| `connector.py` | The `Connector` ABC and `Document` / `WebhookSubscription` dataclasses. The contract every provider implements. |
| `oauth.py` | Provider-agnostic `OAuthClient`. PKCE on by default, refresh-aware (no-op when the provider doesn't issue refresh tokens). |
| `tokens.py` | `Token` dataclass, `TokenStore` `Protocol`, and a `JSONFileTokenStore` for demos. Replace the store class with Redis/Postgres/Secrets-Manager in production. |
| `webhook.py` | HMAC-SHA256 verification primitive plus thin helpers for GitHub and Slack signature conventions. |
| `github.py` | The demonstration provider. ~110 lines that map the four interface methods onto GitHub's REST API. |
| `serve.py` | A minimal Flask app: `/oauth/start`, `/oauth/callback`, `/webhook`, plus a `/whoami` sanity check that lists 5 issues from a repo of your choice. |

## Setup

```bash
cd examples/oauth-connector-blueprint
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill it in
```

Create a GitHub OAuth App at <https://github.com/settings/developers>:

- Application name: anything
- Homepage URL: `http://localhost:8000` (or your ngrok URL)
- Authorization callback URL: must match `OAUTH_REDIRECT_URI` in `.env`

Copy the Client ID and a generated Client Secret into `.env`. Generate `WEBHOOK_SECRET` and `FLASK_SECRET_KEY` with `python -c 'import secrets; print(secrets.token_hex(32))'`.

For webhooks during local dev, run `ngrok http 8000` and use the public HTTPS URL as both `OAUTH_REDIRECT_URI` (with `/oauth/callback`) and `WEBHOOK_CALLBACK_URL` (with `/webhook`).

## Run

```bash
flask --app serve run --port 8000
```

1. Visit <http://localhost:8000/oauth/start> — finishes at GitHub, you get redirected back, token is written to `tokens.json`.
2. Visit `http://localhost:8000/whoami?owner=<you>&repo=<your-repo>` — should return five issues as JSON. This proves OAuth → token store → connector → API call all work.
3. To register a webhook against a repo:

   ```python
   # in a Python REPL with the .env loaded
   from github import GitHubConnector, github_oauth_client
   from oauth import authorized_token
   from tokens import JSONFileTokenStore
   import os

   token = authorized_token(github_oauth_client(), JSONFileTokenStore("./tokens.json"), "github")
   conn = GitHubConnector(token, "owner", "repo")
   sub = conn.register_webhook(
       callback_url=os.environ["WEBHOOK_CALLBACK_URL"],
       secret=os.environ["WEBHOOK_SECRET"],
       events=["issues", "issue_comment"],
   )
   print(sub.id)  # save this if you want to delete the hook later
   ```

   Then create or comment on an issue in that repo. Watch the Flask log for the verified webhook delivery.

## Forking this for another provider

Copy `github.py` to `<provider>.py` and:

1. Replace the OAuth endpoints in `<provider>_oauth_client()`. If the provider doesn't support PKCE, set `use_pkce=False` in the `OAuthConfig`. If it uses space-separated scopes, drop the `scope_separator=","` override.
2. Implement `iter_documents` against the provider's list/search endpoint. Yield, don't accumulate — connectors get pointed at large workspaces.
3. Implement `fetch_permissions` to return your normalized principal strings. Match the encoding suggested in `connector.py` so the downstream search layer is provider-agnostic.
4. Implement `register_webhook` against the provider's hook registration endpoint. Add a signature-verification helper to `webhook.py` if the provider uses a non-standard format.

That's it. The `OAuthClient`, `TokenStore`, and Flask routes don't change.

## What this looks like in production

This blueprint is intentionally narrow so you can read it end-to-end. Real deployments need to handle several things it skips:

- **Per-tenant token isolation.** This example uses one `TOKEN_KEY = "github"`. Production keys tokens by `(tenant_id, provider, user_id)` and uses an encrypted store.
- **Token encryption at rest.** `JSONFileTokenStore` writes plaintext access tokens. Use Secrets Manager / KMS-encrypted Postgres / Vault in production.
- **Concurrent-safe token storage.** `JSONFileTokenStore` is not safe for two processes writing at once. Use a real database with row-level locking, or a `SETNX`-style check on Redis.
- **Refresh-on-401 retry.** This blueprint refreshes pre-emptively if `expires_at` says the token is stale. A more robust pattern *also* catches 401 responses, refreshes, and retries the original request once — providers' clocks drift and `expires_in` lies sometimes.
- **Rate-limit handling.** Real connectors get rate-limited. Add `Retry-After` handling to a shared HTTP layer.
- **Webhook delivery durability.** Receive the webhook, signature-check it, and write the event to a durable queue *before* doing any work. Provider re-deliveries should be idempotent on your side (key by event ID).
- **State storage for `/oauth/start`.** This example uses Flask's signed-cookie session, which is fine for one user. Multi-user or multi-host needs a server-side session store.
- **Webhook secret rotation.** When you rotate `WEBHOOK_SECRET`, plan a window during which both the old and new secret are accepted, or you'll drop deliveries during the rotation.
- **Backfill vs. incremental.** Webhooks tell you about *future* changes. The first sync still has to fetch everything; that's the next example, `delta-sync-pattern/`.

## License

Same as the parent repo.
