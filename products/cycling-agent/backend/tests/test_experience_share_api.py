"""CN: 骑后分享 API 测试，覆盖完成骑行、照片上传、风格图生成与失败分支。
EN: Post-ride share API tests for completed rides, photo upload, share generation, and failures.
"""

from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.plan_result_repository import save_ride_plan
from tests.conftest import set_test_database_url


class StubImageProvider:
    provider_name = "stub-image"

    def edit_ride_photo(self, *, image_bytes: bytes, image_mime_type: str, prompt: str, size: str = "1024x1024") -> dict:
        return {
            "image_bytes": b"styled-image-bytes",
            "mime_type": "image/png",
            "provider_payload": {"prompt": prompt, "size": size},
        }


class BrokenImageProvider:
    provider_name = "broken-image"

    def edit_ride_photo(self, **kwargs):
        raise RuntimeError("boom")


class StubShareCopyProvider:
    provider_name = "stub-copy"

    def generate_post_ride_share_copy(self, *, ride_context: dict, style_preset: str, caption_tone: str, channel_targets: list[str]) -> dict:
        payload = {}
        if "xiaohongshu" in channel_targets:
            payload["xiaohongshu"] = {
                "title": "晚风里的一段轻骑",
                "body": "今天的节奏刚好，骑到江边的时候天色也刚好。",
                "hashtags": ["#城市骑行", "#慢骑一下"],
            }
        if "moments" in channel_targets:
            payload["moments"] = {
                "body": "今天的风和这段骑行，都刚刚好。",
            }
        return {"copy_variants": payload}


def test_post_ride_share_happy_path(monkeypatch, tmp_path) -> None:
    database_url = set_test_database_url(monkeypatch)
    monkeypatch.setenv("CYCLING_AGENT_MEDIA_LOCAL_DIR", str(tmp_path / "generated-media"))
    app = create_app()
    app.state.image_provider = StubImageProvider()
    app.state.llm_provider = StubShareCopyProvider()
    client = TestClient(app)
    save_ride_plan(database_url, _sample_plan_payload())

    complete_response = client.post(
        "/api/v1/experience/rides/RQ-TEST-POSTRIDE/complete",
        json={
            "actual_duration_hours": 1.8,
            "actual_distance_km": 22.5,
            "user_note": "今天江边的风很轻。",
            "visibility_level": "shareable",
        },
    )
    assert complete_response.status_code == 200
    ride_no = complete_response.json()["ride_no"]

    upload_response = client.post(
        "/api/v1/experience/photo-assets",
        data={"ride_no": ride_no},
        files={"photo": ("ride.jpg", b"raw-image-bytes", "image/jpeg")},
    )
    assert upload_response.status_code == 200
    asset_payload = upload_response.json()
    assert asset_payload["status"] == "uploaded"

    share_response = client.post(
        "/api/v1/experience/post-ride-shares",
        json={
            "ride_no": ride_no,
            "asset_no": asset_payload["asset_no"],
            "style_preset": "warm_journal",
            "caption_tone": "gentle",
            "channel_targets": ["xiaohongshu", "moments"],
            "include_route_context": True,
        },
    )
    assert share_response.status_code == 200
    share_payload = share_response.json()
    assert share_payload["status"] == "succeeded"
    assert share_payload["stage"] == "done"
    assert share_payload["styled_image_url"].startswith("/generated-media/")
    assert share_payload["copy_variants"]["xiaohongshu"]["title"]

    result_response = client.get(f"/api/v1/experience/post-ride-shares/{share_payload['share_no']}")
    assert result_response.status_code == 200
    assert result_response.json()["share_no"] == share_payload["share_no"]


