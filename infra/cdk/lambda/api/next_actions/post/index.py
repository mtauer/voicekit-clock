import json
import os
from typing import Any, Dict

from api.next_actions.post.models import from_weather_api_forecast_response
from utils.weather_api_client import WeatherApiClient


WEATHER_API_KEY = os.environ["WEATHER_API_KEY"]
WEATHER_API_LANG = os.environ["WEATHER_API_LANG"]
WEATHER_API_LOCATION = os.environ["WEATHER_API_LOCATION"]

weather_api_client = WeatherApiClient(api_key=WEATHER_API_KEY, lang=WEATHER_API_LANG)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    forecast_days = 3
    wa_forecast = weather_api_client.get_forecast(
        q=WEATHER_API_LOCATION,
        days=forecast_days,
        include_aqi=True,
        include_alerts=True,
    )

    forecast = from_weather_api_forecast_response(wa_forecast)

    print("+++ forecast", forecast.model_dump_json())

    # TODO:
    # - build prompt
    # - call LLM
    # - return result

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "action_type": "say",
                "text": "Guten Tag! Heute ist der 9. August. Es ist jetzt 13:33. Aktuell ist es überwiegend sonnig bei etwa 27 Grad Celsius. Am Nachmittag steigen die Temperaturen weiter bis auf rund 30 Grad. Auch am frühen Abend bleibt es weiterhin sonnig und angenehm – ein perfekter Spätsommertag!",
            },
            ensure_ascii=False,
        ),
    }
