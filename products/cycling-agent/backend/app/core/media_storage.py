"""CN: 媒体存储抽象，保存上传原图和生成结果并返回可访问引用。
EN: Media-storage abstraction for uploaded and generated image assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class StoredMediaObject:
    storage_key: str
    public_url: str
    file_size_bytes: int


class LocalMediaStorage:
    def __init__(self, *, base_dir: str | Path, public_base_path: str) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.public_base_path = public_base_path.rstrip("/")

    def save_bytes(self, *, storage_key: str, payload: bytes) -> StoredMediaObject:
        path = self.base_dir / storage_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return StoredMediaObject(
            storage_key=storage_key,
            public_url=f"{self.public_base_path}/{storage_key}",
            file_size_bytes=len(payload),
        )

    def read_bytes(self, storage_key: str) -> bytes:
        return (self.base_dir / storage_key).read_bytes()
