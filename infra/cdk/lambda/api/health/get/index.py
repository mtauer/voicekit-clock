import json
from typing import Any


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "status": "up",
            },
            ensure_ascii=False,
        ),
    }
