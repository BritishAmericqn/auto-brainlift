"""
Exact match cache implementation using in-memory storage
"""

import time
import hashlib
import json
from typing import Any, Dict, Optional
from pathlib import Path
import logging

from .cache_base import CacheBase

logger = logging.getLogger(__name__)


class ExactCache(CacheBase):
    """In-memory cache for exact query matches with persistent backup"""
    
    def __init__(self, project_id: str, cache_dir: Path):
        super().__init__(project_id)
        self.cache_dir = cache_dir / project_id / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_file = self.cache_dir / 'exact_cache.json'
        
        # Load persistent cache on init
        self._load_cache()
    
    def _generate_key(self, query: str) -> str:
        """Generate cache key from query using MD5 hash"""
        # Include project_id to prevent cross-project contamination
        full_key = f"{self.project_id}:{query}"
        return hashlib.md5(full_key.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        key = self._generate_key(query)
        
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            
            # Check if expired
            if self._is_expired(entry['timestamp'], entry['ttl']):
                del self.memory_cache[key]
                self.stats['evictions'] += 1
                self.stats['misses'] += 1
                return None
            
            self.stats['hits'] += 1
            logger.debug(f"Cache hit for key: {key[:8]}...")
            return entry['value']
        
        self.stats['misses'] += 1
        return None
    
    def set(self, query: str, value: Any, ttl: int = 3600) -> None:
        """Store value in cache with TTL"""
        key = self._generate_key(query)
        
        self.memory_cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl,
            'query_preview': query[:100]  # For debugging
        }
        
        self.stats['sets'] += 1
        logger.debug(f"Cached result for key: {key[:8]}...")
        
        # Persist to disk periodically
        if self.stats['sets'] % 10 == 0:
            self._save_cache()
    
    def delete(self, key: str) -> bool:
        """Delete specific key from cache"""
        if key in self.memory_cache:
            del self.memory_cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.memory_cache.clear()
        self._save_cache()
        logger.info(f"Cleared exact cache for project {self.project_id}")
    
    def _load_cache(self) -> None:
        """Load cache from persistent storage"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    
                # Filter out expired entries
                current_time = time.time()
                self.memory_cache = {
                    k: v for k, v in data.items()
                    if not self._is_expired(v['timestamp'], v['ttl'])
                }
                
                logger.info(f"Loaded {len(self.memory_cache)} cache entries from disk")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                self.memory_cache = {}
    
    def _save_cache(self) -> None:
        """Save cache to persistent storage"""
        try:
            # Only save non-expired entries
            current_time = time.time()
            valid_entries = {
                k: v for k, v in self.memory_cache.items()
                if not self._is_expired(v['timestamp'], v['ttl'])
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(valid_entries, f, indent=2)
                
            logger.debug(f"Saved {len(valid_entries)} cache entries to disk")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        initial_size = len(self.memory_cache)
        current_time = time.time()
        
        self.memory_cache = {
            k: v for k, v in self.memory_cache.items()
            if not self._is_expired(v['timestamp'], v['ttl'])
        }
        
        removed = initial_size - len(self.memory_cache)
        if removed > 0:
            self.stats['evictions'] += removed
            self._save_cache()
            
        return removed 