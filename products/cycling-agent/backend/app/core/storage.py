"""CN: PostgreSQL 存储初始化与兼容层，统一连接、建表与轻量迁移。
EN: PostgreSQL storage initialization and compatibility layer for connections, schemas, and migrations.
"""

from __future__ import annotations

import re
from typing import Any


POSTGRES_SCHEMAS = ("postgres://", "postgresql://")


def database_kind(database_url: str) -> str:
    if database_url.startswith(POSTGRES_SCHEMAS):
        return "postgres"
    raise ValueError(f"cycling-agent-postgres-required:{database_url}")


def connect(database_url: str):
    database_kind(database_url)
    return _connect_postgres(database_url)


def init_storage(database_url: str) -> None:
    with connect(database_url) as connection:
        for statement in _postgres_statements():
            connection.execute(statement)
        _apply_compatible_migrations(connection)


class PostgresConnectionAdapter:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def execute(self, query: str, params: tuple[Any, ...] | list[Any] | None = None):
        cursor = self._connection.cursor()
        cursor.execute(_translate_query_for_postgres(query), tuple(params or ()))
        return PostgresCursorAdapter(cursor)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self._connection.commit()
        else:
            self._connection.rollback()
        self._connection.close()


class PostgresCursorAdapter:
    def __init__(self, cursor: Any) -> None:
        self._cursor = cursor

    def fetchone(self):
        row = self._cursor.fetchone()
        return None if row is None else dict(row)

    def fetchall(self):
        return [dict(row) for row in self._cursor.fetchall()]


def _connect_postgres(database_url: str):
    try:
        from psycopg import connect as psycopg_connect
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError("postgres-driver-not-installed") from exc
    return PostgresConnectionAdapter(psycopg_connect(database_url, row_factory=dict_row))


def _translate_query_for_postgres(query: str) -> str:
    return re.sub(r"\?", "%s", query)


