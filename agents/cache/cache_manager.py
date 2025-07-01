"""
Cache manager orchestrating multi-tier caching for Auto-Brainlift
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor

from langchain_openai import OpenAIEmbeddings
from .exact_cache import ExactCache
from .semantic_cache import SemanticCache

logger = logging.getLogger(__name__)


class CacheManager:
    """Orchestrates multi-tier caching with exact and semantic matching"""
    
    def __init__(self, project_id: str, cache_dir: Optional[Path] = None):
        """Initialize cache manager for a specific project"""
        self.project_id = project_id
        
        # Set up cache directory to match Electron's app.getPath('userData')
        if cache_dir is None:
            # Use platform-specific app data directory
            import platform
            if platform.system() == 'Darwin':  # macOS
                cache_dir = Path.home() / 'Library' / 'Application Support' / 'auto-brainlift' / 'projects'
            elif platform.system() == 'Windows':
                cache_dir = Path.home() / 'AppData' / 'Roaming' / 'auto-brainlift' / 'projects'
            else:  # Linux
                cache_dir = Path.home() / '.config' / 'auto-brainlift' / 'projects'
        
        self.cache_dir = cache_dir
        
        # Initialize caches
        self.exact_cache = ExactCache(project_id, cache_dir)
        self.semantic_cache = SemanticCache(project_id, cache_dir)
        
        # Initialize embeddings model
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002"  # Cheapest at $0.0001/1K tokens
        )
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Metrics tracking
        self.metrics = {
            'exact_hits': 0,
            'semantic_hits': 0,
            'cache_misses': 0,
            'embedding_generations': 0,
            'total_latency_ms': 0,
            'request_count': 0
        }
    
    def get_or_generate(self, query: str, generator_fn: Callable, 
                       cache_ttl: int = 3600) -> Dict[str, Any]:
        """
        Get cached result or generate new one with multi-tier caching
        
        Args:
            query: The query/diff to process
            generator_fn: Function to generate result if not cached
            cache_ttl: Time-to-live for cache entries
            
        Returns:
            Dict with result and metadata
        """
        start_time = time.time()
        
        # Level 1: Check exact match cache (fastest ~50ms)
        exact_result = self.exact_cache.get(query)
        if exact_result is not None:
            self.metrics['exact_hits'] += 1
            return self._format_result(
                exact_result, 
                cache_hit='exact',
                latency_ms=(time.time() - start_time) * 1000
            )
        
        # Level 2: Generate embedding and check semantic cache (~2s)
        try:
            # Generate embedding for the query
            query_embedding = self._generate_embedding(query)
            
            # Search semantic cache
            semantic_result = self.semantic_cache.find_similar(query_embedding)
            if semantic_result is not None:
                self.metrics['semantic_hits'] += 1
                return self._format_result(
                    semantic_result['data'],
                    cache_hit='semantic',
                    similarity=semantic_result['similarity'],
                    cache_age_hours=semantic_result['cache_age'] / 3600,
                    latency_ms=(time.time() - start_time) * 1000
                )
        except Exception as e:
            logger.error(f"Error in semantic cache lookup: {e}")
        
        # Level 3: Generate new result (slowest ~6s)
        self.metrics['cache_misses'] += 1
        
        try:
            # Generate result using provided function
            result = generator_fn(query)
            
            # Cache the result asynchronously
            self._cache_result_async(query, result, query_embedding, cache_ttl)
            
            # Update metrics
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.metrics['request_count'] += 1
            self.metrics['total_latency_ms'] += elapsed_ms
            
            # Save updated stats to file
            self.save_stats_to_file(self.get_cache_stats())
            
            return self._format_result(
                result,
                cache_hit='miss',
                latency_ms=elapsed_ms
            )
            
        except Exception as e:
            logger.error(f"Error generating result: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI API"""
        try:
            self.metrics['embedding_generations'] += 1
            # Truncate very long texts to save on embedding costs
            if len(text) > 8000:
                text = text[:8000] + "... [truncated]"
            
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def _cache_result_async(self, query: str, result: Any, 
                           embedding: Optional[List[float]], ttl: int) -> None:
        """Cache result in background without blocking"""
        def cache_task():
            try:
                # Always cache exact match
                self.exact_cache.set(query, result, ttl)
                
                # Cache semantic match if embedding available
                if embedding is not None:
                    self.semantic_cache.add_embedding(
                        embedding, result, 
                        query_preview=query[:200],
                        ttl=ttl * 24  # Semantic cache has longer TTL
                    )
            except Exception as e:
                logger.error(f"Failed to cache result: {e}")
        
        # Run caching in background
        self.executor.submit(cache_task)
    
    def _format_result(self, data: Any, **metadata) -> Dict[str, Any]:
        """Format result with metadata"""
        return {
            'data': data,
            'metadata': {
                'timestamp': time.time(),
                'project_id': self.project_id,
                **metadata
            }
        }
    
    def clear_cache(self, cache_type: str = 'all') -> Dict[str, bool]:
        """Clear cache(s) for current project"""
        results = {}
        
        if cache_type in ['all', 'exact']:
            self.exact_cache.clear()
            results['exact'] = True
            
        if cache_type in ['all', 'semantic']:
            self.semantic_cache.clear()
            results['semantic'] = True
            
        logger.info(f"Cleared {cache_type} cache for project {self.project_id}")
        return results
    
    def save_stats_to_file(self, stats: Dict[str, Any]) -> None:
        """Save cache statistics to a JSON file for the Electron UI to read"""
        try:
            stats_file = self.cache_dir / self.project_id / 'cache' / 'stats.json'
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(stats_file, 'w') as f:
                import json
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cache stats: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        exact_stats = self.exact_cache.get_stats()
        semantic_stats = self.semantic_cache.get_stats()
        semantic_size = self.semantic_cache.get_cache_size()
        
        # Calculate overall hit rate
        total_hits = self.metrics['exact_hits'] + self.metrics['semantic_hits']
        total_requests = total_hits + self.metrics['cache_misses']
        overall_hit_rate = (total_hits / total_requests) if total_requests > 0 else 0
        
        # Calculate average latency
        avg_latency = (self.metrics['total_latency_ms'] / self.metrics['request_count']
                      if self.metrics['request_count'] > 0 else 0)
        
        # Save stats after calculating
        stats = {
            'project_id': self.project_id,
            'overall': {
                'hit_rate': overall_hit_rate,
                'total_requests': total_requests,
                'avg_latency_ms': avg_latency
            },
            'exact_cache': {
                **exact_stats,
                'hit_count': self.metrics['exact_hits']
            },
            'semantic_cache': {
                **semantic_stats,
                'hit_count': self.metrics['semantic_hits'],
                **semantic_size
            },
            'embeddings': {
                'generations': self.metrics['embedding_generations'],
                'estimated_cost': self.metrics['embedding_generations'] * 0.0001  # $0.0001/1K tokens
            }
        }
        
        # Save to file whenever stats are retrieved
        self.save_stats_to_file(stats)
        
        return stats
    
    def cleanup_expired(self) -> Dict[str, int]:
        """Cleanup expired entries from all caches"""
        return {
            'exact': self.exact_cache.cleanup_expired(),
            'semantic': self.semantic_cache.cleanup_expired()
        }
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True) 