from pydantic import BaseModel
from datetime import datetime
from zoneinfo import ZoneInfo

from utils.weather_api_client_models import GetForecastResponse


class Condition(BaseModel):
    text: str


class AirQuality(BaseModel):
    co: float
    no2: float
    o3: float
    so2: float
    pm2_5: float
    pm10: float
    us_epa_index: int
    gb_defra_index: int


class Current(BaseModel):
    temp_c: float
    feelslike_c: float
    humidity: int
    wind_kph: float
    wind_dir: str
    gust_kph: float
    cloud: int
    precip_mm: float
    pressure_mb: float
    vis_km: float
    uv: float
    is_day: int
    condition: Condition
    air_quality: AirQuality | None = None


class Hour(BaseModel):
    time: str
    temp_c: float
    feelslike_c: float
    humidity: int
    wind_kph: float
    wind_dir: str
    gust_kph: float
    cloud: int
    precip_mm: float
    chance_of_rain: int
    will_it_rain: int
    is_day: int
    condition: Condition
    uv: float


class Day(BaseModel):
    maxtemp_c: float
    mintemp_c: float
    avgtemp_c: float
    maxwind_kph: float
    avghumidity: int
    totalprecip_mm: float
    daily_chance_of_rain: int
    daily_will_it_rain: int
    condition: Condition
    uv: float


class Astro(BaseModel):
    sunrise: str
    sunset: str
    moonrise: str
    moonset: str
    moon_phase: str
    moon_illumination: int
    is_moon_up: int
    is_sun_up: int


class Alert(BaseModel):
    headline: str
    severity: str
    urgency: str
    event: str
    effective: str
    expires: str
    desc: str
    instruction: str | None = None
    areas: str | None = None
    certainty: str | None = None
    category: str | None = None
    msgtype: str | None = None
    note: str | None = None


class Location(BaseModel):
    name: str
    region: str
    country: str


class LocalTime(BaseModel):
    tz_id: str
    local_datetime: str
    local_weekday: str


class DailyBlock(BaseModel):
    date: str
    summary: Day


class ForecastDescription(BaseModel):
    location: Location
    localtime: LocalTime
    hours_today: list[Hour] = []
    days_overview: list[DailyBlock] = []
    current: Current
    alerts: list[Alert] = []
    astro_today: Astro | None = None
    astro_tomorrow: Astro | None = None


class DatetimeHints(BaseModel):
    now: str
    tomorrow: str
    day_after_tomorrow: str


def weather_api_forecast_response_to_forecast_description(
    src: GetForecastResponse,
) -> ForecastDescription:
    # Local time handling
    tz = ZoneInfo(src.location.tz_id)
    local_now = datetime.fromtimestamp(src.location.localtime_epoch, tz)
    today_date = local_now.date()

    # Helper: parse "YYYY-MM-DD HH:MM" in the provided local tz
    def parse_local_hour(ts: str) -> datetime:
        # WeatherAPI uses local time formatted as "YYYY-MM-DD HH:MM"
        return datetime.strptime(ts, "%Y-%m-%d %H:%M").replace(tzinfo=tz)

    # Forecast days list (can be shorter than expected, be defensive)
    days = list(src.forecast.forecastday)

    hours_today: list[Hour] = []
    if days:
        # find the ForecastDay matching 'today' in local tz
        fd_today = next(
            (
                d
                for d in days
                if datetime.strptime(d.date, "%Y-%m-%d").date() == today_date
            ),
            days[0],
        )
        for h in fd_today.hour:
            h_dt = parse_local_hour(h.time)
            if h_dt >= local_now:
                hours_today.append(
                    Hour(
                        time=h.time,
                        temp_c=h.temp_c,
                        feelslike_c=h.feelslike_c,
                        humidity=h.humidity,
                        wind_kph=h.wind_kph,
                        wind_dir=h.wind_dir,
                        gust_kph=h.gust_kph,
                        cloud=h.cloud,
                        precip_mm=h.precip_mm,
                        chance_of_rain=h.chance_of_rain,
                        will_it_rain=h.will_it_rain,
                        is_day=h.is_day,
                        condition=Condition(**h.condition.model_dump()),
                        uv=h.uv,
                    )
                )

    astro_today = None
    astro_tomorrow = None
    if days:
        # today
        d0 = days[0]
        astro_today = Astro(**d0.astro.model_dump())
        # tomorrow (if present)
        if len(days) > 1:
            d1 = days[1]
            astro_tomorrow = Astro(**d1.astro.model_dump())

    days_overview: list[DailyBlock] = []
    # Build a list of days in local tz, in order
    for d in days[:3]:
        days_overview.append(
            DailyBlock(
                date=d.date,
                summary=Day(
                    maxtemp_c=d.day.maxtemp_c,
                    mintemp_c=d.day.mintemp_c,
                    avgtemp_c=d.day.avgtemp_c,
                    maxwind_kph=d.day.maxwind_kph,
                    avghumidity=d.day.avghumidity,
                    totalprecip_mm=d.day.totalprecip_mm,
                    daily_chance_of_rain=d.day.daily_chance_of_rain,
                    daily_will_it_rain=d.day.daily_will_it_rain,
                    condition=Condition(**d.day.condition.model_dump()),
                    uv=d.day.uv,
                ),
            )
        )

    alerts: list[Alert] = []
    if src.alerts and src.alerts.alert:
        for a in src.alerts.alert:
            alerts.append(Alert(**a.model_dump()))

    current = Current(
        temp_c=src.current.temp_c,
        feelslike_c=src.current.feelslike_c,
        humidity=src.current.humidity,
        wind_kph=src.current.wind_kph,
        wind_dir=src.current.wind_dir,
        gust_kph=src.current.gust_kph,
        cloud=src.current.cloud,
        precip_mm=src.current.precip_mm,
        pressure_mb=src.current.pressure_mb,
        vis_km=src.current.vis_km,
        uv=src.current.uv,
        is_day=src.current.is_day,
        condition=Condition(**src.current.condition.model_dump()),
        air_quality=(
            AirQuality(**src.current.air_quality.model_dump())
            if src.current.air_quality is not None
            else None
        ),
    )

    return ForecastDescription(
        location=Location(
            name=src.location.name,
            region=src.location.region,
            country=src.location.country,
        ),
        localtime=LocalTime(
            tz_id=src.location.tz_id,
            local_datetime=src.location.localtime,
            local_weekday="",  # TODO
        ),
        alerts=alerts,
        astro_today=astro_today,
        astro_tomorrow=astro_tomorrow,
        hours_today=hours_today,
        days_overview=days_overview,
        current=current,
    )