def _postgres_statements() -> list[str]:
    return [
        """
        CREATE TABLE IF NOT EXISTS ride_plans (
            request_no TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id TEXT PRIMARY KEY,
            uid TEXT NOT NULL UNIQUE,
            nickname TEXT,
            home_region TEXT,
            fitness_level TEXT,
            ride_style_preferences_json TEXT NOT NULL,
            slope_tolerance TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS route_templates (
            route_code TEXT PRIMARY KEY,
            city_code TEXT NOT NULL,
            district_tags_json TEXT NOT NULL,
            ride_style_tags_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS city_strategy_configs (
            id BIGSERIAL PRIMARY KEY,
            city_code TEXT NOT NULL,
            config_type TEXT NOT NULL,
            config_key TEXT NOT NULL,
            config_value_json TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(city_code, config_type, config_key)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS query_logs (
            request_no TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            target_date TEXT NOT NULL,
            parsed_constraints_json TEXT NOT NULL,
            recommended_route_name TEXT NOT NULL,
            fallback_reason_json TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ride_requests (
            id TEXT,
            request_no TEXT PRIMARY KEY,
            city_code TEXT NOT NULL,
            raw_query TEXT NOT NULL,
            target_date TEXT NOT NULL,
            origin_region TEXT,
            available_hours DOUBLE PRECISION,
            target_distance_km DOUBLE PRECISION,
            fitness_level TEXT,
            ride_style TEXT,
            parsed_constraints_json TEXT NOT NULL,
            user_profile_json TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS weather_snapshots (
            id TEXT,
            request_no TEXT PRIMARY KEY,
            weather_no TEXT NOT NULL,
            city_code TEXT NOT NULL,
            region_code TEXT NOT NULL,
            forecast_date TEXT NOT NULL,
            temperature_min DOUBLE PRECISION,
            temperature_max DOUBLE PRECISION,
            precipitation_probability DOUBLE PRECISION,
            wind_speed DOUBLE PRECISION,
            wind_direction TEXT,
            weather_summary TEXT NOT NULL,
            provider_name TEXT NOT NULL,
            raw_payload_json TEXT,
            fetched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS risk_assessments (
            id BIGSERIAL PRIMARY KEY,
            entity_id TEXT,
            request_no TEXT NOT NULL,
            risk_no TEXT NOT NULL,
            route_code TEXT NOT NULL,
            route_name TEXT NOT NULL,
            recommendation_score DOUBLE PRECISION NOT NULL,
            overall_risk_score DOUBLE PRECISION NOT NULL,
            risk_level TEXT NOT NULL,
            weather_risk_score DOUBLE PRECISION NOT NULL,
            climb_risk_score DOUBLE PRECISION NOT NULL,
            traffic_risk_score DOUBLE PRECISION NOT NULL,
            supply_risk_score DOUBLE PRECISION NOT NULL,
            return_risk_score DOUBLE PRECISION NOT NULL,
            crowd_risk_score DOUBLE PRECISION NOT NULL,
            reasons_json TEXT NOT NULL,
            mitigation_advice_json TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS decision_results (
            id TEXT,
            request_no TEXT PRIMARY KEY,
            decision_no TEXT NOT NULL,
            recommended_route_code TEXT NOT NULL,
            backup_route_codes_json TEXT NOT NULL,
            go_decision TEXT NOT NULL,
            explanation TEXT NOT NULL,
            roadbook_json TEXT,
            status TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS nearby_destinations (
            destination_no TEXT PRIMARY KEY,
            city_code TEXT NOT NULL,
            region_tags_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS trip_templates (
            trip_no TEXT PRIMARY KEY,
            city_code TEXT NOT NULL,
            route_template_id TEXT NOT NULL,
            destination_no TEXT NOT NULL,
            origin_region_tags_json TEXT NOT NULL,
            trip_style_tags_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS experience_contents (
            content_key TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS lifestyle_profiles (
            profile_key TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS completed_rides (
            ride_no TEXT PRIMARY KEY,
            request_no TEXT NOT NULL UNIQUE,
            user_uid TEXT NOT NULL,
            selected_route_code TEXT,
            actual_duration_hours DOUBLE PRECISION,
            actual_distance_km DOUBLE PRECISION,
            user_note TEXT,
            visibility_level TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS media_assets (
            asset_no TEXT PRIMARY KEY,
            owner_type TEXT NOT NULL,
            owner_no TEXT NOT NULL,
            storage_key TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            file_size_bytes BIGINT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS post_ride_shares (
            share_no TEXT PRIMARY KEY,
            ride_no TEXT NOT NULL,
            asset_no TEXT NOT NULL,
            styled_asset_no TEXT,
            style_preset TEXT NOT NULL,
            caption_tone TEXT NOT NULL,
            channel_targets_json TEXT NOT NULL,
            status TEXT NOT NULL,
            stage TEXT NOT NULL,
            provider_name TEXT,
            idempotency_key TEXT NOT NULL UNIQUE,
            context_json TEXT,
            prompt_json TEXT,
            result_payload_json TEXT,
            error_code TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
        """,
    ]


def _apply_compatible_migrations(connection) -> None:
    columns = {
        "route_templates": [
            ("id", "TEXT"),
            ("route_no", "TEXT"),
            ("status", "TEXT DEFAULT 'active'"),
            ("route_source", "TEXT DEFAULT 'seed'"),
        ],
        "city_strategy_configs": [
            ("entity_id", "TEXT"),
            ("config_no", "TEXT"),
        ],
        "ride_requests": [
            ("id", "TEXT"),
            ("rider_state_json", "TEXT"),
        ],
        "weather_snapshots": [
            ("id", "TEXT"),
        ],
        "decision_results": [
            ("id", "TEXT"),
        ],
        "risk_assessments": [
            ("entity_id", "TEXT"),
        ],
        "user_profiles": [
            ("bike_type", "TEXT"),
            ("experience_level", "TEXT"),
            ("riding_goal", "TEXT"),
        ],
    }
    for table_name, table_columns in columns.items():
        existing = _list_columns(connection, table_name)
        for column_name, definition in table_columns:
            if column_name in existing:
                continue
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def _list_columns(connection, table_name: str) -> set[str]:
    rows = connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = ?
        """,
        (table_name,),
    ).fetchall()
    columns: set[str] = set()
    for row in rows:
        if "column_name" in row:
            columns.add(row["column_name"])
            continue
        values = list(row.values())
        if values:
            columns.add(str(values[0]))
    return columns
