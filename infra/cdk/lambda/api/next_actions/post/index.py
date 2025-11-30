from datetime import datetime, timedelta
import json
import os
from typing import Any, Dict
from zoneinfo import ZoneInfo
import boto3
from botocore.exceptions import ClientError
import contentful

from api.next_actions.post.models import (
    BirthdayCalendarItem,
    DatetimeHints,
    map_contentful_birthday_items,
    weather_api_forecast_response_to_forecast_description,
)
from utils.weather_api_client import WeatherApiClient


WEATHER_API_KEY = os.environ["WEATHER_API_KEY"]
WEATHER_API_LANG = os.environ["WEATHER_API_LANG"]
WEATHER_API_LOCATION = os.environ["WEATHER_API_LOCATION"]
BEDROCK_REGION = os.environ["BEDROCK_REGION"]
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]
CONTENTFUL_SPACE_ID = os.environ["CONTENTFUL_SPACE_ID"]
CONTENTFUL_ACCESS_TOKEN = os.environ["CONTENTFUL_ACCESS_TOKEN"]
INCLUDE_BIRTHDAY_CALENDAR = os.environ["INCLUDE_BIRTHDAY_CALENDAR"] == "True"

SYSTEM_PROMPT = "Du bist die Stimme einer Sprachuhr, die nur einen Knopf als Eingabe und einen Lautsprecher als Ausgabe besitzt. Hauptnutzer sind seh-eingeschränkte Personen, die einen einfachen Zugang zu Informationen und Daten wünschen. Die Ausgaben sollen freundlich und leicht verständlich sein und in ganzen Sätzen formuliert werden. Sprich ausschliesslich deutsch."

USER_PROMPT_BASE = """Erstelle basierend auf den folgenden Wetter- und Zeitdaten eine kurze, freundliche Nachricht gemäß der folgenden Vorgaben und Hinweise. Informiere den Nutzer über die Zeit, den Wochentag, das Datum, und zusätzlich einen kompakten Wetterbericht mit kurzer Vorhersage. Die Nachricht sollte kompakt gehalten werden und verschiedene Informationen müssen priorisiert werden. Die Nachricht sollte zwischen 50 und 80 Wörtern lang sein und neben den Informationen auch freundliche Worte enthalten.

Guidelines:
* Für den aktuellen Tag, ist die Wetterentwicklung relevant, speziell Niederschläge sind zu erwähnen. Eine Tendenz für die kommenden Tage kann optional gegeben werden. Außerdem sollten extreme Wetterbedingung hervorgehoben werden. Relevante Warnungen für den aktuelle Tag bzw. die kommenden Tage haben eine hohe Priorität.
* Sollte es aktuell schon dunkel sein, speziell aber mitten in der Nacht, kann die Zeit des Sonnenaufgangs am selben oder nächsten erwähnt werden. Der Zeitpunkt des Sonnenuntergangs ist nicht relevant.
* Vor besonders heißen Temperaturen sollte gewarnt werden; ein Hinweis viel zu trinken kann passend sein. Vor starken Stürmen oder Regenfällen sollte ebenfalls gewarnt werden. Genau so kann eine schlechte Luftqualität erwähnt werden. Besonders kalte Temperaturen sind ebenfalls erwähnenswert.
* Bei Wetterbedingungen, die für Personen mit Kreislaufbeschwerden schwierig sind, sollte hingewiesen werden.
* Uhrzeiten sollten im Format "12:34" (ohne "Uhr") angegeben werden.
* Nutzer sollen geduzt werden.

Hier sind ein paar Beispielnachrichten:
"Guten Tag! Heute ist der 9. August. Es ist jetzt 13:33. Aktuell ist es überwiegend sonnig bei etwa 27 Grad Celsius. Im Nachmittag steigen die Temperaturen weiter bis auf rund 30 Grad. Auch am frühen Abend bleibt es weiterhin sonnig und angenehm – ein perfekter Spätsommertag!"
"Guten Abend! Heute ist Samstag, der 29. November. Es ist jetzt 19:54. Aktuell ist es bedeckt bei 7 Grad, gefühlt sind es 5 Grad. Der Wind weht mit 13 Stundenkilometern aus Süden. Morgen erwarten dich ähnliche Temperaturen mit gelegentlichen Regenschauern. Am Montag wird es dann etwas kälter mit nur noch 6 Grad. Die Sonne geht morgen um 7:53 auf."

---

WOCHENTAG, DATUM UND ZEIT
{{local_datetime_hints}}

---

WETTER- UND VORHERSAGEDATEN
{{weather_forecast_json}}
"""

