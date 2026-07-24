"""
Local-filesystem storage with in-memory cache.
IBM COS integration is optional — when COS credentials are absent the service
falls back to writing files under ``./uploads/``.
"""

from __future__ import annotations

import json
import os
from typing import Optional


class StorageService:
    """Simple file-system-backed storage with an in-memory LRU cache."""

    def __init__(self, storage_dir: str = "./uploads") -> None:
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self._cache: dict[str, dict] = {}

    # ── write ────────────────────────────────────────────────
    def save(
        self,
        file_id: str,
        file_bytes: bytes,
        filename: str,
        profile: dict,
        preview: list[dict],
    ) -> None:
        entry = {
            "filename": filename,
            "profile": profile,
            "preview": preview,
        }
        self._cache[file_id] = entry

        file_dir = os.path.join(self.storage_dir, file_id)
        os.makedirs(file_dir, exist_ok=True)

        with open(os.path.join(file_dir, "metadata.json"), "w") as f:
            json.dump(entry, f, default=str)

        with open(os.path.join(file_dir, filename), "wb") as f:
            f.write(file_bytes)

    # ── read ─────────────────────────────────────────────────
    def get(self, file_id: str) -> Optional[dict]:
        if file_id in self._cache:
            return self._cache[file_id]

        meta_path = os.path.join(self.storage_dir, file_id, "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                data = json.load(f)
            self._cache[file_id] = data
            return data

        return None
