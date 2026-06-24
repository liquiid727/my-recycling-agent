"""CN: Chat turn API 测试，验证 C 端对话体验、槽位合并和 LLM fallback。
EN: Chat turn API tests for consumer chat UX, slot merging, and LLM fallback.
"""

from datetime import date
import time

from fastapi.testclient import TestClient

from app.main import create_app
import app.agents.chat_turn_agent as chat_turn_agent


class StubChatLLMProvider:
    provider_name = "stub-chat-llm"

    def generate_chat_turn(self, *, messages: list[dict], slot_state: dict, planning_scene: str, target_date: date, user_profile: dict | None = None) -> dict:
        latest = messages[-1]["content"]
        if "沈塘桥" in latest:
            return {
                "assistant_message": "收到，沈塘桥出发，骑 2 小时，轻松一点。我先帮你看今晚适不适合骑，再给你几条稳妥路线。",
                "slot_state": {
                    **slot_state,
                    "planning_scene": planning_scene,
                    "start_point": "沈塘桥",
                    "available_hours": 2,
                    "ride_style": "scenic_relaxed",
                    "slope_tolerance": "avoid",
                    "duration_bucket": "evening",
                },
                "missing_slots": [],
                "ready_to_plan": True,
                "confidence": 0.94,
            }
        return {
            "assistant_message": "可以呀～今晚轻松骑挺合适。我先确认两件事：你现在从哪里出发？大概想骑多久？",
            "slot_state": {"planning_scene": planning_scene, "duration_bucket": "evening"},
            "missing_slots": ["start_point", "available_hours_or_target_distance_km"],
            "ready_to_plan": False,
            "confidence": 0.88,
        }


class BrokenChatLLMProvider:
    provider_name = "broken-chat-llm"

    def generate_chat_turn(self, **kwargs):
        raise RuntimeError("llm unavailable")


class OverAskingChatLLMProvider:
    provider_name = "over-asking-chat-llm"

    def generate_chat_turn(self, **kwargs):
        return {
            "assistant_message": "收到，凤起路出发，骑大概 2 小时。再跟我说几点出发、想不想爬坡、强度如何。",
            "slot_state": {
                "planning_scene": "city_ride",
                "duration_bucket": "evening",
                "start_point": "凤起路",
                "available_hours": 2,
            },
            "missing_slots": [],
            "ready_to_plan": False,
        }


class InvalidEnumChatLLMProvider:
    provider_name = "invalid-enum-chat-llm"

    def generate_chat_turn(self, **kwargs):
        return {
            "assistant_message": "收到，凤起路出发，骑 2 小时。",
            "slot_state": {
                "planning_scene": "city_ride",
                "duration_bucket": "evening",
                "start_point": "凤起路",
                "available_hours": 2,
                "slope_tolerance": "avoid_hills",
            },
            "missing_slots": [],
            "ready_to_plan": True,
        }


class SlowChatLLMProvider:
    provider_name = "slow-chat-llm"
    timeout_seconds = 60

    def generate_chat_turn(self, **kwargs):
        time.sleep(0.2)
        return {
            "assistant_message": "这句不应该等到。",
            "slot_state": {},
            "missing_slots": [],
            "ready_to_plan": False,
        }


def test_chat_turn_asks_warm_follow_up_for_vague_city_ride() -> None:
    app = create_app()
    app.state.llm_provider = StubChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [{"role": "user", "content": "我今天晚上想出去骑行一下"}],
            "planning_scene": "city_ride",
            "target_date": "2026-06-06",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assistant_name"] == "AAA骑车帮帮"
    assert body["ready_to_plan"] is False
    assert body["missing_slots"] == ["start_point", "available_hours_or_target_distance_km"]
    assert "你现在从哪里出发" in body["assistant_message"]
    assert "多少公里" in body["assistant_message"]
    assert "当前还缺少关键信息" not in body["assistant_message"]
    assert body["ui_hints"]["quick_replies"]


