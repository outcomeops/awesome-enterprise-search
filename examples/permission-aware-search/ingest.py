"""Ingest Google Docs into S3 Vectors with per-document ACL metadata.

For each Google Doc the OAuth user can see, this script:
  1. Reads the document's text (exported as plain text).
  2. Reads the document's Drive permissions.
  3. Encodes those permissions as a flat list of principal strings:
       - "user@example.com"   (Drive type=user or type=group)
       - "domain:example.com" (Drive type=domain)
       - "anyone"             (Drive type=anyone, "anyone with the link")
  4. Chunks the text, embeds each chunk with Bedrock Titan v2, and writes the
     vectors to S3 Vectors. The principal list is stored as filterable metadata
     on every chunk so the search step can do a single `$in` filter.
"""
from __future__ import annotations

import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from s3vectors_client import BUCKET, INDEX, embed, ensure_bucket_and_index, s3v

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
DOC_MIME = "application/vnd.google-apps.document"
CHUNK_CHARS = 1000
PUT_BATCH = 100  # S3 Vectors put_vectors accepts up to 500; stay well under.


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


def list_docs(svc):
    page_token = None
    while True:
        resp = svc.files().list(
            q=f"mimeType='{DOC_MIME}' and trashed=false",
            fields="nextPageToken, files(id, name, permissions(type, emailAddress, domain, role))",
            pageSize=100,
            pageToken=page_token,
        ).execute()
        for f in resp.get("files", []):
            yield f
        page_token = resp.get("nextPageToken")
        if not page_token:
            return


def fetch_text(svc, file_id: str) -> str:
    raw = svc.files().export(fileId=file_id, mimeType="text/plain").execute()
    return raw.decode("utf-8") if isinstance(raw, bytes) else raw


def encode_principals(perms: list[dict] | None) -> list[str]:
    """Flatten a Drive permissions list into the principal strings we'll filter on."""
    out: set[str] = set()
    for p in perms or []:
        t = p.get("type")
        if t in ("user", "group"):
            email = p.get("emailAddress")
            if email:
                out.add(email.lower())
        elif t == "domain":
            domain = p.get("domain")
            if domain:
                out.add(f"domain:{domain.lower()}")
        elif t == "anyone":
            out.add("anyone")
    return sorted(out)


def chunk_text(text: str, max_chars: int = CHUNK_CHARS) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + 1 > max_chars and cur:
            chunks.append(" ".join(cur))
            cur, cur_len = [w], len(w)
        else:
            cur.append(w)
            cur_len += len(w) + 1
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def put_batch(client, vectors: list[dict]) -> None:
    if not vectors:
        return
    client.put_vectors(vectorBucketName=BUCKET, indexName=INDEX, vectors=vectors)


def main() -> None:
    ensure_bucket_and_index()
    svc = drive_service()
    client = s3v()

    pending: list[dict] = []
    n_docs = n_chunks = 0

    for f in list_docs(svc):
        file_id = f["id"]
        title = f.get("name", "(untitled)")
        principals = encode_principals(f.get("permissions"))
        if not principals:
            print(f"skip {title}: no readable principals (likely a permissions-list scope issue)")
            continue

        try:
            text = fetch_text(svc, file_id)
        except HttpError as e:
            print(f"skip {title}: export failed ({e})")
            continue
        if not text.strip():
            continue

        chunks = chunk_text(text)
        n_docs += 1
        n_chunks += len(chunks)
        print(f"indexing {title}: {len(chunks)} chunks, {len(principals)} principals")

        for idx, chunk in enumerate(chunks):
            pending.append({
                "key": f"{file_id}:{idx}",
                "data": {"float32": embed(chunk)},
                "metadata": {
                    "acl_principals": principals,
                    "title": title,
                    "source_text": chunk,
                    "source_url": f"https://docs.google.com/document/d/{file_id}/edit",
                },
            })
            if len(pending) >= PUT_BATCH:
                put_batch(client, pending)
                pending = []

    put_batch(client, pending)
    print(f"done: {n_docs} docs, {n_chunks} chunks indexed into {BUCKET}/{INDEX}")


if __name__ == "__main__":
    main()
