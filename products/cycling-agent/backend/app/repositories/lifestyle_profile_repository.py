"""CN: 生活方式偏好仓库，保存新前台所需的轻量用户画像。
EN: Lifestyle-profile repository for the new frontend's lightweight preference model.
"""

from __future__ import annotations

import json

from app.core.storage import connect


PROFILE_KEY = "default"


def get_lifestyle_profile(database_url: str) -> dict | None:
    with connect(database_url) as connection:
        row = connection.execute(
            "SELECT payload_json FROM lifestyle_profiles WHERE profile_key = ?",
            (PROFILE_KEY,),
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["payload_json"])


def save_lifestyle_profile(database_url: str, payload: dict) -> dict:
    normalized = {
        "home_region": payload.get("home_region"),
        "preferred_vibe": payload.get("preferred_vibe"),
        "companion_tone": payload.get("companion_tone"),
        "favorite_motifs": payload.get("favorite_motifs", []),
        "avoid_motifs": payload.get("avoid_motifs", []),
    }
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO lifestyle_profiles (profile_key, payload_json)
            VALUES (?, ?)
            ON CONFLICT(profile_key) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                PROFILE_KEY,
                json.dumps(normalized, ensure_ascii=False),
            ),
        )
    return normalized
