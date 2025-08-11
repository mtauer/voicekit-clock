import json
import os
from typing import Any, Dict

from utils.weather_api_client import WeatherApiClient


WEATHER_API_KEY = os.environ["WEATHER_API_KEY"]
WEATHER_API_LANG = os.environ["WEATHER_API_LANG"]
WEATHER_API_LOCATION = os.environ["WEATHER_API_LOCATION"]

weather_api_client = WeatherApiClient(api_key=WEATHER_API_KEY, lang=WEATHER_API_LANG)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    forecast_days = 1
    forecast = weather_api_client.get_forecast(
        q=WEATHER_API_LOCATION,
        days=forecast_days,
        include_aqi=True,
        include_alerts=True,
    )

    prompt = forecast.model_dump_json()

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"prompt": prompt}, ensure_ascii=False),
    }
