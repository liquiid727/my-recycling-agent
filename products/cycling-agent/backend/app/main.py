"""CN: FastAPI 应用工厂，装配 provider、仓库、缓存、路由和启动初始化。
EN: FastAPI application factory that wires providers, repositories, cache, routes, and startup initialization.
"""

from fastapi import FastAPI

from app.api.routes.admin import router as admin_router
from app.api.routes.profile import router as profile_router
from app.api.routes.ride_chat import router as ride_chat_router
from app.api.routes.ride_plan import router as ride_plan_router
from app.api.routes.route_catalog import router as route_catalog_router
from app.core.cache import build_cache_backend
from app.core.config import Settings
from app.core.storage import init_storage
from app.providers.llm_provider import OpenAICompatibleLLMProvider
from app.providers.poi_provider import AMapPoiProvider, LocalPoiProvider
from app.providers.route_provider import AMapRouteProvider, LocalRouteProvider
from app.providers.weather_provider import CachedWeatherProvider, OpenMeteoWeatherProvider
from app.repositories.route_template_repository import seed_route_templates
from app.repositories.nearby_trip_repository import seed_nearby_trip_catalog


def create_app(*, weather_provider: OpenMeteoWeatherProvider | None = None, route_provider=None, poi_provider=None) -> FastAPI:
    settings = Settings()
    app = FastAPI(title=settings.app_name)
    app.state.database_url = settings.database_url
    app.state.cache_backend = build_cache_backend(settings.redis_url)
    base_weather_provider = weather_provider or OpenMeteoWeatherProvider(
        base_url=settings.weather_provider_base_url,
        timeout_seconds=settings.weather_timeout_seconds,
    )
    app.state.weather_provider = CachedWeatherProvider(
        base_weather_provider,
        app.state.cache_backend,
        ttl_seconds=settings.weather_cache_ttl_seconds,
    )
    app.state.ride_plan_cache_ttl_seconds = settings.ride_plan_cache_ttl_seconds
    app.state.llm_provider = _build_llm_provider(settings)
    app.state.route_provider = route_provider or _build_route_provider(settings)
    app.state.poi_provider = poi_provider or _build_poi_provider(settings)
    init_storage(settings.database_url)
    seed_route_templates(
        settings.database_url,
        Path(__file__).resolve().parents[2] / "data" / "hangzhou_routes.json",
    )
    seed_nearby_trip_catalog(
        settings.database_url,
        Path(__file__).resolve().parents[2] / "data" / "hangzhou_nearby_destinations.json",
        Path(__file__).resolve().parents[2] / "data" / "hangzhou_trip_templates.json",
    )
    app.include_router(ride_chat_router)
    app.include_router(ride_plan_router)
    app.include_router(route_catalog_router)
    app.include_router(profile_router)
    app.include_router(admin_router)

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app


def _build_route_provider(settings: Settings):
    if settings.route_provider_mode == "amap":
        _require_amap_key(settings)
        return AMapRouteProvider(
            base_url=settings.amap_base_url,
            api_key=settings.amap_web_api_key,
            timeout_seconds=settings.amap_timeout_seconds,
        )
    return LocalRouteProvider()


def _build_poi_provider(settings: Settings):
    if settings.poi_provider_mode == "amap":
        _require_amap_key(settings)
        return AMapPoiProvider(
            base_url=settings.amap_base_url,
            api_key=settings.amap_web_api_key,
            timeout_seconds=settings.amap_timeout_seconds,
        )
    return LocalPoiProvider()


def _require_amap_key(settings: Settings) -> None:
    if not settings.amap_web_api_key:
        raise RuntimeError("cycling-agent-amap-key-missing")


def _build_llm_provider(settings: Settings):
    if settings.llm_api_base_url and settings.llm_api_key and settings.llm_model:
        return OpenAICompatibleLLMProvider(
            base_url=settings.llm_api_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            thinking=settings.llm_thinking,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    return None

from pathlib import Path


app = FastAPI(title="cycling-agent-backend-bootstrap")


@app.get("/health")
async def healthcheck_bootstrap() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def _bootstrap_app() -> None:
    configured_app = create_app()
    app.router.routes = configured_app.router.routes
    app.state.__dict__.update(configured_app.state.__dict__)
