"""CN: 天气 provider 与缓存包装，归一化 Open-Meteo 天气快照并提供失败兜底。
EN: Weather provider and cache wrapper that normalizes Open-Meteo snapshots and fallback behavior.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Callable

import httpx


WEATHER_CODE_SUMMARY = {
    0: "clear",
    1: "mainly_clear",
    2: "partly_cloudy",
    3: "cloudy",
    45: "fog",
    48: "fog",
    51: "drizzle",
    53: "drizzle",
    55: "drizzle",
    61: "rain",
    63: "rain",
    65: "heavy_rain",
    71: "snow",
    73: "snow",
    75: "snow",
    80: "rain_showers",
    81: "rain_showers",
    82: "rain_showers",
    95: "thunderstorm",
}

WIND_DIRECTION_BUCKETS = [
    "N",
    "NE",
    "E",
    "SE",
    "S",
    "SW",
    "W",
    "NW",
]

REGION_COORDINATES = {
    "hangzhou": {"latitude": 30.2741, "longitude": 120.1551},
    "binjiang": {"latitude": 30.2067, "longitude": 120.2108},
    "xihu": {"latitude": 30.2431, "longitude": 120.1504},
    "longjing": {"latitude": 30.2232, "longitude": 120.1172},
    "xianghu": {"latitude": 30.1636, "longitude": 120.2539},
    "yuhang": {"latitude": 30.4212, "longitude": 120.3019},
    "xiaoshan": {"latitude": 30.1620, "longitude": 120.2707},
}


class OpenMeteoWeatherProvider:
    def __init__(
        self,
        *,
        base_url: str = "https://api.open-meteo.com/v1/forecast",
        timeout_seconds: float = 8.0,
        http_get: Callable[..., Any] | None = None,
    ) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.http_get = http_get or httpx.get

    def get_weather_snapshot(
        self,
        *,
        city_code: str,
        region_code: str,
        forecast_date: date,
    ) -> dict[str, Any]:
        coordinates = REGION_COORDINATES.get(region_code) or REGION_COORDINATES.get(city_code)
        if coordinates is None:
            raise ValueError(f"unsupported-region:{city_code}:{region_code}")

        response = self.http_get(
            self.base_url,
            params={
                "latitude": coordinates["latitude"],
                "longitude": coordinates["longitude"],
                "timezone": "Asia/Shanghai",
                "start_date": forecast_date.isoformat(),
                "end_date": forecast_date.isoformat(),
                "daily": ",".join(
                    [
                        "temperature_2m_min",
                        "temperature_2m_max",
                        "precipitation_probability_max",
                        "wind_speed_10m_max",
                        "wind_direction_10m_dominant",
                        "weather_code",
                    ]
                ),
                "wind_speed_unit": "ms",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        daily = payload["daily"]

        return {
            "region_code": region_code,
            "forecast_date": daily["time"][0],
            "temperature_min": daily["temperature_2m_min"][0],
            "temperature_max": daily["temperature_2m_max"][0],
            "precipitation_probability": round(daily["precipitation_probability_max"][0] / 100, 2),
            "wind_speed": daily["wind_speed_10m_max"][0],
            "wind_direction": _degree_to_compass(daily["wind_direction_10m_dominant"][0]),
            "weather_summary": WEATHER_CODE_SUMMARY.get(daily["weather_code"][0], "unknown"),
            "provider_name": "open-meteo",
            "raw_payload": payload,
        }


class CachedWeatherProvider:
    def __init__(self, weather_provider, cache_backend, *, ttl_seconds: int = 900) -> None:
        self.weather_provider = weather_provider
        self.cache_backend = cache_backend
        self.ttl_seconds = ttl_seconds
        self.provider_name = getattr(weather_provider, "provider_name", "cached-weather")

    def get_weather_snapshot(
        self,
        *,
        city_code: str,
        region_code: str,
        forecast_date: date,
    ) -> dict[str, Any]:
        from app.core.cache import weather_cache_key

        cache_key = weather_cache_key(
            city_code=city_code,
            region_code=region_code,
            forecast_date=forecast_date.isoformat(),
        )
        cached = self.cache_backend.get_json(cache_key)
        if cached is not None:
            return cached
        snapshot = self.weather_provider.get_weather_snapshot(
            city_code=city_code,
            region_code=region_code,
            forecast_date=forecast_date,
        )
        self.cache_backend.set_json(cache_key, snapshot, ttl_seconds=self.ttl_seconds)
        return snapshot


def normalize_region_code(region_name: str | None, city_code: str) -> str:
    if not region_name:
        return city_code

    lookup = {
        "滨江": "binjiang",
        "西湖": "xihu",
        "龙井": "longjing",
        "湘湖": "xianghu",
        "余杭": "yuhang",
        "萧山": "xiaoshan",
    }
    return lookup.get(region_name, city_code)


def build_fallback_weather_snapshot(region_code: str, forecast_date: date) -> dict[str, Any]:
    return {
        "region_code": region_code,
        "forecast_date": forecast_date.isoformat(),
        "temperature_min": None,
        "temperature_max": 29.0,
        "precipitation_probability": 0.15,
        "wind_speed": 3.0,
        "wind_direction": "SE",
        "weather_summary": "unknown",
        "provider_name": "fallback",
        "raw_payload": None,
    }


def _degree_to_compass(degree: float | int | None) -> str:
    if degree is None:
        return "unknown"
    index = int(((float(degree) + 22.5) % 360) / 45)
    return WIND_DIRECTION_BUCKETS[index]