def test_chat_turn_second_reply_returns_planner_request() -> None:
    app = create_app()
    app.state.llm_provider = StubChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [
                {"role": "user", "content": "我今天晚上想出去骑行一下"},
                {"role": "assistant", "content": "你现在从哪里出发？大概想骑多久？"},
                {"role": "user", "content": "沈塘桥，我这里想要骑行2h"},
            ],
            "planning_scene": "city_ride",
            "target_date": "2026-06-06",
            "slot_state": {"planning_scene": "city_ride", "duration_bucket": "evening"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["slot_state"]["start_point"] == "沈塘桥"
    assert body["slot_state"]["available_hours"] == 2
    assert body["planner_request"]["input_mode"] == "structured"
    assert body["planner_request"]["structured_constraints"]["start_point"] == "沈塘桥"
    assert body["planner_request"]["structured_constraints"]["available_hours"] == 2
    assert body["planner_request"]["structured_constraints"]["ride_style"] is None
    assert body["planner_request"]["structured_constraints"]["slope_tolerance"] is None
    assert "missing_fields" not in body["assistant_message"]


def test_chat_turn_falls_back_when_llm_fails() -> None:
    app = create_app()
    app.state.llm_provider = BrokenChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [
                {"role": "user", "content": "我今天晚上想出去骑行一下"},
                {"role": "user", "content": "沈塘桥，我这里想要骑行2h"},
            ],
            "planning_scene": "city_ride",
            "target_date": "2026-06-06",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["slot_state"]["start_point"] == "沈塘桥"
    assert body["slot_state"]["available_hours"] == 2
    assert body["planner_request"] is not None
    assert "风和温度" in body["assistant_message"]


def test_chat_turn_fallback_accepts_bare_road_name_and_duration() -> None:
    app = create_app()
    app.state.llm_provider = BrokenChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [
                {"role": "user", "content": "我今天晚上想出去骑行一下"},
                {"role": "assistant", "content": "你现在从哪里出发？大概想骑多久？"},
                {"role": "user", "content": "凤起路 ，2h吧"},
            ],
            "planning_scene": "city_ride",
            "target_date": "2026-06-06",
            "slot_state": {"planning_scene": "city_ride", "duration_bucket": "evening"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["slot_state"]["start_point"] == "凤起路"
    assert body["slot_state"]["available_hours"] == 2
    assert "还差一个出发点" not in body["assistant_message"]


def test_chat_turn_fallback_accepts_bare_metro_station_follow_up() -> None:
    app = create_app()
    app.state.llm_provider = BrokenChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [
                {"role": "user", "content": "我今天晚上想出去骑行一下"},
                {"role": "assistant", "content": "你现在从哪里出发？大概想骑多久？"},
                {"role": "user", "content": "2h吧"},
                {"role": "assistant", "content": "时长我收到了。还差一个出发点，我才能帮你避开绕路。你现在大概在哪？"},
                {"role": "user", "content": "凤起路地铁站啊"},
            ],
            "planning_scene": "city_ride",
            "target_date": "2026-06-06",
            "slot_state": {"planning_scene": "city_ride", "duration_bucket": "evening", "available_hours": 2},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["slot_state"]["start_point"] == "凤起路地铁站"
    assert body["slot_state"]["available_hours"] == 2
    assert "还差一个出发点" not in body["assistant_message"]


def test_chat_turn_validator_overrides_over_asking_llm_when_core_slots_are_ready() -> None:
    app = create_app()
    app.state.llm_provider = OverAskingChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [
                {"role": "user", "content": "我今天晚上想出去骑行一下"},
                {"role": "user", "content": "凤起路 ，2h吧"},
            ],
            "planning_scene": "city_ride",
            "target_date": "2026-06-06",
            "slot_state": {"planning_scene": "city_ride", "duration_bucket": "evening"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["planner_request"] is not None
    assert body["slot_state"]["start_point"] == "凤起路"
    assert body["slot_state"]["available_hours"] == 2
    assert "再跟我说" not in body["assistant_message"]


def test_chat_turn_validator_normalizes_llm_enum_slots_before_planning() -> None:
    app = create_app()
    app.state.llm_provider = InvalidEnumChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [{"role": "user", "content": "凤起路，2h吧，不要爬坡"}],
            "planning_scene": "city_ride",
            "target_date": "2026-06-06",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["slot_state"]["slope_tolerance"] == "avoid"
    assert body["planner_request"]["structured_constraints"]["slope_tolerance"] == "avoid"


def test_chat_turn_fallback_reconciles_no_climb_intent() -> None:
    app = create_app()
    app.state.llm_provider = BrokenChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [{"role": "user", "content": "凤起路，2h吧，不要爬坡"}],
            "planning_scene": "city_ride",
            "target_date": "2026-06-06",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["slot_state"]["slope_tolerance"] == "avoid"
    assert body["slot_state"]["ride_style"] == "scenic_relaxed"
    assert "带点爬坡" not in body["assistant_message"]
    assert "轻松一点" in body["assistant_message"]


def test_chat_turn_ready_message_respects_tired_rider_state() -> None:
    app = create_app()
    app.state.llm_provider = BrokenChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [{"role": "user", "content": "凤起路，2h吧"}],
            "planning_scene": "city_ride",
            "target_date": "2026-06-06",
            "rider_state": {"fatigue_level": "tired", "mood": "recover", "last_ride_days_ago": 0},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["rider_state"]["fatigue_level"] == "tired"
    assert "轻松恢复一下" in body["assistant_message"]


def test_chat_turn_falls_back_quickly_when_llm_is_slow(monkeypatch) -> None:
    monkeypatch.setattr(chat_turn_agent, "LLM_CHAT_TIMEOUT_SECONDS", 0.01)
    app = create_app()
    app.state.llm_provider = SlowChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [
                {"role": "user", "content": "我今天晚上想出去骑行一下"},
                {"role": "user", "content": "凤起路 ，2h吧"},
            ],
            "planning_scene": "city_ride",
            "target_date": "2026-06-06",
            "slot_state": {"planning_scene": "city_ride", "duration_bucket": "evening"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["slot_state"]["start_point"] == "凤起路"
    assert body["slot_state"]["available_hours"] == 2


def test_chat_turn_weekend_follow_up_asks_for_days_and_overnight() -> None:
    app = create_app()
    app.state.llm_provider = BrokenChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [{"role": "user", "content": "周末想出去骑车，附近有什么推荐线路么"}],
            "planning_scene": "weekend_trip",
            "target_date": "2026-06-06",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is False
    assert body["missing_slots"] == ["start_point", "duration_bucket", "overnight_preference"]
    assert "想骑一天、两天还是三天" in body["assistant_message"]
    assert "住一晚" in body["assistant_message"]
    assert body["ui_hints"]["quick_replies"] == ["滨江出发", "城西出发", "杭州东附近"]


def test_chat_turn_weekend_ready_message_mentions_window_and_backup_shape() -> None:
    app = create_app()
    app.state.llm_provider = BrokenChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [{"role": "user", "content": "这周末想去千岛湖骑两天，从滨江区政府出发，可以住一晚"}],
            "planning_scene": "weekend_trip",
            "target_date": "2026-06-06",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready_to_plan"] is True
    assert body["slot_state"]["duration_bucket"] == "two_day"
    assert body["slot_state"]["overnight_preference"] == "required"
    assert "千岛湖" in body["assistant_message"]
    assert "天气窗口、住宿和返程" in body["assistant_message"]
    assert body["ui_hints"]["planning_status_label"] == "我在看天气窗口、住宿和返程"


def test_chat_turn_allows_explicit_weekend_query_to_override_city_scene_hint() -> None:
    app = create_app()
    app.state.llm_provider = BrokenChatLLMProvider()
    client = TestClient(app)

    response = client.post(
        "/api/v1/ride/chat/turn",
        json={
            "messages": [{"role": "user", "content": "周末想从凤起路出发骑两天，可以住一晚"}],
            "planning_scene": "city_ride",
            "target_date": "2026-06-06",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["slot_state"]["planning_scene"] == "weekend_trip"
    assert body["planner_request"]["planning_scene"] == "weekend_trip"
    assert body["planner_request"]["planning_mode"] == "nearby_trip"
