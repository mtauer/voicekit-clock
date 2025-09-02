import base64
import json
import os
import re
from typing import Any

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")
polly = boto3.client("polly")

BUCKET_NAME = os.environ["BUCKET_NAME"]
TTS_VOICE_ID = os.environ["TTS_VOICE_ID"]
TTS_ENGINE = os.environ["TTS_ENGINE"]
TTS_OUTPUT_FORMAT = os.environ["TTS_OUTPUT_FORMAT"]
TTS_SAMPLE_RATE = os.environ["TTS_SAMPLE_RATE"]


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    qs = (event or {}).get("queryStringParameters") or {}
    text = qs.get("text")
    if not text:
        return _bad_request("Missing required query parameter: text")

    should_cache_audio = len(text) < 100

    # Try to serve from cache
    if should_cache_audio:
        cleaned_text = re.sub(r"[^a-zA-Z0-9]", "_", text)
        cache_key = f"polly/{TTS_VOICE_ID}/{cleaned_text}.{TTS_OUTPUT_FORMAT}"

        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=cache_key)
            body = obj["Body"].read()
            return _audio_response(body)
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchKey":
                # For other S3 errors, bubble up as 500
                return _server_error(f"S3 error: {e}")

    # Not cached -> synthesize with Polly, store, return
    try:
        res = polly.synthesize_speech(
            Text=text,
            TextType="text",
            OutputFormat=TTS_OUTPUT_FORMAT,
            SampleRate=TTS_SAMPLE_RATE,
            VoiceId=TTS_VOICE_ID,
            Engine=TTS_ENGINE,
        )
        audio_stream = res.get("AudioStream")
        if audio_stream is None:
            return _server_error("No audio stream from Polly.")

        audio_bytes = audio_stream.read()

        # Cache to S3
        if should_cache_audio:
            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=cache_key,
                Body=audio_bytes,
                ContentType="audio/mpeg",
                CacheControl="public, max-age=31536000, immutable",
            )

        return _audio_response(audio_bytes)

    except ClientError as e:
        return _server_error(f"Polly error: {e}")


def _audio_response(audio_bytes: bytes) -> dict[str, Any]:
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


def _bad_request(msg: str) -> dict[str, Any]:
    return {
        "statusCode": 400,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": msg}, ensure_ascii=False),
    }


def _server_error(msg: str) -> dict[str, Any]:
    return {
        "statusCode": 500,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": msg}, ensure_ascii=False),
    }
