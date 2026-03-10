"""
File-Based Cache Service.

Simple persistent cache using JSON files with TTL support.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any
import hashlib

logger = logging.getLogger(__name__)


class FileCacheService:
    """
    File-based cache with TTL support.

    Stores cached data as JSON files with metadata.
    """

    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize cache service.

        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Cache service initialized: {cache_dir}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value by key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            cache_file = self._get_cache_file(key)

            if not cache_file.exists():
                return None

            # Read cache file
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Check expiry
            if self._is_expired(cache_data):
                self.delete(key)
                return None

            return cache_data.get("value")

        except Exception as e:
            logger.error(f"Cache get failed for {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set cache value with TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (default: 1 hour)

        Returns:
            True if successful
        """
        try:
            cache_file = self._get_cache_file(key)

            # Prepare cache data
            cache_data = {
                "key": key,
                "value": value,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(seconds=ttl)).isoformat(),
                "ttl": ttl,
            }

            # Write to file
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Cache set failed for {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists and is not expired.

        Args:
            key: Cache key

        Returns:
            True if exists and valid
        """
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        """
        Delete cached value.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        try:
            cache_file = self._get_cache_file(key)

            if cache_file.exists():
                cache_file.unlink()
                return True

            return False

        except Exception as e:
            logger.error(f"Cache delete failed for {key}: {e}")
            return False

    def clear_expired(self) -> int:
        """
        Remove all expired cache files.

        Returns:
            Number of files deleted
        """
        deleted = 0

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)

                    if self._is_expired(cache_data):
                        cache_file.unlink()
                        deleted += 1

                except Exception as e:
                    logger.warning(f"Failed to check expiry for {cache_file}: {e}")

            logger.info(f"Cleared {deleted} expired cache files")

        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

        return deleted

    def clear_all(self) -> int:
        """
        Clear all cache files.

        Returns:
            Number of files deleted
        """
        deleted = 0

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                deleted += 1

            logger.info(f"Cleared all {deleted} cache files")

        except Exception as e:
            logger.error(f"Cache clear failed: {e}")

        return deleted

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with stats
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)

            expired = 0
            for cache_file in cache_files:
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)
                    if self._is_expired(cache_data):
                        expired += 1
                except:
                    pass

            return {
                "total_entries": len(cache_files),
                "expired_entries": expired,
                "valid_entries": len(cache_files) - expired,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "cache_dir": str(self.cache_dir),
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for key."""
        # Hash the key to create safe filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def _is_expired(self, cache_data: dict) -> bool:
        """Check if cache data is expired."""
        try:
            expires_at = datetime.fromisoformat(cache_data["expires_at"])
            return datetime.now() > expires_at
        except:
            return True
