"""CN: 路线 provider 抽象，补充路线形态、道路上下文和高德骑行路径信息。
EN: Route provider abstraction that enriches route shape, road context, and AMap bicycling path facts.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any, Callable

import httpx


LOCAL_POINT_REGISTRY: dict[str, dict[str, Any]] = {
    "沈塘桥": {"longitude": 120.1518, "latitude": 30.2895, "region": "拱墅"},
    "凤起路": {"longitude": 120.1669, "latitude": 30.2635, "region": "拱墅"},
    "凤起路地铁站": {"longitude": 120.1669, "latitude": 30.2635, "region": "拱墅"},
    "杭州东": {"longitude": 120.2120, "latitude": 30.2918, "region": "上城"},
    "杭州东站": {"longitude": 120.2120, "latitude": 30.2918, "region": "上城"},
    "闻涛路滨江段": {"longitude": 120.2103, "latitude": 30.2064, "region": "滨江"},
    "杨公堤南口": {"longitude": 120.1378, "latitude": 30.2417, "region": "西湖"},
    "湘湖游客中心": {"longitude": 120.2525, "latitude": 30.1545, "region": "萧山"},
    "奥体印象城外广场": {"longitude": 120.2251, "latitude": 30.2288, "region": "滨江"},
    "余杭良渚文化村口": {"longitude": 120.0451, "latitude": 30.3721, "region": "余杭"},
}
LOCAL_CYCLING_DETOUR_FACTOR = 1.25
LOCAL_APPROACH_SPEED_KMH = 16.0


class LocalRouteProvider:
    provider_name = "local-route-stub"

    def resolve_point(self, address: str, *, city_code: str) -> dict[str, Any]:
        normalized_address = _normalize_local_address(address)
        known = LOCAL_POINT_REGISTRY.get(normalized_address)
        if known is None:
            raise RuntimeError("local-route-provider-unknown-point")
        return {
            "name": normalized_address,
            "longitude": known["longitude"],
            "latitude": known["latitude"],
            "region": known.get("region"),
            "source": "local-registry",
        }

    def get_cycling_path(self, start_point: dict[str, Any], end_point: dict[str, Any]) -> dict[str, Any]:
        if None in (
            start_point.get("longitude"),
            start_point.get("latitude"),
            end_point.get("longitude"),
            end_point.get("latitude"),
        ):
            raise RuntimeError("local-route-provider-missing-coordinate")
        return _estimate_local_cycling_path(start_point, end_point)

    def get_route_context(self, route: dict[str, Any], constraints: dict[str, Any]) -> dict[str, Any]:
        origin_region = constraints.get("origin_region") or route.get("district_tags", ["杭州"])[0]
        distance_km = float(route.get("distance_km", 0))
        estimated_duration_hours = float(route.get("estimated_duration_hours", 0))
        average_speed_kmh = round(distance_km / estimated_duration_hours, 1) if estimated_duration_hours else None
        template_start_point = {
            "name": route.get("start_point_name"),
            "longitude": route.get("start_point_lng"),
            "latitude": route.get("start_point_lat"),
            "source": "template",
        }
        user_start_point = self._resolve_local_user_start_point(constraints, route)
        approach_context = self._estimate_local_approach(user_start_point, template_start_point)
        # 本地 provider 不重算整条骑行路线，只把“用户到模板起点”的接驳段叠加到样板路线。
        total_distance_km = round(distance_km + approach_context["approach_distance_km"], 1)
        total_duration_hours = round(estimated_duration_hours + approach_context["approach_duration_hours"], 2)
        if approach_context["fact_source"] == "template+local-approach":
            return _compose_route_context(
                route,
                provider_name=self.provider_name,
                fact_source="template+local-approach",
                live_fact_source="local-approach",
                start_region=user_start_point.get("region") or origin_region,
                distance_km=total_distance_km,
                estimated_duration_hours=total_duration_hours,
                average_speed_kmh=round(total_distance_km / total_duration_hours, 1) if total_duration_hours else average_speed_kmh,
                template_distance_km=distance_km,
                template_duration_hours=estimated_duration_hours,
                total_distance_km=total_distance_km,
                total_duration_hours=total_duration_hours,
                approach_distance_km=approach_context["approach_distance_km"],
                approach_duration_hours=approach_context["approach_duration_hours"],
                user_start_point=user_start_point,
                template_start_point=template_start_point,
                surface_type=route.get("surface_type"),
                loop_type=route.get("loop_type"),
                approach_method="local-coordinate-estimate",
            )
        return _compose_route_context(
            route,
            provider_name=self.provider_name,
            fact_source="template",
            live_fact_source=None,
            start_region=origin_region,
            distance_km=distance_km,
            estimated_duration_hours=estimated_duration_hours,
            average_speed_kmh=average_speed_kmh,
            template_distance_km=distance_km,
            template_duration_hours=estimated_duration_hours,
            total_distance_km=distance_km,
            total_duration_hours=estimated_duration_hours,
            approach_distance_km=None,
            approach_duration_hours=None,
            user_start_point=user_start_point,
            template_start_point=template_start_point,
            surface_type=route.get("surface_type"),
            loop_type=route.get("loop_type"),
            fallback_reason="route-provider-template-only",
        )

    def _resolve_local_user_start_point(self, constraints: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
        start_point = constraints.get("start_point") or route.get("start_point_name")
        normalized_start_point = _normalize_local_address(start_point)
        if normalized_start_point in LOCAL_POINT_REGISTRY:
            known = LOCAL_POINT_REGISTRY[normalized_start_point]
            return {
                "name": normalized_start_point,
                "longitude": known["longitude"],
                "latitude": known["latitude"],
                "region": known.get("region"),
                "source": "local-registry",
            }
        return {"name": start_point, "longitude": None, "latitude": None, "source": "user-input"}

    def _estimate_local_approach(self, user_start_point: dict[str, Any], template_start_point: dict[str, Any]) -> dict[str, Any]:
        if None in (
            user_start_point.get("longitude"),
            user_start_point.get("latitude"),
            template_start_point.get("longitude"),
            template_start_point.get("latitude"),
        ):
            return {"fact_source": "template", "approach_distance_km": 0.0, "approach_duration_hours": 0.0}
        straight_distance_km = _haversine_km(
            float(user_start_point["longitude"]),
            float(user_start_point["latitude"]),
            float(template_start_point["longitude"]),
            float(template_start_point["latitude"]),
        )
        approach_distance_km = round(straight_distance_km * LOCAL_CYCLING_DETOUR_FACTOR, 1)
        approach_duration_hours = round(approach_distance_km / LOCAL_APPROACH_SPEED_KMH, 2) if approach_distance_km else 0.0
        return {
            "fact_source": "template+local-approach",
            "approach_distance_km": approach_distance_km,
            "approach_duration_hours": approach_duration_hours,
        }


def _haversine_km(start_lng: float, start_lat: float, end_lng: float, end_lat: float) -> float:
    radius_km = 6371.0
    delta_lat = radians(end_lat - start_lat)
    delta_lng = radians(end_lng - start_lng)
    lat1 = radians(start_lat)
    lat2 = radians(end_lat)
    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lng / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def _normalize_local_address(address: str | None) -> str:
    text = (address or "").strip()
    for suffix in ("附近", "周边"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    return text


def _estimate_local_cycling_path(start_point: dict[str, Any], end_point: dict[str, Any]) -> dict[str, Any]:
    # 没有真实骑行导航时，用直线距离 * 绕行系数给出保守估算，至少保证动态发现链路可继续。
    distance_km = round(
        _haversine_km(
            float(start_point["longitude"]),
            float(start_point["latitude"]),
            float(end_point["longitude"]),
            float(end_point["latitude"]),
        )
        * LOCAL_CYCLING_DETOUR_FACTOR,
        1,
    )
    estimated_duration_hours = round(distance_km / LOCAL_APPROACH_SPEED_KMH, 2) if distance_km else 0.0
    return {
        "distance_km": distance_km,
        "estimated_duration_hours": estimated_duration_hours,
        "average_speed_kmh": LOCAL_APPROACH_SPEED_KMH,
        "direction_summary": [],
        "polyline": _endpoint_polyline(start_point, end_point),
        "fallback_reason": "amap-bicycling-empty-local-estimate",
    }


def _endpoint_polyline(start_point: dict[str, Any], end_point: dict[str, Any]) -> list[dict[str, float]]:
    return [
        {"longitude": float(start_point["longitude"]), "latitude": float(start_point["latitude"])},
        {"longitude": float(end_point["longitude"]), "latitude": float(end_point["latitude"])},
    ]


def _route_end_point(route: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": route.get("end_point_name") or route.get("start_point_name"),
        "longitude": route.get("end_point_lng") or route.get("start_point_lng"),
        "latitude": route.get("end_point_lat") or route.get("start_point_lat"),
    }


def _build_route_template_layer(route: dict[str, Any], template_start_point: dict[str, Any]) -> dict[str, Any] | None:
    if route.get("route_source") == "dynamic_nearby":
        return None
    return {
        "fact_source": "template",
        "route_code": route.get("route_code"),
        "route_name": route.get("name"),
        "start_point": template_start_point,
        "end_point": _route_end_point(route),
        "distance_km": float(route.get("distance_km", 0)),
        "duration_hours": float(route.get("estimated_duration_hours", 0)),
        "surface_type": route.get("surface_type"),
        "loop_type": route.get("loop_type"),
    }


def _resolved_metric_source(route: dict[str, Any], fact_source: str, approach_distance_km: float | None) -> str:
    if route.get("route_source") == "dynamic_nearby":
        return "dynamic-live"
    if fact_source == "template":
        return "template"
    if approach_distance_km not in (None, 0, 0.0):
        return "template-plus-approach"
    return "template-plus-live"


def _compose_route_context(
    route: dict[str, Any],
    *,
    provider_name: str,
    fact_source: str,
    live_fact_source: str | None,
    start_region: str | None,
    distance_km: float,
    estimated_duration_hours: float,
    average_speed_kmh: float | None,
    template_distance_km: float,
    template_duration_hours: float,
    total_distance_km: float,
    total_duration_hours: float,
    approach_distance_km: float | None,
    approach_duration_hours: float | None,
    user_start_point: dict[str, Any],
    template_start_point: dict[str, Any],
    surface_type: str | None,
    loop_type: str | None,
    polyline: list[dict[str, float]] | None = None,
    direction_summary: list[dict[str, Any]] | None = None,
    road_context: dict[str, Any] | None = None,
    fallback_reason: str | None = None,
    approach_method: str | None = None,
    start_location: dict[str, Any] | None = None,
    approach_polyline: list[dict[str, float]] | None = None,
) -> dict[str, Any]:
    template_layer = _build_route_template_layer(route, template_start_point)
    live_layer = None
    if live_fact_source:
        live_layer = {
            "provider_name": provider_name,
            "fact_source": live_fact_source,
            "start_region": start_region,
            "user_start_point": user_start_point,
            "polyline": polyline or [],
            "direction_summary": direction_summary or [],
            "road_context": road_context,
            "approach_distance_km": approach_distance_km,
            "approach_duration_hours": approach_duration_hours,
            "approach_method": approach_method,
            "start_location": start_location,
            "approach_polyline": approach_polyline or [],
        }
    resolved_layer = {
        "provider_name": provider_name,
        "fact_source": fact_source,
        "metric_source": _resolved_metric_source(route, fact_source, approach_distance_km),
        "distance_km": distance_km,
        "estimated_duration_hours": estimated_duration_hours,
        "average_speed_kmh": average_speed_kmh,
        "total_distance_km": total_distance_km,
        "total_duration_hours": total_duration_hours,
    }
    context = {
        "provider_name": provider_name,
        "start_region": start_region,
        "distance_km": distance_km,
        "estimated_duration_hours": estimated_duration_hours,
        "average_speed_kmh": average_speed_kmh,
        "template_distance_km": template_distance_km,
        "template_duration_hours": template_duration_hours,
        "total_distance_km": total_distance_km,
        "total_duration_hours": total_duration_hours,
        "approach_distance_km": approach_distance_km,
        "approach_duration_hours": approach_duration_hours,
        "user_start_point": user_start_point,
        "template_start_point": template_start_point,
        "surface_type": surface_type,
        "loop_type": loop_type,
        "fact_source": fact_source,
        "template": template_layer,
        "live": live_layer,
        "resolved": resolved_layer,
    }
    if polyline:
        context["polyline"] = polyline
    if direction_summary:
        context["direction_summary"] = direction_summary
    if road_context:
        context["road_context"] = road_context
    if fallback_reason:
        context["fallback_reason"] = fallback_reason
    if approach_method:
        context["approach_method"] = approach_method
    if start_location:
        context["start_location"] = start_location
    if approach_polyline:
        context["approach_polyline"] = approach_polyline
    return context


class AMapRouteProvider:
    provider_name = "amap-route"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        timeout_seconds: float,
        http_get: Callable[..., Any] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.http_get = http_get or httpx.get

    def get_route_context(self, route: dict[str, Any], constraints: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("amap-route-provider-missing-key")

        template_start_point = self._resolve_point(
            route.get("start_point_name"),
            route.get("start_point_lng"),
            route.get("start_point_lat"),
            city_code=route.get("city_code", "hangzhou"),
        )
        user_start_point = self._resolve_user_start_point(constraints, route)
        reverse_payload = self._reverse_geocode(user_start_point["longitude"], user_start_point["latitude"])
        template_distance_km = float(route.get("distance_km", 0))
        template_duration_hours = float(route.get("estimated_duration_hours", 0))
        approach_context = self._resolve_approach_context(user_start_point, template_start_point)
        total_distance_km = round(template_distance_km + approach_context["approach_distance_km"], 1)
        total_duration_hours = round(template_duration_hours + approach_context["approach_duration_hours"], 2)
        fact_source = "template+amap"
        live_fact_source = "amap-approach"
        polyline = list(approach_context["approach_polyline"])
        direction_summary: list[dict[str, Any]] = []
        road_context = self._extract_road_context(reverse_payload)

        end_point_name = route.get("end_point_name")
        if end_point_name and end_point_name != route.get("start_point_name") and route.get("loop_type") != "loop":
            try:
                end_point = self._resolve_point(end_point_name, None, None, city_code=route.get("city_code", "hangzhou"))
                direction_payload = self._cycling_direction(template_start_point, end_point)
            except Exception:
                fact_source = "template+amap"
            else:
                normalized = self._normalize_direction(direction_payload)
                direction_summary = normalized["direction_summary"]
                polyline = [*approach_context["approach_polyline"], *normalized["polyline"]]
                fact_source = "amap"
                live_fact_source = "amap"
        elif approach_context["approach_polyline"]:
            polyline = approach_context["approach_polyline"]

        return _compose_route_context(
            route,
            provider_name=self.provider_name,
            fact_source=fact_source,
            live_fact_source=live_fact_source,
            start_region=self._extract_region(reverse_payload, constraints, route),
            distance_km=total_distance_km,
            estimated_duration_hours=total_duration_hours,
            average_speed_kmh=round(total_distance_km / total_duration_hours, 1) if total_duration_hours else None,
            template_distance_km=template_distance_km,
            template_duration_hours=template_duration_hours,
            total_distance_km=total_distance_km,
            total_duration_hours=total_duration_hours,
            approach_distance_km=approach_context["approach_distance_km"],
            approach_duration_hours=approach_context["approach_duration_hours"],
            user_start_point=user_start_point,
            template_start_point=template_start_point,
            surface_type=route.get("surface_type"),
            loop_type=route.get("loop_type"),
            polyline=polyline,
            direction_summary=direction_summary,
            road_context=road_context,
            start_location=user_start_point,
            approach_polyline=approach_context["approach_polyline"],
        )

    def resolve_point(self, address: str, *, city_code: str) -> dict[str, Any]:
        return self._resolve_point(address, None, None, city_code=city_code)

    def get_cycling_path(self, start_point: dict[str, Any], end_point: dict[str, Any]) -> dict[str, Any]:
        try:
            path = self._normalize_direction(self._cycling_direction(start_point, end_point))
        except Exception:
            # 高德骑行接口失败时，不中断上层流程，退回本地估算保证仍能产出候选。
            return _estimate_local_cycling_path(start_point, end_point)
        if not path.get("polyline"):
            path["polyline"] = _endpoint_polyline(start_point, end_point)
            path["fallback_reason"] = "amap-bicycling-polyline-empty-endpoint-fallback"
        return path

    def _resolve_user_start_point(self, constraints: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
        start_point = constraints.get("start_point")
        if not start_point:
            return self._resolve_point(
                route.get("start_point_name"),
                route.get("start_point_lng"),
                route.get("start_point_lat"),
                city_code=route.get("city_code", "hangzhou"),
            )
        return self._resolve_point(start_point, None, None, city_code=route.get("city_code", "hangzhou"))

    def _resolve_approach_context(self, user_start_point: dict[str, Any], template_start_point: dict[str, Any]) -> dict[str, Any]:
        if user_start_point["longitude"] == template_start_point["longitude"] and user_start_point["latitude"] == template_start_point["latitude"]:
            return {"approach_distance_km": 0.0, "approach_duration_hours": 0.0, "approach_polyline": []}
        direction_payload = self._cycling_direction(user_start_point, template_start_point)
        normalized = self._normalize_direction(direction_payload)
        return {
            "approach_distance_km": normalized["distance_km"],
            "approach_duration_hours": normalized["estimated_duration_hours"],
            "approach_polyline": normalized["polyline"],
        }

    def _resolve_point(
        self,
        address: str | None,
        longitude: float | None,
        latitude: float | None,
        *,
        city_code: str,
    ) -> dict[str, Any]:
        if longitude is not None and latitude is not None:
            # 模板里已有坐标时直接复用，避免重复 geocode 带来的额外请求和偏移误差。
            return {"name": address, "longitude": float(longitude), "latitude": float(latitude), "source": "template"}
        if not address:
            raise RuntimeError("amap-route-provider-missing-address")

        response = self.http_get(
            f"{self.base_url}/v3/geocode/geo",
            params={"key": self.api_key, "address": address, "city": city_code},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "1" or not payload.get("geocodes"):
            raise RuntimeError("amap-geocode-empty")
        location = payload["geocodes"][0]["location"]
        lng, lat = location.split(",")
        return {"name": address, "longitude": float(lng), "latitude": float(lat), "source": "amap-geocode"}

    def _reverse_geocode(self, longitude: float, latitude: float) -> dict[str, Any]:
        response = self.http_get(
            f"{self.base_url}/v3/geocode/regeo",
            params={"key": self.api_key, "location": f"{longitude},{latitude}", "extensions": "base"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "1" or "regeocode" not in payload:
            raise RuntimeError("amap-regeo-empty")
        return payload

    def _cycling_direction(self, start_point: dict[str, Any], end_point: dict[str, Any]) -> dict[str, Any]:
        response = self.http_get(
            f"{self.base_url}/v4/direction/bicycling",
            params={
                "key": self.api_key,
                "origin": f"{start_point['longitude']},{start_point['latitude']}",
                "destination": f"{end_point['longitude']},{end_point['latitude']}",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if str(payload.get("errcode")) != "0" or not payload.get("data", {}).get("paths"):
            raise RuntimeError("amap-bicycling-empty")
        return payload

    def _normalize_direction(self, payload: dict[str, Any]) -> dict[str, Any]:
        path = payload["data"]["paths"][0]
        distance_m = float(path.get("distance", 0))
        duration_s = float(path.get("duration", 0))
        rides = path.get("rides", [])
        return {
            "distance_km": round(distance_m / 1000, 1),
            "estimated_duration_hours": round(duration_s / 3600, 2),
            "average_speed_kmh": round((distance_m / 1000) / (duration_s / 3600), 1) if duration_s else None,
            "direction_summary": rides[:2],
            "polyline": self._extract_polyline(rides),
        }

    def _extract_polyline(self, rides: list[dict[str, Any]]) -> list[dict[str, float]]:
        points: list[dict[str, float]] = []
        for ride in rides:
            for raw_point in str(ride.get("polyline", "")).split(";"):
                if not raw_point or "," not in raw_point:
                    continue
                longitude, latitude = raw_point.split(",", 1)
                points.append({"longitude": float(longitude), "latitude": float(latitude)})
        return points

    def _extract_region(self, payload: dict[str, Any], constraints: dict[str, Any], route: dict[str, Any]) -> str:
        regeocode = payload.get("regeocode", {})
        component = regeocode.get("addressComponent", {})
        district = component.get("district")
        return district or constraints.get("origin_region") or route.get("district_tags", ["杭州"])[0]

    def _extract_road_context(self, payload: dict[str, Any]) -> dict[str, Any]:
        regeocode = payload.get("regeocode", {})
        component = regeocode.get("addressComponent", {})
        roads = regeocode.get("roads", [])
        return {
            "province": component.get("province"),
            "city": component.get("city"),
            "district": component.get("district"),
            "road_name": roads[0].get("name") if roads else None,
        }

    def _calc_average_speed(self, route: dict[str, Any]) -> float | None:
        distance_km = float(route.get("distance_km", 0))
        estimated_duration_hours = float(route.get("estimated_duration_hours", 0))
        return round(distance_km / estimated_duration_hours, 1) if estimated_duration_hours else None
