"""Search the index built by ingest.py, filtering by the searcher's ACL principals.

Usage:
    python search.py --as alice@example.com --query "Q3 roadmap" \\
        --groups engineering@example.com,leads@example.com \\
        --domain example.com

The --as / --groups / --domain flags simulate an authenticated identity. In
production these come from the verified session, never from CLI input.
"""
from __future__ import annotations

import argparse

from s3vectors_client import BUCKET, INDEX, embed, s3v


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--as", dest="user", required=True, help="searcher's email")
    p.add_argument("--query", required=True, help="natural-language query")
    p.add_argument("--groups", default="", help="comma-separated group emails")
    p.add_argument("--domain", default="", help="searcher's workspace domain")
    p.add_argument("--top-k", type=int, default=5)
    return p.parse_args()


def build_principals(user: str, groups: str, domain: str) -> list[str]:
    """The set of principal strings this searcher is authorized as.

    Mirrors the encoding used in ingest.py:encode_principals so the comparison
    is apples-to-apples. "anyone" is always included so anyone-with-the-link
    documents are visible to every authenticated user.
    """
    out: set[str] = {user.lower(), "anyone"}
    if domain:
        out.add(f"domain:{domain.lower()}")
    for g in (groups or "").split(","):
        g = g.strip().lower()
        if g:
            out.add(g)
    return sorted(out)


def build_filter(principals: list[str]) -> dict:
    """Match vectors where any of the searcher's principals appears in
    acl_principals.

    We use $or of $eq rather than $in because the S3 Vectors docs only
    document `$eq against a list-valued field` — it matches when the scalar
    appears as an element of the list. The behavior of `$in` against a
    list-valued field is not specified, so we stay on the documented path.
    See: https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-metadata-filtering.html
    """
    return {"$or": [{"acl_principals": {"$eq": p}} for p in principals]}


def main() -> None:
    args = parse_args()
    principals = build_principals(args.user, args.groups, args.domain)

    print(f"searching as: {args.user}")
    print(f"effective principals: {principals}")
    print(f"query: {args.query}\n")

    response = s3v().query_vectors(
        vectorBucketName=BUCKET,
        indexName=INDEX,
        queryVector={"float32": embed(args.query)},
        topK=args.top_k,
        filter=build_filter(principals),
        returnDistance=True,
        returnMetadata=True,
    )

    hits = response.get("vectors", [])
    if not hits:
        print("no authorized matches.")
        return

    for i, hit in enumerate(hits, 1):
        md = hit.get("metadata", {})
        title = md.get("title", "(untitled)")
        url = md.get("source_url", "")
        text = (md.get("source_text", "") or "").strip().replace("\n", " ")
        snippet = text[:200] + ("…" if len(text) > 200 else "")
        print(f"{i}. {title}  (distance={hit.get('distance'):.4f})")
        print(f"   {url}")
        print(f"   {snippet}\n")


if __name__ == "__main__":
    main()
