"""CN: 后端运行配置入口，集中读取数据库、缓存、LLM、高德和天气相关环境变量。
EN: Backend settings entrypoint for database, cache, LLM, AMap, and weather environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CYCLING_AGENT_", extra="ignore")

    app_name: str = "cycling-agent-backend"
    database_url: str = "sqlite:///./cycling-agent.db"
    llm_api_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = 20.0
    weather_provider_base_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_timeout_seconds: float = 8.0
    redis_url: str | None = None
    weather_cache_ttl_seconds: int = 900
    ride_plan_cache_ttl_seconds: int = 1800
    route_provider_mode: str = "local"
    poi_provider_mode: str = "local"
    amap_base_url: str = "https://restapi.amap.com"
    amap_web_api_key: str | None = None
    amap_timeout_seconds: float = 10.0