USER_PROMPT_BIRTHDAY_EXTENSION = """

---

ZUSÄTZLICHE ANWEISUNGEN FÜR GEBURTSTAGSINFORMATIONEN

Erweitere die Nachricht nach dem Wetterteil um eine kurze Information zu kommenden Geburtstagen, falls welche in den nächsten 14 Tagen im Kalender eingetragen sind. Die Geburtstagsinformationen sollen klar, ruhig und gut verständlich sein.

Guidelines für Geburtstagsinformationen:
* Die Wetter- und Zeitinformation kommt immer zuerst. Erst danach folgt ein kurzer Übergang zu den Geburtstagen.
* Die Geburtstagsinformationen sind ein separater Absatz. Absätze sollen durch Zeilenumbrüche voneinander getrennt werden.
* Wenn es einen oder mehrere Geburtstage innerhalb der nächsten 14 Tage gibt, fasse sie kurz zusammen.
* Verwende vorzugsweise Formulierungen mit relativer Zeit UND Datum, zum Beispiel:
  - "In drei Tagen, am 12. März, wird deine Tochter Anna 75 Jahre alt."
  - "Morgen, am 3. April, wird dein Enkel Paul 12 Jahre alt."
  - "Heute, am 5. Mai, wird deine Enkelin Lisa 10 Jahre alt."
* Wenn das Alter der Person bekannt ist, nenne es zusätzlich. Wenn kein Alter vorliegt, nenne nur den Geburtstag:
  - "In sechs Tagen, am 15. März, hat deine Freundin Maria Geburtstag."
* Verwende einfache, gut strukturierte Sätze und sprich den Nutzer mit "du" an.
* Nenne die Beziehung (z. B. Tochter, Sohn, Enkel, Enkelin, Freund, Nachbar) zusammen mit dem Vornamen/Kurznamen, wenn diese Information vorhanden ist.
* Runde Geburtstage sollen speziell hervorgehoben werden.

Beispiele für Übergänge vom Wetterteil zu den Geburtstagen:
* "Und jetzt noch ein kurzer Überblick über die nächsten Geburtstage. In den nächsten zwei Wochen stehen gleich drei Geburtstage an."
* "Zum Schluss noch ein Blick auf die drei anstehenden Geburtstage in den nächsten zwei Wochen."
* "Außer dem Wetter gibt es noch etwas Wichtiges: die nächsten Geburtstage. Es gibt zwei in den nächsten zwei Wochen."
* "Das war der Wetterbericht. In den nächsten zwei Wochen steht kein Geburtstag an."
* "Außerdem gibt es demnächst zwei Geburtstage, an die du denken kannst."

Wenn es KEINE Geburtstage innerhalb der nächsten 14 Tage gibt, füge nach dem Wetter einen kurzen Satz hinzu, zum Beispiel:
* "In den nächsten zwei Wochen steht kein Geburtstag an."
* "In den kommenden zwei Wochen hat niemand Geburtstag."
* "Es gibt keine Geburtstage in den nächsten zwei Wochen."

Achte weiterhin darauf, dass die gesamte Nachricht kompakt bleibt. Die Geburtstagsinformationen sollen sich in den vorhandenen Rahmen einfügen und die Nachricht nicht unnötig verlängern. Wenn nötig, kann der Wetterteil etwas knapper gehalten werden, damit die Gesamtlänge in einem ähnlichen Umfang bleibt.

---

GEBURTSTAGSMETADATEN (JSON)

Die folgenden Daten stehen dir als JSON-Array zur Verfügung. Jeder Eintrag kann u. a. folgende Felder enthalten:
* "name": Vorname/Kurzname/Name der Person (z. B. "Anna")
* "relation": Beziehung zum Nutzer (z. B. "Tochter", "Sohn", "Enkel", "Enkelin", "Freund", "Nachbar")
* "date": Datum des nächsten Geburtstags im ISO-Format (z. B. "2025-03-12")
* "days_until_birthday": Anzahl der Tage bis zum nächsten Geburtstag (Ganzzahl)
* "age": Alter, das die Person an diesem Geburtstag erreicht (Ganzzahl, optional)

Nutze diese Daten, um die oben beschriebenen Geburtstagsinformationen zu formulieren.

GEBURTSTAGSDATEN
{{birthday_calendar_json}}
"""

