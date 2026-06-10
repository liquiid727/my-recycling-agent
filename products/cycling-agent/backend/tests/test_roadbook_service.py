"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from app.services.roadbook_service import build_equipment_advice, build_roadbook


def test_build_roadbook_returns_departure_and_supply_advice() -> None:
    roadbook = build_roadbook(
        route={
            "name": "滨江-钱塘江休闲往返线",
            "start_point_name": "闻涛路滨江段",
            "best_time_slots": ["06:30-09:30"],
            "supply_points": [{"name": "奥体观景平台补水点", "km_mark": 18, "type": "补水点"}],
            "bailout_options": [{"name": "奥体中途折返", "km_mark": 18, "reason": "保留江景主段"}],
        },
        risk={"risk_level": "low"},
    )

    assert roadbook["departure_window"] == "06:30-09:30"
    assert isinstance(roadbook["supply_advice"], list)
    assert "奥体观景平台补水点" in roadbook["supply_advice"][1]
    assert "奥体中途折返" in roadbook["shorten_options"][0]


def test_build_equipment_advice_accounts_for_evening_rain_and_climb() -> None:
    advice = build_equipment_advice(
        route={"climb_segments": [{"name": "龙井爬坡"}]},
        risk={"risk_level": "medium"},
        weather_snapshot={"precipitation_probability": 0.5},
        constraints={"duration_bucket": "evening"},
    )

    assert any("车灯" in item for item in advice)
    assert any("雨" in item for item in advice)
    assert any("补水" in item for item in advice)
