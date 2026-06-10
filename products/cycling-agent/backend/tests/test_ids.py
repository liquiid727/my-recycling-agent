"""CN: 后端测试文件，验证 API、服务、仓库、provider、缓存和 live 集成边界。
EN: Backend test file covering APIs, services, repositories, providers, cache, and live integration boundaries.
"""

import re

from app.core.ids import derive_business_no, generate_business_no


def test_generate_business_no_returns_prefixed_time_ordered_suffix() -> None:
    first = generate_business_no("RQ")
    second = generate_business_no("RQ")

    assert re.fullmatch(r"RQ-[0-9A-HJKMNPQRSTVWXYZ]{12}", first)
    assert re.fullmatch(r"RQ-[0-9A-HJKMNPQRSTVWXYZ]{12}", second)
    assert first != second
    assert first < second


def test_derive_business_no_reuses_request_suffix_for_related_entities() -> None:
    request_no = "RQ-01HG6G7X9ZAB"

    assert derive_business_no("DC", request_no) == "DC-01HG6G7X9ZAB"
    assert derive_business_no("RS", request_no, suffix=2) == "RS-01HG6G7X9ZAB-02"
