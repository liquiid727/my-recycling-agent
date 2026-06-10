"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from datetime import date

from app.providers.weather_provider import OpenMeteoWeatherProvider


class StubResponse:
    def json(self) -> dict:
        return {
            "daily": {
                "time": ["2026-05-30"],
                "temperature_2m_min": [22.0],
                "temperature_2m_max": [31.0],
                "precipitation_probability_max": [15],
                "wind_speed_10m_max": [4.8],
                "wind_direction_10m_dominant": [135],
                "weather_code": [3],
            }
        }

    def raise_for_status(self) -> None:
        return None


def test_open_meteo_provider_normalizes_daily_forecast() -> None:
    provider = OpenMeteoWeatherProvider(
        http_get=lambda *args, **kwargs: StubResponse(),
    )

    snapshot = provider.get_weather_snapshot(
        city_code="hangzhou",
        region_code="binjiang",
        forecast_date=date(2026, 5, 30),
    )

    assert snapshot["region_code"] == "binjiang"
    assert snapshot["temperature_max"] == 31.0
    assert snapshot["precipitation_probability"] == 0.15
    assert snapshot["wind_direction"] == "SE"
    assert snapshot["weather_summary"] == "cloudy"
