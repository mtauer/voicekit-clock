import base64
import json
import os
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")

BUCKET = os.environ["BUCKET_NAME"]


def _bad_request(msg: str) -> Dict[str, Any]:
    return {
        "statusCode": 400,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": msg}, ensure_ascii=False),
    }


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    qs = (event or {}).get("queryStringParameters") or {}
    text = qs.get("text-content")
    if not text:
        return _bad_request("Missing required query parameter: text-content")

    # Try to serve from cache
    try:
        key = "time_13_33.mp3"
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        body = obj["Body"].read()
        return _audio_response(body)
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchKey":
            # For other S3 errors, bubble up as 500
            return _server_error(f"S3 error: {e}")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _audio_response(audio_bytes: bytes) -> Dict[str, Any]:
    # API Gateway (Lambda proxy) needs base64 body + isBase64Encoded for binary media.
    b64 = base64.b64encode(audio_bytes).decode("ascii")
    return {
        "statusCode": 200,
        "isBase64Encoded": True,
        "headers": {
            "Content-Type": "audio/mpeg",
            "Content-Length": str(len(audio_bytes)),
            "Cache-Control": "public, max-age=31536000, immutable",
            "Content-Disposition": 'attachment; filename="audio.mp3"',
        },
        "body": b64,
    }


def _server_error(msg: str) -> Dict[str, Any]:
    return {
        "statusCode": 500,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": msg}, ensure_ascii=False),
    }
