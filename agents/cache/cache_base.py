"""
Abstract base class for cache implementations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time


class CacheBase(ABC):
    """Abstract base class for cache implementations"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Store value in cache with time-to-live"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = 0
        if self.stats['hits'] + self.stats['misses'] > 0:
            hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses'])
        
        return {
            **self.stats,
            'hit_rate': hit_rate
        }
    
    def _is_expired(self, timestamp: float, ttl: int) -> bool:
        """Check if cache entry has expired"""
        return time.time() - timestamp > ttl 