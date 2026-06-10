"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

from app.providers.llm_provider import OpenAICompatibleLLMProvider


class MockResponse:
    def __init__(self, content: str) -> None:
        self.content = content

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self.content}}]}


def test_llm_provider_parses_query_and_generates_roadbook_json() -> None:
    calls = []

    def fake_post(url: str, *, headers: dict, json: dict, timeout: float):
        calls.append(json["messages"][0]["content"])
        if "骑行查询解析器" in json["messages"][0]["content"]:
            return MockResponse('{"origin_region":"滨江","available_hours":3,"ride_style":"scenic_relaxed","missing_fields":[],"confidence":0.91}')
        return MockResponse('{"departure_window":"06:30-09:00","mitigation_advice":["注意补水"]}')

    provider = OpenAICompatibleLLMProvider(
        base_url="https://example.com/v1",
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
        http_post=fake_post,
    )

    parsed = provider.parse_query(query="周六从闻涛路滨江段出发骑3小时，不想太累", user_profile={})
    roadbook = provider.generate_roadbook(route={"name": "滨江线"}, risk={"risk_level": "low"}, parsed_constraints=parsed)

    assert parsed["origin_region"] == "滨江"
    assert parsed["available_hours"] == 3
    assert parsed["ride_style"] == "scenic_relaxed"
    assert roadbook["departure_window"] == "06:30-09:00"
    assert calls


def test_llm_provider_normalizes_nested_parser_payload() -> None:
    def fake_post(url: str, *, headers: dict, json: dict, timeout: float):
        if "骑行查询解析器" in json["messages"][0]["content"]:
            return MockResponse(
                '{"parsed_query":{"departure_place":"滨江","duration_hours":"3小时","style_preference":"scenic"},"missing_fields":["departure_place"],"confidence":"0.83"}'
            )
        return MockResponse('{"departure_window":"06:30-09:00"}')

    provider = OpenAICompatibleLLMProvider(
        base_url="https://example.com/v1",
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
        http_post=fake_post,
    )

    parsed = provider.parse_query(query="周六从闻涛路滨江段出发骑3小时，不想太累", user_profile={})

    assert parsed == {
        "origin_region": "滨江",
        "available_hours": 3.0,
        "ride_style": "scenic_relaxed",
        "missing_fields": [],
        "confidence": 0.83,
    }
