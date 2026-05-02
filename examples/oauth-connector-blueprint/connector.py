"""The shape every connector implements.

A connector's job is to make documents from one source system pullable in a
uniform way: list them, fetch their content, fetch who can read them, and
subscribe to change notifications. The vector store / search layer is downstream
of this — it doesn't care which provider produced the Document.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Document:
    id: str            # provider-stable ID, used as the vector key
    title: str
    body: str
    url: str           # canonical link back to the source
    updated_at: str    # ISO-8601; used by the delta-sync example
    extra: dict = field(default_factory=dict)


@dataclass
class WebhookSubscription:
    id: str            # provider's hook ID, needed to unsubscribe later
    callback_url: str
    events: list[str]


class Connector(ABC):
    """Override these four methods. Everything else (OAuth, token persistence,
    signature verification) is provided by the blueprint modules."""

    @abstractmethod
    def iter_documents(self, since: str | None = None) -> Iterator[Document]:
        """Yield Documents. If `since` is provided, yield only ones updated after it."""

    @abstractmethod
    def fetch_permissions(self, document: Document) -> list[str]:
        """Return the principal strings authorized to read `document`.

        Use the same encoding across providers so the search layer can do one
        kind of $eq filter. Suggested:
            "user:<provider>:<id-or-email>"
            "group:<provider>:<id-or-email>"
            "domain:<domain>"
            "anyone"
        """

    @abstractmethod
    def register_webhook(
        self, callback_url: str, secret: str, events: list[str]
    ) -> WebhookSubscription:
        """Subscribe `callback_url` to provider events. The provider will sign
        each delivery with `secret` so the receiver can verify authenticity."""
