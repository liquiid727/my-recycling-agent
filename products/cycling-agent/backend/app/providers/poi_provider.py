"""CN: POI provider 抽象，支持本地补给/撤退点事实与高德周边搜索适配。
EN: POI provider abstraction for local supply/bailout facts and AMap place-around adaptation.
"""

from __future__ import annotations

from typing import Any, Callable

import httpx


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
