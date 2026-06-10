"""CN: 用户画像仓库，保存默认骑行能力、坡度容忍和偏好风格。
EN: User profile repository for default fitness, slope tolerance, and ride-style preferences.
"""

from __future__ import annotations

import json

from app.core.ids import generate_uuid_v7_like
from app.core.storage import connect


DEFAULT_UID = "00000001"


def get_default_user_profile(database_url: str) -> dict | None:
    with connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT id, uid, nickname, home_region, fitness_level, ride_style_preferences_json, slope_tolerance
            FROM user_profiles
            WHERE uid = ?
            """,
            (DEFAULT_UID,),
        ).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "uid": row["uid"],
        "nickname": row["nickname"],
        "home_region": row["home_region"],
        "fitness_level": row["fitness_level"],
        "ride_style_preferences": json.loads(row["ride_style_preferences_json"]),
        "slope_tolerance": row["slope_tolerance"],
    }


def save_default_user_profile(database_url: str, payload: dict) -> dict:
    existing = get_default_user_profile(database_url)
    normalized = {
        "id": existing["id"] if existing else generate_uuid_v7_like(),
        "uid": DEFAULT_UID,
        "nickname": payload.get("nickname"),
        "home_region": payload.get("home_region"),
        "fitness_level": payload.get("fitness_level"),
        "ride_style_preferences": payload.get("ride_style_preferences", []),
        "slope_tolerance": payload.get("slope_tolerance"),
    }
    with connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO user_profiles (
                id, uid, nickname, home_region, fitness_level, ride_style_preferences_json, slope_tolerance
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uid) DO UPDATE SET
                nickname = excluded.nickname,
                home_region = excluded.home_region,
                fitness_level = excluded.fitness_level,
                ride_style_preferences_json = excluded.ride_style_preferences_json,
                slope_tolerance = excluded.slope_tolerance,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                normalized["id"],
                normalized["uid"],
                normalized["nickname"],
                normalized["home_region"],
                normalized["fitness_level"],
                json.dumps(normalized["ride_style_preferences"], ensure_ascii=False),
                normalized["slope_tolerance"],
            ),
        )
    return normalized
