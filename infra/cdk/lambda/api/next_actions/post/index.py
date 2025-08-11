import json
import os
from typing import Any, Dict

from api.next_actions.post.models import from_weather_api_get_forecast_response
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

    forecast = from_weather_api_get_forecast_response(wa_forecast)

    print("+++ forecast", forecast.model_dump_json())

    prompt = forecast.model_dump_json()

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"prompt": prompt}, ensure_ascii=False),
    }
