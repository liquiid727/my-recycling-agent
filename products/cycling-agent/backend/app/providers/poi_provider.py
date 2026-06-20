"""CN: POI provider 抽象，支持本地补给/撤退点事实与高德周边搜索适配。
EN: POI provider abstraction for local supply/bailout facts and AMap place-around adaptation.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any, Callable

import httpx


LOCAL_ROUTE_ANCHORS: list[dict[str, Any]] = [
    {"name": "运河亚运公园", "type": "公园", "address": "拱墅区", "longitude": 120.1450, "latitude": 30.3100, "district": "拱墅"},
    {"name": "市民公园", "type": "公园", "address": "拱墅区", "longitude": 120.1560, "latitude": 30.2740, "district": "拱墅"},
    {"name": "朝晖文化公园", "type": "公园", "address": "拱墅区", "longitude": 120.1650, "latitude": 30.2870, "district": "拱墅"},
    {"name": "大兜路历史街区", "type": "景点", "address": "拱墅区", "longitude": 120.1510, "latitude": 30.3080, "district": "拱墅"},
    {"name": "西湖文化广场", "type": "广场", "address": "拱墅区", "longitude": 120.1659, "latitude": 30.2798, "district": "拱墅"},
    {"name": "钱塘江城市阳台", "type": "水系", "address": "上城区", "longitude": 120.2140, "latitude": 30.2410, "district": "上城"},
    {"name": "闻涛路滨江段", "type": "绿道", "address": "滨江区", "longitude": 120.2103, "latitude": 30.2064, "district": "滨江"},
    {"name": "湘湖游客中心", "type": "湖", "address": "萧山区", "longitude": 120.2525, "latitude": 30.1545, "district": "萧山"},
]
LOCAL_POI_RADIUS_KM = 12.0


class LocalPoiProvider:
    provider_name = "local-poi-stub"

    def get_poi_context(self, route: dict[str, Any]) -> dict[str, Any]:
        supply_points = route.get("supply_points", [])
        bailout_options = route.get("bailout_options", [])
        poi_labels = [f"{point['name']}({point['type']})" for point in supply_points[:3]]
        bailout_labels = [option["name"] for option in bailout_options[:2]]
        return {
            "provider_name": self.provider_name,
            "poi_summary": {
                "supply_count": len(supply_points),
                "bailout_count": len(bailout_options),
                "supply_labels": poi_labels,
                "bailout_labels": bailout_labels,
                "fact_source": "template",
            },
        }

    def search_route_anchors(
        self,
        *,
        longitude: float,
        latitude: float,
        city_code: str,
        ride_style: str | None = None,
    ) -> list[dict[str, Any]]:
        anchors = []
        for anchor in LOCAL_ROUTE_ANCHORS:
            distance_km = _haversine_km(longitude, latitude, float(anchor["longitude"]), float(anchor["latitude"]))
            if distance_km > LOCAL_POI_RADIUS_KM:
                continue
            anchors.append({**anchor, "distance_km": round(distance_km, 2)})
        return sorted(anchors, key=lambda item: (_local_anchor_rank(item, ride_style), -item["distance_km"]), reverse=True)


class AMapPoiProvider:
    provider_name = "amap-poi"

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

    def get_poi_context(self, route: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("amap-poi-provider-missing-key")
        longitude = route.get("start_point_lng")
        latitude = route.get("start_point_lat")
        if longitude is None or latitude is None:
            raise RuntimeError("amap-poi-provider-missing-start-point")

        pois = self._search_poi(longitude=float(longitude), latitude=float(latitude))
        return {
            "provider_name": self.provider_name,
            "poi_summary": {
                "supply_count": len(pois),
                "bailout_count": len(route.get("bailout_options", [])),
                "supply_labels": [f"{poi['name']}({poi['type']})" for poi in pois[:3]],
                "bailout_labels": [option["name"] for option in route.get("bailout_options", [])[:2]],
                "fact_source": "amap",
            },
            "poi_items": pois,
        }

    def search_route_anchors(
        self,
        *,
        longitude: float,
        latitude: float,
        city_code: str,
        ride_style: str | None = None,
    ) -> list[dict[str, Any]]:
        keywords = "公园|绿地|风景区|运河|河道|湖|咖啡店" if ride_style == "scenic_relaxed" else "公园|绿地|风景区|运河|河道|湖|商圈|咖啡店"
        response = self.http_get(
            f"{self.base_url}/v5/place/around",
            params={
                "key": self.api_key,
                "location": f"{longitude},{latitude}",
                "keywords": keywords,
                "radius": 12000,
                "page_size": 25,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "1":
            raise RuntimeError("amap-route-anchor-empty")
        anchors = []
        for poi in payload.get("pois", []):
            location = poi.get("location")
            if not poi.get("name") or not location or "," not in location:
                continue
            longitude_text, latitude_text = location.split(",", 1)
            anchor_type = _normalize_anchor_type(poi.get("type"))
            anchors.append(
                {
                    "name": poi.get("name"),
                    "type": anchor_type,
                    "address": poi.get("address"),
                    "longitude": float(longitude_text),
                    "latitude": float(latitude_text),
                }
            )
        return anchors[:20]

    def _search_poi(self, *, longitude: float, latitude: float) -> list[dict[str, Any]]:
        response = self.http_get(
            f"{self.base_url}/v5/place/around",
            params={
                "key": self.api_key,
                "location": f"{longitude},{latitude}",
                "keywords": "便利店|咖啡店|卫生间|医院",
                "radius": 3000,
                "page_size": 10,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "1":
            raise RuntimeError("amap-poi-empty")
        pois = payload.get("pois", [])
        return [
            {
                "name": poi.get("name"),
                "type": _normalize_poi_type(poi.get("type")),
                "address": poi.get("address"),
                "location": poi.get("location"),
            }
            for poi in pois[:5]
            if poi.get("name")
        ]


def _normalize_poi_type(raw_type: str | None) -> str:
    if not raw_type:
        return "POI"
    if "便利" in raw_type:
        return "便利店"
    if "咖啡" in raw_type:
        return "咖啡店"
    if "卫生" in raw_type:
        return "卫生间"
    if "医院" in raw_type or "医疗" in raw_type:
        return "医院"
    return raw_type.split(";")[0]


def _local_anchor_rank(anchor: dict[str, Any], ride_style: str | None) -> int:
    anchor_text = f"{anchor.get('name', '')}{anchor.get('type', '')}"
    rank = 0
    if any(token in anchor_text for token in ("公园", "绿道", "湖", "河", "运河", "水系")):
        rank += 3
    if any(token in anchor_text for token in ("景点", "广场")):
        rank += 2
    if ride_style == "scenic_relaxed" and any(token in anchor_text for token in ("公园", "绿道", "湖", "河")):
        rank += 2
    return rank


def _haversine_km(start_lng: float, start_lat: float, end_lng: float, end_lat: float) -> float:
    radius_km = 6371.0
    delta_lat = radians(end_lat - start_lat)
    delta_lng = radians(end_lng - start_lng)
    lat1 = radians(start_lat)
    lat2 = radians(end_lat)
    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lng / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def _normalize_anchor_type(raw_type: str | None) -> str:
    if not raw_type:
        return "POI"
    if "公园" in raw_type or "绿地" in raw_type:
        return "公园"
    if "风景" in raw_type or "景点" in raw_type:
        return "景点"
    if "河" in raw_type or "湖" in raw_type or "运河" in raw_type:
        return "水系"
    if "咖啡" in raw_type:
        return "咖啡店"
    if "购物" in raw_type or "商圈" in raw_type:
        return "商圈"
    return raw_type.split(";")[0]
