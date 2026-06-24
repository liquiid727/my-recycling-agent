"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

import sys
import types

import pytest

from app.core.storage import _translate_query_for_postgres, connect, database_kind, init_storage


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


def test_database_kind_accepts_only_postgres_urls() -> None:
    assert database_kind("postgresql://user:pass@localhost:5432/cycling_agent") == "postgres"
    with pytest.raises(ValueError):
        database_kind("sqlite:///./cycling-agent.db")


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

    assert any("CREATE TABLE IF NOT EXISTS ride_plans" in query for query, _ in fake_connection.cursor_obj.executed)
    assert any("BIGSERIAL PRIMARY KEY" in query for query, _ in fake_connection.cursor_obj.executed)
    assert any("CREATE TABLE IF NOT EXISTS completed_rides" in query for query, _ in fake_connection.cursor_obj.executed)
    assert any("CREATE TABLE IF NOT EXISTS post_ride_shares" in query for query, _ in fake_connection.cursor_obj.executed)
