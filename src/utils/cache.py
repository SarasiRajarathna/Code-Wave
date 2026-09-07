"""
cache.py

Deterministic disk caching layer to prevent redundant LLM and retrieval calls.
Adheres to the competition guideline: 'Design to be cheap: cache responses you've already generated'.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Any, Optional


class SimpleDiskCache:
    """Lightweight disk cache using hashed filenames."""

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            workspace_root = Path(__file__).resolve().parent.parent.parent
            self.cache_dir = workspace_root / "data" / ".cache"
        else:
            self.cache_dir = Path(cache_dir)
        self.enabled = os.getenv("CACHE_ENABLED", "true").lower() in ("true", "1", "yes")
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def hash_key(*args, **kwargs) -> str:
        """Create deterministic SHA256 hex digest from arguments."""
        raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value if present and enabled."""
        if not self.enabled:
            return None
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def set(self, key: str, value: Any) -> None:
        """Save value to cache if enabled."""
        if not self.enabled:
            return
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to write cache {cache_file}: {e}")

    def clear(self) -> None:
        """Clear all cache files."""
        if self.cache_dir.exists():
            for f in self.cache_dir.glob("*.json"):
                try:
                    f.unlink()
                except Exception:
                    pass