if INCLUDE_BIRTHDAY_CALENDAR:
    USER_PROMPT = USER_PROMPT_BASE + USER_PROMPT_BIRTHDAY_EXTENSION
else:
    USER_PROMPT = USER_PROMPT_BASE

weather_api_client = WeatherApiClient(api_key=WEATHER_API_KEY, lang=WEATHER_API_LANG)
bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # 1) Fetch + normalize forecast
        forecast_days = 3
        datetime_hints = _get_local_datetime_hints()

        try:
            wa_forecast = weather_api_client.get_forecast(
                q=WEATHER_API_LOCATION,
                days=forecast_days,
                include_aqi=True,
                include_alerts=True,
            )
        except Exception as e:
            return _error_response(e, code="WEATHER_FETCH_FAILED")

        try:
            forecast = weather_api_forecast_response_to_forecast_description(
                wa_forecast
            )
        except Exception as e:
            return _error_response(e, code="FORECAST_PARSE_FAILED")

        all_birthday_calendar_items = (
            [] if not INCLUDE_BIRTHDAY_CALENDAR else _get_birthday_calendar()
        )
        birthday_calendar_items = [
            item
            for item in all_birthday_calendar_items
            if 0 <= item.days_until_birthday <= 14
        ]

        # 2) Build prompts
        system = [{"text": SYSTEM_PROMPT}]
        user_prompt_filled = (
            USER_PROMPT.replace(
                "{{local_datetime_hints}}", datetime_hints.model_dump_json()
            )
            .replace("{{weather_forecast_json}}", forecast.model_dump_json())
            .replace(
                "{{birthday_calendar_json}}",
                json.dumps(
                    [item.model_dump_json() for item in birthday_calendar_items],
                    ensure_ascii=False,
                ),
            )
        )
        messages = [{"role": "user", "content": [{"text": user_prompt_filled}]}]

        print("[DEBUG] system prompt:", system)
        print("[DEBUG] messages:", messages)

        # 3) Call Bedrock Converse
        try:
            resp = bedrock_client.converse(
                modelId=BEDROCK_MODEL_ID,
                system=system,
                messages=messages,
                inferenceConfig={
                    "maxTokens": 400,
                    "temperature": 0.4,
                    "topP": 0.9,
                },
            )
        except ClientError as e:
            return _error_response(e, code="BEDROCK_CLIENT_ERROR")
        except Exception as e:
            return _error_response(e, code="BEDROCK_CALL_FAILED")

        # 4) Extract text
        outputs = resp.get("output", {}).get("message", {}).get("content", [])
        llm_text_parts = [
            part.get("text", "") for part in outputs if isinstance(part, dict)
        ]
        llm_text = "".join(llm_text_parts).strip()

        if not llm_text:
            return _error_response(
                RuntimeError("Empty model output"), code="LLM_EMPTY_OUTPUT"
            )

        print("[DEBUG] llm_text:", llm_text)

        # 5) Success
        return _json_response(
            200,
            {
                "action_type": "say",
                "text": llm_text,
            },
        )

    except Exception as e:
        return _error_response(e, code="UNHANDLED_EXCEPTION")


def _get_local_datetime_hints() -> DatetimeHints:
    now = datetime.now(ZoneInfo("Europe/Berlin"))
    tomorrow = now + timedelta(days=1)
    day_after_tomorrow = now + timedelta(days=2)

    return DatetimeHints(
        now=now.strftime("%A, %Y-%m-%d %H:%M:%S"),
        tomorrow=tomorrow.strftime("%A, %Y-%m-%d"),
        day_after_tomorrow=day_after_tomorrow.strftime("%A, %Y-%m-%d"),
    )


def _get_birthday_calendar() -> list[BirthdayCalendarItem]:
    client = contentful.Client(CONTENTFUL_SPACE_ID, CONTENTFUL_ACCESS_TOKEN)
    cf_birthday_calendar_items = client.entries(
        {"content_type": "birthdayCalendarItem"}
    )

    return map_contentful_birthday_items(cf_birthday_calendar_items)


def _json_response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _error_response(exc: Exception, code: str = "INTERNAL_ERROR") -> Dict[str, Any]:
    print(f"[ERROR] {code}: {repr(exc)}")
    return _json_response(
        500,
        {
            "error": {
                "code": code,
                "message": "Internal server error",
            }
        },
    )
