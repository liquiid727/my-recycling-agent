"""CN: 骑后分享仓库，保存完成骑行、媒体资产和生成结果。
EN: Post-ride share repository for completed rides, media assets, and generation records.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.storage import connect


def save_completed_ride(database_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_completed_ride_by_request_no(database_url, payload["request_no"])
    normalized = dict(payload)
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO completed_rides (
                ride_no, request_no, user_uid, selected_route_code, actual_duration_hours,
                actual_distance_km, user_note, visibility_level
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(request_no) DO UPDATE SET
                user_uid = excluded.user_uid,
                selected_route_code = excluded.selected_route_code,
                actual_duration_hours = excluded.actual_duration_hours,
                actual_distance_km = excluded.actual_distance_km,
                user_note = excluded.user_note,
                visibility_level = excluded.visibility_level
            """,
            (
                normalized["ride_no"],
                normalized["request_no"],
                normalized["user_uid"],
                normalized.get("selected_route_code"),
                normalized.get("actual_duration_hours"),
                normalized.get("actual_distance_km"),
                normalized.get("user_note"),
                normalized["visibility_level"],
            ),
        )
    return get_completed_ride(database_url, normalized["ride_no"]) or normalized


def get_completed_ride(database_url: str, ride_no: str) -> dict[str, Any] | None:
    with connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT ride_no, request_no, user_uid, selected_route_code, actual_duration_hours,
                   actual_distance_km, user_note, visibility_level, created_at
            FROM completed_rides
            WHERE ride_no = ?
            """,
            (ride_no,),
        ).fetchone()
    return None if row is None else dict(row)


def get_completed_ride_by_request_no(database_url: str, request_no: str) -> dict[str, Any] | None:
    with connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT ride_no, request_no, user_uid, selected_route_code, actual_duration_hours,
                   actual_distance_km, user_note, visibility_level, created_at
            FROM completed_rides
            WHERE request_no = ?
            """,
            (request_no,),
        ).fetchone()
    return None if row is None else dict(row)


def save_media_asset(database_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO media_assets (
                asset_no, owner_type, owner_no, storage_key, mime_type, file_size_bytes, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["asset_no"],
                payload["owner_type"],
                payload["owner_no"],
                payload["storage_key"],
                payload["mime_type"],
                payload["file_size_bytes"],
                payload["status"],
            ),
        )
    return get_media_asset(database_url, payload["asset_no"]) or payload


def get_media_asset(database_url: str, asset_no: str) -> dict[str, Any] | None:
    with connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT asset_no, owner_type, owner_no, storage_key, mime_type, file_size_bytes, status, created_at
            FROM media_assets
            WHERE asset_no = ?
            """,
            (asset_no,),
        ).fetchone()
    return None if row is None else dict(row)


def create_post_ride_share(database_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO post_ride_shares (
                share_no, ride_no, asset_no, styled_asset_no, style_preset, caption_tone, channel_targets_json,
                status, stage, provider_name, idempotency_key, context_json, prompt_json, result_payload_json,
                error_code
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["share_no"],
                payload["ride_no"],
                payload["asset_no"],
                payload.get("styled_asset_no"),
                payload["style_preset"],
                payload["caption_tone"],
                json.dumps(payload.get("channel_targets", []), ensure_ascii=False),
                payload["status"],
                payload["stage"],
                payload.get("provider_name"),
                payload["idempotency_key"],
                json.dumps(payload.get("context"), ensure_ascii=False) if payload.get("context") is not None else None,
                json.dumps(payload.get("prompt"), ensure_ascii=False) if payload.get("prompt") is not None else None,
                json.dumps(payload.get("result_payload"), ensure_ascii=False) if payload.get("result_payload") is not None else None,
                payload.get("error_code"),
            ),
        )
    return get_post_ride_share(database_url, payload["share_no"]) or payload


def update_post_ride_share(database_url: str, share_no: str, patch: dict[str, Any]) -> dict[str, Any]:
    existing = get_post_ride_share(database_url, share_no)
    if existing is None:
        raise RuntimeError("post-ride-share-not-found")
    merged = dict(existing)
    merged.update(patch)
    with connect(database_url) as connection:
        connection.execute(
            """
            UPDATE post_ride_shares
            SET styled_asset_no = ?,
                status = ?,
                stage = ?,
                provider_name = ?,
                context_json = ?,
                prompt_json = ?,
                result_payload_json = ?,
                error_code = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE share_no = ?
            """,
            (
                merged.get("styled_asset_no"),
                merged["status"],
                merged["stage"],
                merged.get("provider_name"),
                json.dumps(merged.get("context"), ensure_ascii=False) if merged.get("context") is not None else None,
                json.dumps(merged.get("prompt"), ensure_ascii=False) if merged.get("prompt") is not None else None,
                json.dumps(merged.get("result_payload"), ensure_ascii=False) if merged.get("result_payload") is not None else None,
                merged.get("error_code"),
                share_no,
            ),
        )
    return get_post_ride_share(database_url, share_no) or merged


def find_post_ride_share_by_idempotency_key(database_url: str, idempotency_key: str) -> dict[str, Any] | None:
    with connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT share_no
            FROM post_ride_shares
            WHERE idempotency_key = ?
            """,
            (idempotency_key,),
        ).fetchone()
    if row is None:
        return None
    return get_post_ride_share(database_url, row["share_no"])


def get_post_ride_share(database_url: str, share_no: str) -> dict[str, Any] | None:
    with connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT share_no, ride_no, asset_no, styled_asset_no, style_preset, caption_tone, channel_targets_json,
                   status, stage, provider_name, idempotency_key, context_json, prompt_json, result_payload_json,
                   error_code, created_at, updated_at
            FROM post_ride_shares
            WHERE share_no = ?
            """,
            (share_no,),
        ).fetchone()
    if row is None:
        return None
    return {
        **dict(row),
        "channel_targets": json.loads(row["channel_targets_json"]),
        "context": json.loads(row["context_json"]) if row["context_json"] else None,
        "prompt": json.loads(row["prompt_json"]) if row["prompt_json"] else None,
        "result_payload": json.loads(row["result_payload_json"]) if row["result_payload_json"] else {},
    }
