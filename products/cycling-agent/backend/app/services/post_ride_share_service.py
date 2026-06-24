"""CN: 骑后分享服务，编排完成骑行、图片落盘、风格化生成与分享文案。
EN: Post-ride share service for completed rides, photo storage, stylized generation, and share copy.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.core.ids import generate_business_no
from app.repositories.plan_result_repository import get_ride_plan
from app.repositories.post_ride_share_repository import (
    create_post_ride_share,
    find_post_ride_share_by_idempotency_key,
    get_completed_ride,
    get_completed_ride_by_request_no,
    get_media_asset,
    get_post_ride_share,
    save_completed_ride,
    save_media_asset,
    update_post_ride_share,
)
from app.repositories.user_profile_repository import DEFAULT_UID


ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def complete_ride_from_request(
    database_url: str,
    *,
    request_no: str,
    actual_duration_hours: float | None,
    actual_distance_km: float | None,
    selected_route_code: str | None,
    user_note: str | None,
    visibility_level: str,
) -> dict[str, Any] | None:
    existing = get_completed_ride_by_request_no(database_url, request_no)
    if existing is not None:
        return existing
    plan_payload = get_ride_plan(database_url, request_no)
    if plan_payload is None:
        return None
    resolved_route_code = selected_route_code or _infer_selected_route_code(plan_payload)
    return save_completed_ride(
        database_url,
        {
            "ride_no": generate_business_no("RD"),
            "request_no": request_no,
            "user_uid": DEFAULT_UID,
            "selected_route_code": resolved_route_code,
            "actual_duration_hours": actual_duration_hours,
            "actual_distance_km": actual_distance_km,
            "user_note": user_note,
            "visibility_level": visibility_level,
        },
    )


def store_ride_photo(
    database_url: str,
    *,
    media_storage,
    ride_no: str,
    file_bytes: bytes,
    mime_type: str,
) -> dict[str, Any] | None:
    ride = get_completed_ride(database_url, ride_no)
    if ride is None:
        return None
    asset_no = generate_business_no("AS")
    extension = _extension_for_mime_type(mime_type)
    storage_object = media_storage.save_bytes(
        storage_key=f"rides/{ride_no}/{asset_no}.{extension}",
        payload=file_bytes,
    )
    asset = save_media_asset(
        database_url,
        {
            "asset_no": asset_no,
            "owner_type": "completed_ride",
            "owner_no": ride_no,
            "storage_key": storage_object.storage_key,
            "mime_type": mime_type,
            "file_size_bytes": storage_object.file_size_bytes,
            "status": "uploaded",
        },
    )
    asset["original_url"] = storage_object.public_url
    return asset


def generate_post_ride_share(
    database_url: str,
    *,
    ride_no: str,
    asset_no: str,
    style_preset: str,
    caption_tone: str,
    channel_targets: list[str],
    include_route_context: bool,
    regenerate: bool,
    media_storage,
    image_provider,
    llm_provider,
) -> dict[str, Any] | None:
    ride = get_completed_ride(database_url, ride_no)
    asset = get_media_asset(database_url, asset_no)
    if ride is None:
        raise RuntimeError("experience-share-ride-not-found")
    if asset is None:
        raise RuntimeError("experience-share-asset-not-found")
    if asset["owner_type"] != "completed_ride" or asset["owner_no"] != ride_no:
        raise RuntimeError("experience-share-asset-not-found")
    idempotency_key = _build_idempotency_key(
        ride_no=ride_no,
        asset_no=asset_no,
        style_preset=style_preset,
        caption_tone=caption_tone,
        channel_targets=channel_targets,
        regenerate=regenerate,
    )
    if not regenerate:
        existing = find_post_ride_share_by_idempotency_key(database_url, idempotency_key)
        if existing is not None:
            return _normalize_share(existing)

    share = create_post_ride_share(
        database_url,
        {
            "share_no": generate_business_no("SH"),
            "ride_no": ride_no,
            "asset_no": asset_no,
            "styled_asset_no": None,
            "style_preset": style_preset,
            "caption_tone": caption_tone,
            "channel_targets": channel_targets,
            "status": "processing",
            "stage": "load_context",
            "provider_name": getattr(image_provider, "provider_name", None),
            "idempotency_key": idempotency_key,
            "context": None,
            "prompt": None,
            "result_payload": None,
            "error_code": None,
        },
    )
    try:
        context = _build_share_context(database_url, ride=ride, include_route_context=include_route_context)
        share = update_post_ride_share(
            database_url,
            share["share_no"],
            {
                "context": context,
                "stage": "generate_style_image",
                "status": "processing",
            },
        )
        if image_provider is None:
            raise RuntimeError("image-provider-missing")
        prompt = {
            "image_prompt": _build_image_prompt(context=context, style_preset=style_preset),
            "copy_prompt": {
                "caption_tone": caption_tone,
                "channel_targets": channel_targets,
            },
        }
        source_bytes = media_storage.read_bytes(asset["storage_key"])
        generated = image_provider.edit_ride_photo(
            image_bytes=source_bytes,
            image_mime_type=asset["mime_type"],
            prompt=prompt["image_prompt"],
        )
        styled_asset_no = generate_business_no("AS")
        styled_extension = _extension_for_mime_type(generated["mime_type"])
        styled_object = media_storage.save_bytes(
            storage_key=f"shares/{share['share_no']}/{styled_asset_no}.{styled_extension}",
            payload=generated["image_bytes"],
        )
        save_media_asset(
            database_url,
            {
                "asset_no": styled_asset_no,
                "owner_type": "post_ride_share",
                "owner_no": share["share_no"],
                "storage_key": styled_object.storage_key,
                "mime_type": generated["mime_type"],
                "file_size_bytes": styled_object.file_size_bytes,
                "status": "ready",
            },
        )
        copy_variants = _generate_copy_variants(
            llm_provider=llm_provider,
            ride_context=context,
            style_preset=style_preset,
            caption_tone=caption_tone,
            channel_targets=channel_targets,
        )
        share = update_post_ride_share(
            database_url,
            share["share_no"],
            {
                "styled_asset_no": styled_asset_no,
                "stage": "done",
                "status": "succeeded",
                "prompt": prompt,
                "provider_name": getattr(image_provider, "provider_name", None),
                "result_payload": {
                    "styled_image_url": styled_object.public_url,
                    "copy_variants": copy_variants,
                },
                "error_code": None,
            },
        )
        return _normalize_share(share)
    except Exception:
        failed = update_post_ride_share(
            database_url,
            share["share_no"],
            {
                "status": "failed",
                "stage": "done",
                "error_code": "experience-share-generation-failed",
            },
        )
        return _normalize_share(failed)


def get_post_ride_share_result(database_url: str, *, share_no: str) -> dict[str, Any] | None:
    share = get_post_ride_share(database_url, share_no)
    if share is None:
        return None
    return _normalize_share(share)


def _infer_selected_route_code(plan_payload: dict[str, Any]) -> str | None:
    if plan_payload.get("recommended_plan"):
        return plan_payload["recommended_plan"].get("route_code")
    if plan_payload.get("recommended_trip"):
        return plan_payload["recommended_trip"].get("trip_no")
    return None


def _build_share_context(database_url: str, *, ride: dict[str, Any], include_route_context: bool) -> dict[str, Any]:
    plan_payload = get_ride_plan(database_url, ride["request_no"])
    if plan_payload is None:
        return {
            "request_no": ride["request_no"],
            "user_note": ride.get("user_note"),
            "selected_route_code": ride.get("selected_route_code"),
        }
    context = {
        "request_no": ride["request_no"],
        "selected_route_code": ride.get("selected_route_code"),
        "user_note": ride.get("user_note"),
        "actual_duration_hours": ride.get("actual_duration_hours"),
        "actual_distance_km": ride.get("actual_distance_km"),
        "visibility_level": ride.get("visibility_level"),
        "decision_summary": plan_payload.get("decision_summary") or {},
        "weather_snapshot": plan_payload.get("weather_snapshot") or {},
    }
    if include_route_context:
        context["recommended_plan"] = plan_payload.get("recommended_plan") or plan_payload.get("recommended_trip") or {}
    return context


def _build_image_prompt(*, context: dict[str, Any], style_preset: str) -> str:
    preset_fragments = {
        "anime_sky_glow": "明亮天空、柔和逆光、轻盈的骑行旅途氛围",
        "warm_journal": "温暖手账质感、生活方式摄影、轻松真实",
        "sunset_film": "傍晚胶片感、金色日落、城市慢骑节奏",
        "city_minimal": "克制干净、都市留白、简洁高级的骑行画面",
    }
    summary_parts = [
        context.get("selected_route_code") or "",
        (context.get("decision_summary") or {}).get("decision_reason") or "",
        context.get("user_note") or "",
    ]
    summary = " ".join(part for part in summary_parts if part).strip()
    return (
        "基于用户上传的真实骑行照片做风格化处理，保留人物/单车/环境主体，"
        f"整体视觉方向为：{preset_fragments[style_preset]}。"
        f"已知骑行上下文：{summary or '一次轻松的城市骑行'}。"
        "不要添加文字水印，不要杜撰地标。"
    )


def _generate_copy_variants(
    *,
    llm_provider,
    ride_context: dict[str, Any],
    style_preset: str,
    caption_tone: str,
    channel_targets: list[str],
) -> dict[str, Any]:
    if llm_provider is not None:
        try:
            payload = llm_provider.generate_post_ride_share_copy(
                ride_context=ride_context,
                style_preset=style_preset,
                caption_tone=caption_tone,
                channel_targets=channel_targets,
            )
            if isinstance(payload.get("copy_variants"), dict):
                return payload["copy_variants"]
        except Exception:
            pass
    return _fallback_copy_variants(
        ride_context=ride_context,
        caption_tone=caption_tone,
        channel_targets=channel_targets,
    )


def _fallback_copy_variants(*, ride_context: dict[str, Any], caption_tone: str, channel_targets: list[str]) -> dict[str, Any]:
    note = ride_context.get("user_note") or "今天把节奏放慢了一点。"
    route = (ride_context.get("recommended_plan") or {}).get("route_name") or "这段骑行"
    prefix = {
        "gentle": "今天的风刚刚好。",
        "editorial": "把城市留给傍晚，把自己留给骑行。",
        "playful": "今日份骑行打卡完成。",
    }[caption_tone]
    variants: dict[str, Any] = {}
    if "xiaohongshu" in channel_targets:
        variants["xiaohongshu"] = {
            "title": prefix,
            "body": f"{route}结束之后，最想记住的是这张照片。{note}",
            "hashtags": ["#城市骑行", "#骑行日记", "#慢骑一下"],
        }
    if "moments" in channel_targets:
        variants["moments"] = {
            "body": f"{prefix} {note}",
        }
    return variants


def _build_idempotency_key(
    *,
    ride_no: str,
    asset_no: str,
    style_preset: str,
    caption_tone: str,
    channel_targets: list[str],
    regenerate: bool,
) -> str:
    if regenerate:
        return generate_business_no("IK")
    digest = hashlib.sha1(
        json.dumps(
            {
                "ride_no": ride_no,
                "asset_no": asset_no,
                "style_preset": style_preset,
                "caption_tone": caption_tone,
                "channel_targets": sorted(channel_targets),
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return f"share-{digest}"


def _extension_for_mime_type(mime_type: str) -> str:
    mapping = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    return mapping.get(mime_type, "bin")


def _normalize_share(share: dict[str, Any]) -> dict[str, Any]:
    result_payload = share.get("result_payload") or {}
    return {
        "share_no": share["share_no"],
        "ride_no": share["ride_no"],
        "asset_no": share["asset_no"],
        "status": share["status"],
        "stage": share["stage"],
        "poll_url": f"/api/v1/experience/post-ride-shares/{share['share_no']}",
        "styled_image_url": result_payload.get("styled_image_url"),
        "copy_variants": result_payload.get("copy_variants", {}),
        "error_code": share.get("error_code"),
    }
