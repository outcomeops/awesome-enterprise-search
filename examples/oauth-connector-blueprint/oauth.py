"""Provider-agnostic OAuth 2.0 authorization-code client with PKCE.

You construct one OAuthClient per provider by passing its endpoints. The class
knows nothing about which provider it's talking to — it just executes the
spec'd flow. Refresh is included for providers that issue short-lived tokens
(GitHub Apps, Google, Notion); it's a no-op when refresh_token is absent
(GitHub OAuth Apps, classic Slack tokens, etc).
"""
from __future__ import annotations

import base64
import hashlib
import secrets
import time
import urllib.parse
from dataclasses import dataclass

import requests

from tokens import Token


@dataclass(frozen=True)
class OAuthConfig:
    authorize_url: str
    token_url: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]
    use_pkce: bool = True
    # Most providers want scopes space-separated; a few (GitHub) want commas.
    scope_separator: str = " "


class OAuthClient:
    def __init__(self, config: OAuthConfig):
        self.cfg = config

    def begin(self, state: str) -> tuple[str, str | None]:
        """Build the authorize URL the user opens in their browser. Returns
        (auth_url, code_verifier). Stash the verifier in the user's session and
        replay it in `exchange_code`."""
        params = {
            "response_type": "code",
            "client_id": self.cfg.client_id,
            "redirect_uri": self.cfg.redirect_uri,
            "scope": self.cfg.scope_separator.join(self.cfg.scopes),
            "state": state,
        }
        verifier: str | None = None
        if self.cfg.use_pkce:
            verifier = _b64url(secrets.token_bytes(32))
            challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
            params["code_challenge"] = challenge
            params["code_challenge_method"] = "S256"
        return f"{self.cfg.authorize_url}?{urllib.parse.urlencode(params)}", verifier

    def exchange_code(self, code: str, code_verifier: str | None = None) -> Token:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.cfg.redirect_uri,
            "client_id": self.cfg.client_id,
            "client_secret": self.cfg.client_secret,
        }
        if self.cfg.use_pkce:
            if not code_verifier:
                raise ValueError("PKCE enabled but no code_verifier supplied")
            data["code_verifier"] = code_verifier
        return self._post_token(data)

    def refresh(self, refresh_token: str) -> Token:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.cfg.client_id,
            "client_secret": self.cfg.client_secret,
        }
        return self._post_token(data)

    def _post_token(self, data: dict) -> Token:
        # Accept-JSON is needed for GitHub (which otherwise returns form-encoded).
        r = requests.post(
            self.cfg.token_url,
            data=data,
            headers={"Accept": "application/json"},
            timeout=15,
        )
        r.raise_for_status()
        body = r.json()
        if "error" in body:
            raise RuntimeError(f"OAuth error: {body}")
        expires_at = (
            time.time() + int(body["expires_in"]) if "expires_in" in body else None
        )
        return Token(
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token"),
            expires_at=expires_at,
            raw=body,
        )


def authorized_token(
    client: OAuthClient, store, key: str
) -> Token:
    """Load a token from the store, refreshing if expired. Raises if no token
    is present (caller should redirect to /oauth/start)."""
    tok = store.get(key)
    if tok is None:
        raise LookupError(f"no token for {key} — start the OAuth flow first")
    if tok.is_expired() and tok.refresh_token:
        tok = client.refresh(tok.refresh_token)
        store.put(key, tok)
    return tok


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")
