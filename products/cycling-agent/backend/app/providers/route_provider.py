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
        total_distance_km = round(distance_km + approach_context["approach_distance_km"], 1)
        total_duration_hours = round(estimated_duration_hours + approach_context["approach_duration_hours"], 2)
        if approach_context["fact_source"] == "template+local-approach":
            return {
                "provider_name": self.provider_name,
                "start_region": user_start_point.get("region") or origin_region,
                "distance_km": total_distance_km,
                "estimated_duration_hours": total_duration_hours,
                "average_speed_kmh": round(total_distance_km / total_duration_hours, 1) if total_duration_hours else average_speed_kmh,
                "template_distance_km": distance_km,
                "template_duration_hours": estimated_duration_hours,
                "total_distance_km": total_distance_km,
                "total_duration_hours": total_duration_hours,
                "approach_distance_km": approach_context["approach_distance_km"],
                "approach_duration_hours": approach_context["approach_duration_hours"],
                "user_start_point": user_start_point,
                "template_start_point": template_start_point,
                "surface_type": route.get("surface_type"),
                "loop_type": route.get("loop_type"),
                "fact_source": "template+local-approach",
                "approach_method": "local-coordinate-estimate",
            }
        return {
            "provider_name": self.provider_name,
            "start_region": origin_region,
            "distance_km": distance_km,
            "estimated_duration_hours": estimated_duration_hours,
            "average_speed_kmh": average_speed_kmh,
            "template_distance_km": distance_km,
            "template_duration_hours": estimated_duration_hours,
            "total_distance_km": distance_km,
            "total_duration_hours": estimated_duration_hours,
            "approach_distance_km": None,
            "approach_duration_hours": None,
            "user_start_point": user_start_point,
            "template_start_point": template_start_point,
            "surface_type": route.get("surface_type"),
            "loop_type": route.get("loop_type"),
            "fact_source": "template",
            "fallback_reason": "route-provider-template-only",
        }

    def _resolve_local_user_start_point(self, constraints: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
        start_point = constraints.get("start_point") or route.get("start_point_name")
        if start_point in LOCAL_POINT_REGISTRY:
            known = LOCAL_POINT_REGISTRY[start_point]
            return {
                "name": start_point,
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


def _estimate_local_cycling_path(start_point: dict[str, Any], end_point: dict[str, Any]) -> dict[str, Any]:
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
        route_context = {
            "provider_name": self.provider_name,
            "start_region": self._extract_region(reverse_payload, constraints, route),
            "distance_km": total_distance_km,
            "estimated_duration_hours": total_duration_hours,
            "average_speed_kmh": round(total_distance_km / total_duration_hours, 1) if total_duration_hours else None,
            "template_distance_km": template_distance_km,
            "template_duration_hours": template_duration_hours,
            "total_distance_km": total_distance_km,
            "total_duration_hours": total_duration_hours,
            "approach_distance_km": approach_context["approach_distance_km"],
            "approach_duration_hours": approach_context["approach_duration_hours"],
            "user_start_point": user_start_point,
            "template_start_point": template_start_point,
            "surface_type": route.get("surface_type"),
            "loop_type": route.get("loop_type"),
            "fact_source": "template+amap",
            "start_location": user_start_point,
            "road_context": self._extract_road_context(reverse_payload),
            "approach_polyline": approach_context["approach_polyline"],
        }

        end_point_name = route.get("end_point_name")
        if end_point_name and end_point_name != route.get("start_point_name") and route.get("loop_type") != "loop":
            try:
                end_point = self._resolve_point(end_point_name, None, None, city_code=route.get("city_code", "hangzhou"))
                direction_payload = self._cycling_direction(template_start_point, end_point)
            except Exception:
                route_context["fact_source"] = "template+amap"
            else:
                normalized = self._normalize_direction(direction_payload)
                route_context["direction_summary"] = normalized["direction_summary"]
                route_context["polyline"] = [*approach_context["approach_polyline"], *normalized["polyline"]]
                route_context["fact_source"] = "amap"
        elif approach_context["approach_polyline"]:
            route_context["polyline"] = approach_context["approach_polyline"]

        return route_context

    def resolve_point(self, address: str, *, city_code: str) -> dict[str, Any]:
        return self._resolve_point(address, None, None, city_code=city_code)

    def get_cycling_path(self, start_point: dict[str, Any], end_point: dict[str, Any]) -> dict[str, Any]:
        try:
            path = self._normalize_direction(self._cycling_direction(start_point, end_point))
        except Exception:
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
