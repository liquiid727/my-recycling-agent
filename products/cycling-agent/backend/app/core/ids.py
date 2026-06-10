"""CN: 业务编号生成工具，生成时间有序的 request/risk/weather/decision 编号。
EN: Business identifier helpers for time-ordered request, risk, weather, and decision numbers.
"""

from __future__ import annotations

import threading
import time
import uuid


_BASE32_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_STATE_LOCK = threading.Lock()
_LAST_MILLIS = 0
_SEQUENCE = 0


def generate_business_no(prefix: str) -> str:
    return f"{prefix}-{_next_time_ordered_suffix()}"


def generate_uuid_v7_like() -> str:
    timestamp_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    random_bytes = bytearray(uuid.uuid4().bytes)
    value = bytearray(16)

    value[0:6] = timestamp_ms.to_bytes(6, "big")
    value[6] = (0x70 | (random_bytes[6] & 0x0F))
    value[7] = random_bytes[7]
    value[8] = 0x80 | (random_bytes[8] & 0x3F)
    value[9:] = random_bytes[9:]

    return str(uuid.UUID(bytes=bytes(value)))


def derive_business_no(prefix: str, request_no: str, *, suffix: int | None = None) -> str:
    base = request_no.split("RQ-", 1)[-1]
    if suffix is None:
        return f"{prefix}-{base}"
    return f"{prefix}-{base}-{suffix:02d}"


def _next_time_ordered_suffix() -> str:
    global _LAST_MILLIS, _SEQUENCE

    with _STATE_LOCK:
        current_millis = int(time.time() * 1000)
        if current_millis == _LAST_MILLIS:
            _SEQUENCE = (_SEQUENCE + 1) & 0xFFF
            if _SEQUENCE == 0:
                while current_millis <= _LAST_MILLIS:
                    current_millis = int(time.time() * 1000)
        else:
            _SEQUENCE = 0
        _LAST_MILLIS = current_millis
        packed = (current_millis << 12) | _SEQUENCE

    return _encode_base32(packed, length=12)


def _encode_base32(value: int, *, length: int) -> str:
    chars = []
    remaining = value
    for _ in range(length):
        chars.append(_BASE32_ALPHABET[remaining & 0x1F])
        remaining >>= 5
    return "".join(reversed(chars))
