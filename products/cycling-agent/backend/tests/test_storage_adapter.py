"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

import sys
import types

from app.core import storage as storage_module
from app.core.storage import _translate_query_for_postgres, connect, database_kind, init_storage
from app.repositories.ride_record_repository import save_ride_record


class FakeCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple]] = []

    def execute(self, query: str, params: tuple) -> None:
        self.executed.append((query, params))

    def fetchone(self):
        return {"count": 1}

    def fetchall(self):
        return [{"request_no": "RQ-TEST"}]


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_obj = FakeCursor()
        self.commit_called = False
        self.rollback_called = False
        self.close_called = False

    def cursor(self) -> FakeCursor:
        return self.cursor_obj

    def commit(self) -> None:
        self.commit_called = True

    def rollback(self) -> None:
        self.rollback_called = True

    def close(self) -> None:
        self.close_called = True


def test_database_kind_supports_sqlite_and_postgres() -> None:
    assert database_kind("sqlite:///./cycling-agent.db") == "sqlite"
    assert database_kind("postgresql://user:pass@localhost:5432/cycling_agent") == "postgres"


def test_translate_query_for_postgres_rewrites_placeholders() -> None:
    query = "SELECT payload_json FROM route_templates WHERE (? IS NULL OR city_code = ?) AND route_code = ?"
    assert _translate_query_for_postgres(query) == "SELECT payload_json FROM route_templates WHERE (%s IS NULL OR city_code = %s) AND route_code = %s"


def test_connect_postgres_uses_psycopg_and_returns_mapping_rows(monkeypatch) -> None:
    fake_connection = FakeConnection()
    fake_psycopg = types.SimpleNamespace(connect=lambda *args, **kwargs: fake_connection)
    fake_rows = types.SimpleNamespace(dict_row="dict_row")
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.rows", fake_rows)

    with connect("postgresql://user:pass@localhost:5432/cycling_agent") as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM route_templates WHERE route_code = ?", ("HZ-RIVER-001",)).fetchone()

    assert row["count"] == 1
    assert fake_connection.cursor_obj.executed[0][0] == "SELECT COUNT(*) AS count FROM route_templates WHERE route_code = %s"
    assert fake_connection.commit_called is True
    assert fake_connection.close_called is True


def test_init_storage_runs_postgres_ddl(monkeypatch) -> None:
    fake_connection = FakeConnection()
    fake_psycopg = types.SimpleNamespace(connect=lambda *args, **kwargs: fake_connection)
    fake_rows = types.SimpleNamespace(dict_row="dict_row")
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.rows", fake_rows)

    init_storage("postgresql://user:pass@localhost:5432/cycling_agent")

    executed_queries = [query for query, _ in fake_connection.cursor_obj.executed]
    ride_records_ddl = next(query for query in executed_queries if "CREATE TABLE IF NOT EXISTS ride_records" in query)
    assert any("CREATE TABLE IF NOT EXISTS ride_plans" in query for query in executed_queries)
    assert any("BIGSERIAL PRIMARY KEY" in query for query in executed_queries)
    assert "destination_name TEXT" in ride_records_ddl
    assert "start_point TEXT" in ride_records_ddl
    assert "payload_json TEXT NOT NULL" in ride_records_ddl
    assert "updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP" in ride_records_ddl


def test_init_storage_uses_postgres_timestamp_type_for_legacy_ride_record_updated_at(monkeypatch) -> None:
    fake_connection = FakeConnection()
    fake_psycopg = types.SimpleNamespace(connect=lambda *args, **kwargs: fake_connection)
    fake_rows = types.SimpleNamespace(dict_row="dict_row")
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.rows", fake_rows)

    existing_ride_record_columns = {
        "entry_mode",
        "source_request_no",
        "ride_date",
        "intent",
        "plan_kind",
        "route_code",
        "route_title",
        "destination_name",
        "start_point",
        "origin_region",
        "completion_status",
        "actual_duration_hours",
        "actual_distance_km",
        "effort_feeling",
        "mood_after",
        "notes",
        "tags_json",
        "payload_json",
    }

    def fake_list_columns(connection, database_url: str, table_name: str) -> set[str]:
        if table_name == "ride_records":
            return existing_ride_record_columns
        return {"id", "route_no", "status", "route_source", "entity_id", "config_no"}

    monkeypatch.setattr(storage_module, "_list_columns", fake_list_columns)

    init_storage("postgresql://user:pass@localhost:5432/cycling_agent")

    assert (
        "ALTER TABLE ride_records ADD COLUMN updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP",
        (),
    ) in fake_connection.cursor_obj.executed


def test_ride_record_repository_uses_postgres_adapter_for_save(monkeypatch) -> None:
    fake_connection = FakeConnection()
    fake_psycopg = types.SimpleNamespace(connect=lambda *args, **kwargs: fake_connection)
    fake_rows = types.SimpleNamespace(dict_row="dict_row")
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.rows", fake_rows)

    save_ride_record(
        "postgresql://user:pass@localhost:5432/cycling_agent",
        {
            "ride_record_no": "RR-PG-001",
            "entry_mode": "manual",
            "ride_date": "2026-06-15",
            "destination_name": "钱塘江南岸",
            "start_point": "闻涛路滨江段",
            "completion_status": "completed",
            "effort_feeling": "steady",
            "mood_after": "refreshed",
            "tags": ["postgres-path"],
        },
    )

    insert_query, params = fake_connection.cursor_obj.executed[0]
    assert "INSERT INTO ride_records" in insert_query
    assert "payload_json" in insert_query
    assert "%s" in insert_query
    assert "?" not in insert_query
    assert params[0] == "RR-PG-001"
    assert params[8] == "钱塘江南岸"
    assert params[9] == "闻涛路滨江段"
