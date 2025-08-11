import json
import os
from typing import Any
import urllib.parse
import urllib.request

from utils.weather_api_client_models import GetForecastResponse


WEATHER_API_BASE_URL = os.environ["WEATHER_API_BASE_URL"].rstrip("/")


class WeatherApiClient:
    def __init__(self, api_key: str, lang: str):
        self._api_key = api_key
        self.lang = lang

    def _get(self, url_path: str, params: dict[str, Any]) -> dict[str, Any]:
        qs = urllib.parse.urlencode(params)
        url = f"{WEATHER_API_BASE_URL}{url_path}?{qs}"
        req = urllib.request.Request(url, headers={"User-Agent": "weather-client/1.0"})
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.status != 200:
                raise RuntimeError(f"WeatherAPI HTTP {response.status}")
            return json.load(response)

    def get_forecast(
        self,
        *,
        q: str,
        days: int | None,
        include_aqi: bool | None,
        include_alerts: bool | None,
    ) -> GetForecastResponse:
        params = {
            "key": self._api_key,
            "q": q,
            "days": str(days),
            "aqi": "yes" if include_aqi else "no",
            "alerts": "yes" if include_alerts else "no",
            "lang": self.lang,
        }
        response_data = self._get("/forecast.json", params)

        # Validate and return
        return GetForecastResponse.model_validate(response_data)
