from pydantic import BaseModel, ConfigDict, Field


class Condition(BaseModel):
    text: str
    icon: str
    code: int


class AirQuality(BaseModel):
    co: float
    no2: float
    o3: float
    so2: float
    pm2_5: float
    pm10: float
    us_epa_index: int = Field(
        validation_alias="us-epa-index", serialization_alias="us-epa-index"
    )
    gb_defra_index: int = Field(
        validation_alias="gb-defra-index", serialization_alias="gb-defra-index"
    )


class Location(BaseModel):
    name: str
    region: str
    country: str
    lat: float
    lon: float
    tz_id: str
    localtime_epoch: int
    localtime: str


class Current(BaseModel):
    last_updated_epoch: int
    last_updated: str
    temp_c: float
    temp_f: float
    is_day: int
    condition: Condition
    wind_mph: float
    wind_kph: float
    wind_degree: int
    wind_dir: str
    pressure_mb: float
    pressure_in: float
    precip_mm: float
    precip_in: float
    humidity: int
    cloud: int
    feelslike_c: float
    feelslike_f: float
    windchill_c: float
    windchill_f: float
    heatindex_c: float
    heatindex_f: float
    dewpoint_c: float
    dewpoint_f: float
    vis_km: float
    vis_miles: float
    uv: float
    gust_mph: float
    gust_kph: float
    air_quality: AirQuality | None
    short_rad: float
    diff_rad: float
    dni: float
    gti: float


class Day(BaseModel):
    maxtemp_c: float
    maxtemp_f: float
    mintemp_c: float
    mintemp_f: float
    avgtemp_c: float
    avgtemp_f: float
    maxwind_mph: float
    maxwind_kph: float
    totalprecip_mm: float
    totalprecip_in: float
    totalsnow_cm: float
    avgvis_km: float
    avgvis_miles: float
    avghumidity: int
    daily_will_it_rain: int
    daily_chance_of_rain: int
    daily_will_it_snow: int
    daily_chance_of_snow: int
    condition: Condition
    uv: float
    air_quality: AirQuality


class Astro(BaseModel):
    sunrise: str
    sunset: str
    moonrise: str
    moonset: str
    moon_phase: str
    moon_illumination: int
    is_moon_up: int
    is_sun_up: int


class Hour(BaseModel):
    time_epoch: int
    time: str
    temp_c: float
    temp_f: float
    is_day: int
    condition: Condition
    wind_mph: float
    wind_kph: float
    wind_degree: int
    wind_dir: str
    pressure_mb: float
    pressure_in: float
    precip_mm: float
    precip_in: float
    snow_cm: float
    humidity: int
    cloud: int
    feelslike_c: float
    feelslike_f: float
    windchill_c: float
    windchill_f: float
    heatindex_c: float
    heatindex_f: float
    dewpoint_c: float
    dewpoint_f: float
    will_it_rain: int
    chance_of_rain: int
    will_it_snow: int
    chance_of_snow: int
    vis_km: float
    vis_miles: float
    gust_mph: float
    gust_kph: float
    uv: float
    air_quality: AirQuality
    short_rad: float
    diff_rad: float
    dni: float
    gti: float


class ForecastDay(BaseModel):
    date: str
    date_epoch: int
    day: Day
    astro: Astro
    hour: list[Hour]


class Forecast(BaseModel):
    forecastday: list[ForecastDay]


class Alert(BaseModel):
    headline: str
    msgtype: str
    severity: str
    urgency: str
    areas: str
    category: str
    certainty: str
    event: str
    note: str
    effective: str
    expires: str
    desc: str
    instruction: str


class Alerts(BaseModel):
    alert: list[Alert]


class GetForecastResponse(BaseModel):
    model_config = ConfigDict(
        validate_by_alias=True,  # accept incoming dashed keys
        validate_by_name=True,  # also allow field names
    )

    location: Location
    current: Current
    forecast: Forecast
    alerts: Alerts | None
