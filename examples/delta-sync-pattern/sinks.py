"""Where deltas land.

Each sync_*.py defaults to printing — that's enough to see the patterns work.
To wire deltas into a real index, implement this two-method protocol. See
`examples/permission-aware-search/` for an S3 Vectors writer you can adapt:
    - upsert(doc) → embed(doc.body) + put_vectors(...)
    - delete(id)  → s3v().delete_vectors(keys=[id, ...])
"""
from __future__ import annotations

from typing import Protocol

from connector import Document


class Sink(Protocol):
    def upsert(self, doc: Document) -> None: ...
    def delete(self, doc_id: str) -> None: ...


class StdoutSink:
    def upsert(self, doc: Document) -> None:
        print(f"  upsert {doc.id}  {doc.title!r}  modified={doc.updated_at}")

    def delete(self, doc_id: str) -> None:
        print(f"  delete {doc_id}")
