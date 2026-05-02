"""GitHub as a demonstration provider for the connector blueprint.

Scope of this adapter (intentionally narrow):
  - "Documents" are issues + their bodies (PRs filtered out).
  - "Permissions" are repo collaborators with at least pull access.
  - Webhooks subscribe to issue and issue_comment events.

Read this alongside connector.py to see how a provider plugs into the
blueprint. To add a new provider, copy this file and replace the URL
constants and the parsing in iter_documents / fetch_permissions.
"""
from __future__ import annotations

import os
from typing import Iterator

import requests

from connector import Connector, Document, WebhookSubscription
from oauth import OAuthClient, OAuthConfig
from tokens import Token

API = "https://api.github.com"
ACCEPT = "application/vnd.github+json"


def github_oauth_client() -> OAuthClient:
    return OAuthClient(OAuthConfig(
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        client_id=os.environ["GITHUB_CLIENT_ID"],
        client_secret=os.environ["GITHUB_CLIENT_SECRET"],
        redirect_uri=os.environ["OAUTH_REDIRECT_URI"],
        scopes=["repo", "read:org"],
        scope_separator=",",   # GitHub-specific
    ))


class GitHubConnector(Connector):
    def __init__(self, token: Token, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token.access_token}",
            "Accept": ACCEPT,
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def iter_documents(self, since: str | None = None) -> Iterator[Document]:
        page = 1
        while True:
            params = {"state": "all", "sort": "updated", "direction": "desc",
                      "per_page": 100, "page": page}
            if since:
                params["since"] = since
            r = requests.get(
                f"{API}/repos/{self.owner}/{self.repo}/issues",
                headers=self._headers(), params=params, timeout=15,
            )
            r.raise_for_status()
            issues = r.json()
            if not issues:
                return
            for issue in issues:
                if "pull_request" in issue:  # /issues returns PRs too
                    continue
                yield Document(
                    id=f"github:{self.owner}/{self.repo}#{issue['number']}",
                    title=issue["title"],
                    body=issue.get("body") or "",
                    url=issue["html_url"],
                    updated_at=issue["updated_at"],
                    extra={"number": issue["number"], "state": issue["state"]},
                )
            page += 1

    def fetch_permissions(self, document: Document) -> list[str]:
        # All repo issues share the repo's ACL — same query for every doc, so
        # cache the result if you call this in a tight loop.
        r = requests.get(
            f"{API}/repos/{self.owner}/{self.repo}/collaborators",
            headers=self._headers(),
            params={"affiliation": "all", "per_page": 100},
            timeout=15,
        )
        r.raise_for_status()
        out = []
        for c in r.json():
            if c.get("permissions", {}).get("pull"):
                out.append(f"user:github:{c['login']}")
        # Public repos are readable by anyone; reflect that in the principal set.
        meta = requests.get(
            f"{API}/repos/{self.owner}/{self.repo}",
            headers=self._headers(), timeout=15,
        ).json()
        if not meta.get("private", True):
            out.append("anyone")
        return sorted(set(out))

    def register_webhook(
        self, callback_url: str, secret: str, events: list[str]
    ) -> WebhookSubscription:
        r = requests.post(
            f"{API}/repos/{self.owner}/{self.repo}/hooks",
            headers=self._headers(),
            json={
                "name": "web",
                "active": True,
                "events": events,
                "config": {
                    "url": callback_url,
                    "content_type": "json",
                    "secret": secret,
                    "insecure_ssl": "0",
                },
            },
            timeout=15,
        )
        r.raise_for_status()
        hook = r.json()
        return WebhookSubscription(id=str(hook["id"]), callback_url=callback_url, events=events)