def test_post_ride_share_returns_failed_status_when_generation_breaks(monkeypatch, tmp_path) -> None:
    database_url = set_test_database_url(monkeypatch)
    monkeypatch.setenv("CYCLING_AGENT_MEDIA_LOCAL_DIR", str(tmp_path / "generated-media"))
    app = create_app()
    app.state.image_provider = BrokenImageProvider()
    client = TestClient(app)
    save_ride_plan(database_url, _sample_plan_payload())

    ride_no = client.post(
        "/api/v1/experience/rides/RQ-TEST-POSTRIDE/complete",
        json={"visibility_level": "private"},
    ).json()["ride_no"]
    asset_no = client.post(
        "/api/v1/experience/photo-assets",
        data={"ride_no": ride_no},
        files={"photo": ("ride.jpg", b"raw-image-bytes", "image/jpeg")},
    ).json()["asset_no"]

    share_response = client.post(
        "/api/v1/experience/post-ride-shares",
        json={
            "ride_no": ride_no,
            "asset_no": asset_no,
            "style_preset": "city_minimal",
            "caption_tone": "editorial",
            "channel_targets": ["moments"],
            "include_route_context": True,
        },
    )
    assert share_response.status_code == 200
    payload = share_response.json()
    assert payload["status"] == "failed"
    assert payload["error_code"] == "experience-share-generation-failed"


def test_post_ride_share_is_idempotent_without_regenerate(monkeypatch, tmp_path) -> None:
    database_url = set_test_database_url(monkeypatch)
    monkeypatch.setenv("CYCLING_AGENT_MEDIA_LOCAL_DIR", str(tmp_path / "generated-media"))
    app = create_app()
    app.state.image_provider = StubImageProvider()
    app.state.llm_provider = StubShareCopyProvider()
    client = TestClient(app)
    save_ride_plan(database_url, _sample_plan_payload())

    ride_no = client.post(
        "/api/v1/experience/rides/RQ-TEST-POSTRIDE/complete",
        json={"visibility_level": "shareable"},
    ).json()["ride_no"]
    asset_no = client.post(
        "/api/v1/experience/photo-assets",
        data={"ride_no": ride_no},
        files={"photo": ("ride.jpg", b"raw-image-bytes", "image/jpeg")},
    ).json()["asset_no"]

    first = client.post(
        "/api/v1/experience/post-ride-shares",
        json={
            "ride_no": ride_no,
            "asset_no": asset_no,
            "style_preset": "sunset_film",
            "caption_tone": "playful",
            "channel_targets": ["moments"],
            "include_route_context": True,
        },
    ).json()
    second = client.post(
        "/api/v1/experience/post-ride-shares",
        json={
            "ride_no": ride_no,
            "asset_no": asset_no,
            "style_preset": "sunset_film",
            "caption_tone": "playful",
            "channel_targets": ["moments"],
            "include_route_context": True,
        },
    ).json()

    assert first["share_no"] == second["share_no"]


def _sample_plan_payload() -> dict:
    return {
        "status": "success",
        "planning_mode": "route",
        "request_no": "RQ-TEST-POSTRIDE",
        "parsed_constraints": {
            "origin_region": "滨江",
            "available_hours": 2,
            "ride_style": "scenic_relaxed",
        },
        "input_summary": {},
        "recommended_plan": {
            "go_decision": "go",
            "route_name": "滨江晚风线",
            "route_code": "HZ-RIVER-001",
            "distance_km": 20.0,
            "elevation_gain_m": 120.0,
            "estimated_duration_hours": 1.7,
            "risk_level": "low",
            "summary_reason": "江边视野开阔，适合今天慢慢骑。",
        },
        "alternatives": [],
        "weather_snapshot": {
            "region_code": "滨江",
            "forecast_date": "2026-06-24",
            "weather_summary": "cloudy",
            "provider_name": "stub",
        },
        "fallback_reason": [],
        "tool_trace": [],
        "decision_summary": {
            "scene": "city_ride",
            "go_decision": "go",
            "decision_title": "今晚可以出门",
            "decision_reason": "风和温度都比较舒服。",
            "confidence_notes": [],
            "equipment_advice": [],
        },
        "roadbook": {},
    }
