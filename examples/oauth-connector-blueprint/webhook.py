"""Webhook signature verification.

Most providers sign webhook deliveries with HMAC-SHA256 using a shared secret
you set when registering the hook. The header name and signature format vary,
but the underlying check is the same: HMAC the raw body with the secret and
compare in constant time.

This file gives you the primitive plus thin helpers for the conventions of a
few common providers. Add more as you build more connectors.
"""
from __future__ import annotations

import hashlib
import hmac


def verify_hmac_sha256(secret: bytes, body: bytes, expected_hex: str) -> bool:
    """Constant-time check. `expected_hex` is the hex digest the provider sent."""
    computed = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, expected_hex)


def verify_github_signature(secret: str, body: bytes, header_value: str) -> bool:
    """GitHub: header `X-Hub-Signature-256` is `sha256=<hex>`."""
    if not header_value or not header_value.startswith("sha256="):
        return False
    return verify_hmac_sha256(secret.encode(), body, header_value[len("sha256="):])


def verify_slack_signature(
    signing_secret: str, timestamp: str, body: bytes, header_value: str
) -> bool:
    """Slack: header `X-Slack-Signature` is `v0=<hex>` over `v0:{timestamp}:{body}`."""
    if not header_value or not header_value.startswith("v0="):
        return False
    base = f"v0:{timestamp}:".encode() + body
    return verify_hmac_sha256(signing_secret.encode(), base, header_value[len("v0="):])
