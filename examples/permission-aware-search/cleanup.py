"""Delete the vector bucket + index this example created.

Idempotent: NotFound is treated as "already gone." Order matters — the index
has to go before the bucket can be deleted.

Usage:
    python cleanup.py          # prompts before deleting
    python cleanup.py --yes    # skip the prompt
"""
from __future__ import annotations

import argparse
import sys

from botocore.exceptions import ClientError

from s3vectors_client import BUCKET, INDEX, s3v


def delete_index(client) -> None:
    try:
        client.delete_index(vectorBucketName=BUCKET, indexName=INDEX)
        print(f"deleted index: {INDEX}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "NotFoundException":
            print(f"index {INDEX} already gone")
            return
        raise


def delete_bucket(client) -> None:
    try:
        client.delete_vector_bucket(vectorBucketName=BUCKET)
        print(f"deleted bucket: {BUCKET}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "NotFoundException":
            print(f"bucket {BUCKET} already gone")
            return
        raise


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--yes", action="store_true", help="skip confirmation prompt")
    args = p.parse_args()

    print(f"about to delete:\n  bucket: {BUCKET}\n  index:  {INDEX}")
    if not args.yes:
        if input("proceed? [y/N] ").strip().lower() != "y":
            sys.exit("aborted")

    client = s3v()
    delete_index(client)
    delete_bucket(client)


if __name__ == "__main__":
    main()
