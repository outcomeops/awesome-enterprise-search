"""Shared S3 Vectors + Bedrock helpers for the permission-aware-search example."""
from __future__ import annotations

import json
import os
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

REGION = os.environ.get("AWS_REGION", "us-west-2")
BUCKET = os.environ["S3_VECTOR_BUCKET"]
INDEX = os.environ["S3_VECTOR_INDEX"]
EMBED_MODEL_ID = os.environ.get("BEDROCK_EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
EMBED_DIMENSION = int(os.environ.get("EMBED_DIMENSION", "1024"))

# Keys we never want to filter on — stored alongside the vector for display only.
# Everything not listed here (e.g. acl_principals) is filterable by default.
NON_FILTERABLE_KEYS = ["source_text", "source_url", "title"]


@lru_cache(maxsize=1)
def s3v():
    return boto3.client("s3vectors", region_name=REGION)


@lru_cache(maxsize=1)
def bedrock():
    return boto3.client("bedrock-runtime", region_name=REGION)


def ensure_bucket_and_index() -> None:
    """Create the vector bucket and index if they don't already exist."""
    client = s3v()
    try:
        client.create_vector_bucket(vectorBucketName=BUCKET)
        print(f"created vector bucket: {BUCKET}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConflictException":
            raise

    try:
        client.create_index(
            vectorBucketName=BUCKET,
            indexName=INDEX,
            dimension=EMBED_DIMENSION,
            distanceMetric="cosine",
            dataType="float32",
            metadataConfiguration={"nonFilterableMetadataKeys": NON_FILTERABLE_KEYS},
        )
        print(f"created vector index: {INDEX}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConflictException":
            raise


def embed(text: str) -> list[float]:
    """Embed text with Bedrock Titan Text Embeddings V2 (returns a list of float32)."""
    body = json.dumps(
        {"inputText": text, "dimensions": EMBED_DIMENSION, "normalize": True}
    )
    response = bedrock().invoke_model(modelId=EMBED_MODEL_ID, body=body)
    payload = json.loads(response["body"].read())
    return payload["embedding"]
