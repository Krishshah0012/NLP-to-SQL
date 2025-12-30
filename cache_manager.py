"""
Intelligent caching system for cost optimization
"""
import json
import hashlib
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path


class CacheManager:
    """Manage caching of NL to SQL translations"""
    
    def __init__(
        self,
        cache_dir: str = ".cache",
        ttl_hours: int = 24,
        max_size: int = 1000
    ):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time to live for cache entries in hours
            max_size: Maximum number of cache entries
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "nl_to_sql_cache.json"
        self.ttl_hours = ttl_hours
        self.max_size = max_size
        self.cache: Dict[str, Dict[str, Any]] = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    # Filter out expired entries
                    now = datetime.now()
                    valid_cache = {}
                    for key, value in cache_data.items():
                        try:
                            cached_at_str = value.get("cached_at", "")
                            if cached_at_str:
                                cached_at = datetime.fromisoformat(cached_at_str)
                                if now - cached_at < timedelta(hours=self.ttl_hours):
                                    valid_cache[key] = value
                        except (ValueError, TypeError):
                            # Skip invalid entries
                            continue
                    return valid_cache
            except (json.JSONDecodeError, KeyError, ValueError):
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2, default=str)
        except Exception as e:
            # Silently fail - caching is not critical
            pass
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result
        
        Args:
            key: Cache key
            
        Returns:
            Cached result or None if not found/expired
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        try:
            cached_at_str = entry.get("cached_at", "")
            if not cached_at_str:
                return None
            cached_at = datetime.fromisoformat(cached_at_str)
            
            # Check if expired
            if datetime.now() - cached_at >= timedelta(hours=self.ttl_hours):
                del self.cache[key]
                self._save_cache()
                return None
        except (ValueError, TypeError):
            # Invalid cache entry, remove it
            del self.cache[key]
            self._save_cache()
            return None
        
        return entry.get("result")
    
    def set(self, key: str, value: Dict[str, Any]):
        """
        Set cache entry
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Enforce max size - remove oldest entries if needed
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            try:
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: datetime.fromisoformat(
                        self.cache[k].get("cached_at", datetime.min.isoformat())
                    )
                )
                del self.cache[oldest_key]
            except (ValueError, TypeError):
                # If we can't determine oldest, remove first entry
                first_key = next(iter(self.cache))
                del self.cache[first_key]
        
        self.cache[key] = {
            "result": value,
            "cached_at": datetime.now().isoformat()
        }
        self._save_cache()
    
    def clear(self):
        """Clear all cache entries"""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_hours": self.ttl_hours,
            "cache_file": str(self.cache_file)
        }

