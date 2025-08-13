from datetime import datetime, timedelta
import json
import os
from typing import Any, Dict
from zoneinfo import ZoneInfo

from api.next_actions.post.models import (
    from_weather_api_forecast_response,
    DatetimeHints,
)
import boto3
from botocore.exceptions import ClientError
from utils.weather_api_client import WeatherApiClient


WEATHER_API_KEY = os.environ["WEATHER_API_KEY"]
WEATHER_API_LANG = os.environ["WEATHER_API_LANG"]
WEATHER_API_LOCATION = os.environ["WEATHER_API_LOCATION"]
BEDROCK_REGION = os.environ["BEDROCK_REGION"]
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]

SYSTEM_PROMPT = "Du bist die Stimme einer Sprachuhr, die nur einen Knopf als Eingabe und einen Lautsprecher als Ausgabe besitzt. Hauptnutzer sind seh-eingeschränkte Personen, die einen einfachen Zugang zu Informationen und Daten wünschen. Die Ausgaben sollen freundlich und leicht verständlich sein und in ganzen Sätzen formuliert werden. Sprich ausschliesslich deutsch."

USER_PROMPT = """Erstelle basierend auf den folgenden Wetter- und Zeitdaten eine kurze, freundliche Nachricht gemäß der folgenden Vorgaben und Hinweise. Informiere den Nutzer über die Zeit, den Wochentag, das Datum, und zusätzlich einen kompakten Wetterbericht mit kurzer Vorhersage. Die Nachricht sollte kompakt gehalten werden und verschiedene Informationen müssen priorisiert werden. Die Nachricht sollte zwischen 50 und 80 Wörtern lang sein und neben den Informationen auch freundliche Worte enthalten.

Guidelines:
* Für den aktuellen Tag, ist die Wetterentwicklung relevant, speziell Niederschläge sind zu erwähnen. Eine Tendenz für die kommenden Tage kann optional gegeben werden. Außerdem sollten extreme Wetterbedingung hervorgehoben werden. Relevante Warnungen für den aktuelle Tag bzw. die kommenden Tage haben eine hohe Priorität.
* Sollte es aktuell schon dunkel sein, speziell aber mitten in der Nacht, kann die Zeit des Sonnenaufgangs am selben oder nächsten erwähnt werden. Der Zeitpunkt des Sonnenuntergangs ist nicht relevant.
* Vor besonders heißen Temperaturen sollte gewarnt werden; ein Hinweis viel zu trinken kann passend sein. Vor starken Stürmen oder Regenfällen sollte ebenfalls gewarnt werden. Genau so kann eine schlechte Luftqualität erwähnt werden. Besonders kalte Temperaturen sind ebenfalls erwähnenswert.
* Bei Wetterbedingungen, die für Personen mit Kreislaufbeschwerden schwierig sind, sollte hingewiesen werden.
* Uhrzeiten sollten im Format "12:34" (ohne "Uhr") angegeben werden.
* Nutzer sollen geduzt werden.

Hier sind ein paar Beispielnachrichten:
"Guten Tag! Heute ist der 9. August. Es ist jetzt 13:33. Aktuell ist es überwiegend sonnig bei etwa 27 Grad Celsius. Im Nachmittag steigen die Temperaturen weiter bis auf rund 30 Grad. Auch am frühen Abend bleibt es weiterhin sonnig und angenehm – ein perfekter Spätsommertag!

---

WOCHENTAG, DATUM UND ZEIT
{{local_datetime_hints}}

---

WETTER- UND VORHERSAGEDATEN
{{weather_forecast_json}}
"""

weather_api_client = WeatherApiClient(api_key=WEATHER_API_KEY, lang=WEATHER_API_LANG)
bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)


def _get_local_datetime_hints() -> DatetimeHints:
    now = datetime.now(ZoneInfo("Europe/Berlin"))
    tomorrow = now + timedelta(days=1)
    day_after_tomorrow = now + timedelta(days=2)

    return DatetimeHints(
        now=now.strftime("%A, %Y-%m-%d %H:%M:%S"),
        tomorrow=tomorrow.strftime("%A, %Y-%m-%d"),
        day_after_tomorrow=day_after_tomorrow.strftime("%A, %Y-%m-%d"),
    )


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    forecast_days = 3
    wa_forecast = weather_api_client.get_forecast(
        q=WEATHER_API_LOCATION,
        days=forecast_days,
        include_aqi=True,
        include_alerts=True,
    )

    datetime_hints = _get_local_datetime_hints()
    forecast = from_weather_api_forecast_response(wa_forecast)

    # Prepare prompts
    system = [{"text": SYSTEM_PROMPT}]
    user_prompt_filled = USER_PROMPT.replace(
        "{{local_datetime_hints}}", datetime_hints.model_dump_json()
    ).replace("{{weather_forecast_json}}", forecast.model_dump_json())
    messages = [
        {"role": "user", "content": [{"text": user_prompt_filled}]},
    ]

    print("+++ system", system)
    print("+++ messages", messages)

    # Call Bedrock (Converse)
    try:
        resp = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            system=system,
            messages=messages,
            inferenceConfig={
                # keep it steady and TTS-friendly
                "maxTokens": 400,
                "temperature": 0.4,
                "topP": 0.9,
            },
        )
        # Extract text (Converse returns output.message.content list)
        outputs = resp.get("output", {}).get("message", {}).get("content", [])
        llm_text = ""
        for part in outputs:
            if "text" in part:
                llm_text += part["text"]
        if not llm_text:
            llm_text = "Entschuldigung, ich konnte die Wetterzusammenfassung gerade nicht erzeugen."

        print("+++ llm_text", llm_text)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "action_type": "say",
                    "text": llm_text.strip(),
                },
                ensure_ascii=False,
            ),
        }

    except ClientError as e:
        # Fallback path if Bedrock errors—keeps device usable
        print("Bedrock error:", repr(e))
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "action_type": "say",
                    "text": (
                        "Entschuldigung, der Wetterdienst ist momentan nicht erreichbar. "
                        "Bitte versuche es später erneut."
                    ),
                },
                ensure_ascii=False,
            ),
        }
