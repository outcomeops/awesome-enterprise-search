# Permission-aware enterprise search

A runnable example showing how to do **permission propagation** correctly: when Alice and Bob run the same query against the same index, they only see the documents they're authorized to read in the source system.

Most RAG tutorials skip this. They build an index, embed everything, and let any user query everything — which is the difference between a demo and something you can actually deploy inside a company.

This example uses **Google Drive** as the source of truth for permissions and **AWS S3 Vectors** as the vector store. The same pattern works for any OAuth source (Confluence, SharePoint, Notion, GitHub) and any vector store with metadata filtering.

## The core idea

1. **At ingest time**, for each document, ask the source system *who can read this?* Store the answer as metadata on the vector.
2. **At query time**, build a filter from the searcher's identity (their email, their group memberships, "anyone") and pass it to the vector store as a metadata filter.
3. **The vector store applies the filter during the ANN search**, not after — so you don't get the "top-K results, then 0 after filtering" surprise.

In S3 Vectors, that filter looks like:

```python
{"$or": [
    {"acl_principals": {"$eq": "alice@example.com"}},
    {"acl_principals": {"$eq": "engineering@example.com"}},
    {"acl_principals": {"$eq": "domain:example.com"}},
    {"acl_principals": {"$eq": "anyone"}},
]}
```

A note on filter shape: S3 Vectors' [filter docs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-metadata-filtering.html) explicitly document that `$eq` against a list-valued metadata field matches when the scalar appears as an element of the list. The behavior of `$in` against a list-valued field is *not* specified, so this example uses an `$or` of `$eq` clauses to stay on the documented path. The same docs confirm filters are evaluated *in tandem* with the similarity search — you get correct top-K rather than the "top-K then filter" surprise.

## What you'll need

- Python 3.11+
- An AWS account with S3 Vectors and Bedrock enabled in the same region (the example uses `us-west-2` — adjust in `.env`)
- Bedrock model access for `amazon.titan-embed-text-v2:0` (1024-dim embeddings)
- A Google Cloud project with the Drive API enabled and an OAuth client ID (Desktop app type) — download as `credentials.json` into this folder
- A few Google Docs in your Drive with mixed sharing (some private, some shared with specific users, some "anyone with the link")

## Setup

```bash
cd examples/permission-aware-search
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then edit values
```

Place your Google OAuth client file at `./credentials.json`. The first run of `ingest.py` will open a browser for consent and write `./token.json`.

## Run

**Index your Drive docs (one-time, or re-run to refresh):**

```bash
python ingest.py
```

**Search as one identity:**

```bash
python search.py --as alice@example.com --query "Q3 roadmap" \
  --groups engineering@example.com --domain example.com
```

**Search as another identity, same query:**

```bash
python search.py --as contractor@external.com --query "Q3 roadmap"
```

You should see different results — the contractor only sees documents explicitly shared with them or with "anyone with the link." That's the property you want.

## What this looks like in production

This example is intentionally minimal so you can read it end-to-end. Real deployments need to handle several things it skips:

- **Group expansion.** This example trusts the `--groups` CLI flag. In production, resolve group memberships from your IdP (Google Workspace Admin SDK `groups.list?userKey=...`, Okta, Entra ID) at query time, with a short-TTL cache. Group changes need to invalidate the cache or you'll get stale authorization.
- **Nested groups.** Most IdPs allow groups inside groups. Real expansion is recursive with cycle detection.
- **Deny rules.** Drive doesn't have them, but SharePoint, Confluence, and Box do. `$in` is not enough — you also need a `$nin` against a deny list, or you compute the effective ACL at ingest and only store the resolved allow set.
- **Permission drift.** Permissions change continuously. This example re-indexes everything; production needs a delta-sync loop driven by Drive's [`changes.watch`](https://developers.google.com/drive/api/reference/rest/v3/changes/watch) webhook (or polling `changes.list` with a `pageToken`) so a revocation propagates in seconds, not on the next nightly job. *(That's the next example in this repo: `delta-sync-pattern/`.)*
- **Identity at query time.** This example takes `--as` from a CLI flag, which is fine for a demo and a security disaster for anything real. Production reads the verified identity from a session token or ID token and never trusts a client-supplied user ID.
- **Chunking.** This example chunks at 1000 chars on whitespace boundaries — fine for a demo, not optimal for retrieval. Production wants semantic or layout-aware chunking, and ACL metadata copied onto every chunk.
- **Document types.** This example only ingests Google Docs (exported as plain text). Production needs PDFs, Word docs, Sheets, slides — each with its own extraction path.
- **Per-chunk permissions.** Some systems (Confluence with restricted page sections, Notion with per-block permissions) have ACLs *below* the document level. The pattern is the same — just attach the per-chunk ACL instead of the per-document one.
- **Audit trail.** Log every query with the resolved principal set used for filtering, so you can prove what a user could and couldn't see at any point in time.

## Files

| File | What it does |
| --- | --- |
| `ingest.py` | OAuths into Drive, lists Google Docs, fetches each doc's permissions, embeds with Bedrock Titan v2, writes to S3 Vectors with `acl_principals` metadata. |
| `search.py` | Embeds the query, builds the principal set from `--as`/`--groups`/`--domain`, queries S3 Vectors with an `$in` filter. |
| `s3vectors_client.py` | Idempotent `create_or_get` for the bucket and index, plus the Bedrock embedding call. Shared by ingest and search. |

## License

Same as the parent repo.
