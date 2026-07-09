"""Drive as a delta-sync provider.

Implements the `Connector` ABC plus two Drive-specific helpers the cursor +
webhook patterns need: `get_start_page_token()` and `list_changes(token)`.

Reuses the same Desktop OAuth flow as `permission-aware-search/` so OAuth
boilerplate stays out of the delta-sync code.
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from typing import Iterator

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from connector import Connector, Document, WebhookSubscription

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
DOC_MIME = "application/vnd.google-apps.document"
WATCH_TTL_SECONDS = 7 * 24 * 60 * 60  # Drive caps channels at 7 days.


def drive_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                sys.exit("missing credentials.json — see README setup steps")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def change_to_document(file: dict) -> Document:
    return Document(
        id=f"drive:{file['id']}",
        title=file.get("name", "(untitled)"),
        body="",  # delta-sync example doesn't fetch bodies; downstream does.
        url=file.get("webViewLink", ""),
        updated_at=file.get("modifiedTime", ""),
        extra={"file_id": file["id"]},
    )


class DriveConnector(Connector):
    def __init__(self, svc=None):
        self.svc = svc or drive_service()

    def iter_documents(self, since: str | None = None) -> Iterator[Document]:
        q = f"mimeType='{DOC_MIME}' and trashed=false"
        if since:
            q += f" and modifiedTime > '{since}'"
        page_token = None
        while True:
            resp = self.svc.files().list(
                q=q,
                fields="nextPageToken, files(id, name, modifiedTime, webViewLink)",
                pageSize=100,
                pageToken=page_token,
            ).execute()
            for f in resp.get("files", []):
                yield change_to_document(f)
            page_token = resp.get("nextPageToken")
            if not page_token:
                return

    def fetch_permissions(self, document: Document) -> list[str]:
        # Same encoding as permission-aware-search/ingest.py:encode_principals.
        out: set[str] = set()
        try:
            perms = self.svc.permissions().list(
                fileId=document.extra["file_id"],
                fields="permissions(type, emailAddress, domain)",
            ).execute().get("permissions", [])
        except HttpError:
            return []
        for p in perms:
            t = p.get("type")
            if t in ("user", "group") and p.get("emailAddress"):
                out.add(p["emailAddress"].lower())
            elif t == "domain" and p.get("domain"):
                out.add(f"domain:{p['domain'].lower()}")
            elif t == "anyone":
                out.add("anyone")
        return sorted(out)

    def register_webhook(
        self, callback_url: str, secret: str, events: list[str]
    ) -> WebhookSubscription:
        info = self.start_channel(callback_url, secret)
        return WebhookSubscription(
            id=info["channel_id"], callback_url=callback_url, events=events,
        )

    # --- Drive-specific helpers used by the cursor + webhook patterns. ---

    def get_start_page_token(self) -> str:
        return self.svc.changes().getStartPageToken().execute()["startPageToken"]

    def list_changes(self, page_token: str) -> tuple[list[dict], str]:
        """Drain everything since `page_token`. Returns (changes, new_token)."""
        changes: list[dict] = []
        token = page_token
        while True:
            resp = self.svc.changes().list(
                pageToken=token,
                includeRemoved=True,
                fields=(
                    "nextPageToken, newStartPageToken, "
                    "changes(removed, fileId, "
                    "file(id, name, mimeType, modifiedTime, webViewLink, trashed))"
                ),
            ).execute()
            changes.extend(resp.get("changes", []))
            if "nextPageToken" in resp:
                token = resp["nextPageToken"]
                continue
            return changes, resp["newStartPageToken"]

    def start_channel(self, callback_url: str, secret: str) -> dict:
        """Open a channel + return {channel_id, resource_id, expiration, page_token}.

        page_token is captured *before* watch() so no edits land in the gap.
        """
        page_token = self.get_start_page_token()
        body = {
            "id": str(uuid.uuid4()),
            "type": "web_hook",
            "address": callback_url,
            "token": secret,    # echoed back as X-Goog-Channel-Token, our auth.
            "expiration": int((time.time() + WATCH_TTL_SECONDS) * 1000),
        }
        ch = self.svc.changes().watch(pageToken=page_token, body=body).execute()
        return {
            "channel_id": ch["id"],
            "resource_id": ch["resourceId"],
            "expiration": int(ch.get("expiration", 0)),
            "page_token": page_token,
        }

    def stop_channel(self, channel_id: str, resource_id: str) -> None:
        self.svc.channels().stop(
            body={"id": channel_id, "resourceId": resource_id}
        ).execute()
