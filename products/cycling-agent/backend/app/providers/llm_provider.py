"""CN: OpenAI-compatible LLM provider，供查询解析和路书生成在配置可用时调用。
EN: OpenAI-compatible LLM provider used by query parsing and roadbook generation when configured.
"""

from __future__ import annotations

import base64
import json
import re
from typing import Any, Callable

import httpx

from app.agents.query_parser_agent import parse_query_fallback


class OpenAICompatibleLLMProvider:
    provider_name = "openai-compatible-llm"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        thinking: str | None = None,
        http_post: Callable[..., Any] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.thinking = thinking
        self.timeout_seconds = timeout_seconds
        self.http_post = http_post or httpx.post

    def parse_query(self, *, query: str, user_profile: dict | None = None) -> dict[str, Any]:
        payload = self._chat_completion(
            system_prompt=(
                "你是骑行查询解析器。只输出 JSON。"
                "不得虚构天气、路线、POI、距离事实。"
                "信息不足时保留 null，并写入 missing_fields。"
                "输出顶层必须只包含这些键：origin_region、available_hours、ride_style、missing_fields、confidence。"
                "其中 ride_style 只能是 scenic_relaxed、training_loop、climb、general 之一。"
            ),
            user_prompt=json.dumps({"query": query, "user_profile": user_profile or {}}, ensure_ascii=False),
        )
        return self._normalize_parsed_query(json.loads(payload), query=query)

    def generate_roadbook(self, *, route: dict[str, Any], risk: dict[str, Any], parsed_constraints: dict[str, Any]) -> dict[str, Any]:
        payload = self._chat_completion(
            system_prompt=(
                "你是骑行建议解释器。只输出 JSON。"
                "只能使用已给出的结构化事实，不得新增不存在的天气、路线细节、POI 或时间结论。"
            ),
            user_prompt=json.dumps(
                {"route": route, "risk": risk, "parsed_constraints": parsed_constraints},
                ensure_ascii=False,
            ),
        )
        return json.loads(payload)

    def generate_chat_turn(
        self,
        *,
        messages: list[dict],
        slot_state: dict,
        planning_scene: str,
        target_date,
        user_profile: dict | None = None,
    ) -> dict[str, Any]:
        payload = self._chat_completion(
            system_prompt=(
                "你是 AAA骑车帮帮，一个熟悉杭州及周边骑行的 C 端私人骑行助手。"
                "用亲切、直接、像朋友的口吻回复。不要说 missing_fields、字段、约束、解析等工程词。"
                "你只能理解用户意图、提取槽位、追问关键信息；不得虚构天气、路线、补给点、住宿事实。"
                "只输出 JSON，键包括 assistant_message、slot_state、missing_slots、ready_to_plan、confidence。"
                "slot_state 只能包含 planning_scene、start_point、available_hours、target_distance_km、departure_time、"
                "duration_bucket、ride_style、slope_tolerance、destination_preferences、overnight_preference、"
                "lodging_preference、cross_city_allowed、origin_region。"
            ),
            user_prompt=json.dumps(
                {
                    "messages": messages,
                    "slot_state": slot_state,
                    "planning_scene": planning_scene,
                    "target_date": str(target_date),
                    "user_profile": user_profile or {},
                },
                ensure_ascii=False,
            ),
        )
        return json.loads(payload)

    def generate_post_ride_share_copy(
        self,
        *,
        ride_context: dict[str, Any],
        style_preset: str,
        caption_tone: str,
        channel_targets: list[str],
    ) -> dict[str, Any]:
        payload = self._chat_completion(
            system_prompt=(
                "你是骑后分享文案助手。只输出 JSON。"
                "只能使用已提供的骑行事实、路线摘要和用户备注。"
                "不得虚构距离、天气、成就、同行人、具体住址。"
                "输出顶层只包含 copy_variants。"
                "copy_variants 可包含 xiaohongshu 和 moments。"
            ),
            user_prompt=json.dumps(
                {
                    "ride_context": ride_context,
                    "style_preset": style_preset,
                    "caption_tone": caption_tone,
                    "channel_targets": channel_targets,
                },
                ensure_ascii=False,
            ),
        )
        return json.loads(payload)

    def _chat_completion(self, *, system_prompt: str, user_prompt: str) -> str:
        request_body = {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.thinking:
            request_body["thinking"] = {"type": self.thinking}

        response = self.http_post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=request_body,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]

    def _normalize_parsed_query(self, parsed: dict[str, Any], *, query: str) -> dict[str, Any]:
        source = parsed.get("parsed_query") if isinstance(parsed.get("parsed_query"), dict) else parsed
        fallback = parse_query_fallback(query)

        origin_region = self._pick_first_string(
            source,
            "origin_region",
            "departure_place",
            "departure_region",
            "start_region",
            "starting_area",
            "origin",
        )
        available_hours = self._coerce_float(
            self._pick_first_value(
                source,
                "available_hours",
                "duration_hours",
                "planned_hours",
                "available_time_hours",
                "hours",
            )
        )
        ride_style = self._normalize_ride_style(
            self._pick_first_string(
                source,
                "ride_style",
                "style_preference",
                "ride_preference",
                "riding_style",
            )
        )

        if ride_style is None:
            ride_style = self._infer_ride_style(source)
        if origin_region is None:
            origin_region = fallback.get("origin_region")
        if available_hours is None:
            available_hours = fallback.get("available_hours")
        if ride_style is None:
            ride_style = fallback.get("ride_style")

        normalized = {
            "origin_region": origin_region,
            "available_hours": available_hours,
            "ride_style": ride_style,
            "missing_fields": self._normalize_missing_fields(parsed.get("missing_fields", [])),
            "confidence": self._coerce_confidence(parsed.get("confidence")),
        }

        if normalized["origin_region"] is not None:
            normalized["missing_fields"] = [
                item for item in normalized["missing_fields"] if item != "origin_region"
            ]
        if normalized["available_hours"] is not None:
            normalized["missing_fields"] = [
                item for item in normalized["missing_fields"] if item != "available_hours"
            ]
        if normalized["origin_region"] is None and "origin_region" not in normalized["missing_fields"]:
            normalized["missing_fields"].append("origin_region")
        if normalized["available_hours"] is None and "available_hours" not in normalized["missing_fields"]:
            normalized["missing_fields"].append("available_hours")

        return normalized

    def _pick_first_string(self, source: dict[str, Any], *keys: str) -> str | None:
        value = self._pick_first_value(source, *keys)
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _pick_first_value(self, source: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            value = source.get(key)
            if value not in (None, ""):
                return value
        return None

    def _coerce_float(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            match = re.search(r"\d+(?:\.\d+)?", value)
            if match:
                return float(match.group(0))
        return None

    def _coerce_confidence(self, value: Any) -> float:
        parsed = self._coerce_float(value)
        if parsed is None:
            return 0.75
        return max(0.0, min(parsed, 1.0))

    def _normalize_missing_fields(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []

        aliases = {
            "departure_place": "origin_region",
            "departure_region": "origin_region",
            "start_region": "origin_region",
            "starting_area": "origin_region",
            "duration_hours": "available_hours",
            "planned_hours": "available_hours",
            "available_time_hours": "available_hours",
            "hours": "available_hours",
        }
        allowed = {"origin_region", "available_hours", "ride_style"}
        normalized: list[str] = []
        for item in value:
            if item is None:
                continue
            mapped = aliases.get(str(item), str(item))
            if mapped in allowed and mapped not in normalized:
                normalized.append(mapped)
        return normalized

    def _normalize_ride_style(self, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        alias_map = {
            "scenic": "scenic_relaxed",
            "relaxed": "scenic_relaxed",
            "leisure": "scenic_relaxed",
            "easy": "scenic_relaxed",
            "scenic_relaxed": "scenic_relaxed",
            "training": "training_loop",
            "training_loop": "training_loop",
            "loop": "training_loop",
            "climb": "climb",
            "climbing": "climb",
            "general": "general",
        }
        if normalized in alias_map:
            return alias_map[normalized]

        raw_lower = value.lower()
        if any(keyword in raw_lower for keyword in ("风景", "轻松", "休闲", "relax", "scenic")):
            return "scenic_relaxed"
        if any(keyword in raw_lower for keyword in ("爬坡", "climb")):
            return "climb"
        if any(keyword in raw_lower for keyword in ("训练", "刷圈", "interval", "training")):
            return "training_loop"
        return "general"

    def _infer_ride_style(self, source: dict[str, Any]) -> str | None:
        combined = " ".join(str(value) for value in source.values() if isinstance(value, (str, int, float)))
        if not combined:
            return None
        return self._normalize_ride_style(combined)


class OpenAICompatibleImageProvider:
    provider_name = "openai-compatible-image"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        http_post: Callable[..., Any] | None = None,
        http_get: Callable[..., Any] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.http_post = http_post or httpx.post
        self.http_get = http_get or httpx.get

    def edit_ride_photo(
        self,
        *,
        image_bytes: bytes,
        image_mime_type: str,
        prompt: str,
        size: str = "1024x1024",
    ) -> dict[str, Any]:
        extension = _mime_type_to_extension(image_mime_type)
        response = self.http_post(
            f"{self.base_url}/images/edits",
            headers={"Authorization": f"Bearer {self.api_key}"},
            data={
                "model": self.model,
                "prompt": prompt,
                "size": size,
            },
            files={
                "image": (f"ride-photo.{extension}", image_bytes, image_mime_type),
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        item = (payload.get("data") or [{}])[0]
        if item.get("b64_json"):
            return {
                "image_bytes": base64.b64decode(item["b64_json"]),
                "mime_type": "image/png",
                "provider_payload": payload,
            }
        if item.get("url"):
            image_response = self.http_get(item["url"], timeout=self.timeout_seconds)
            image_response.raise_for_status()
            return {
                "image_bytes": image_response.content,
                "mime_type": image_response.headers.get("Content-Type", "image/png"),
                "provider_payload": payload,
            }
        raise RuntimeError("image-generation-empty-payload")


def _mime_type_to_extension(mime_type: str) -> str:
    mapping = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    return mapping.get(mime_type, "png")
