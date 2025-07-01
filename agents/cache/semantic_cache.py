"""
Semantic cache implementation using embeddings and SQLite
"""

import json
import sqlite3
import time
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import logging

from .cache_base import CacheBase

logger = logging.getLogger(__name__)


class SemanticCache(CacheBase):
    """Semantic cache using embeddings for similarity matching"""
    
    def __init__(self, project_id: str, cache_dir: Path, similarity_threshold: float = 0.85):
        super().__init__(project_id)
        self.cache_dir = cache_dir / project_id / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.cache_dir / 'semantic_cache.db'
        self.similarity_threshold = similarity_threshold
        
        # Initialize database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database with embeddings table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                data_json TEXT NOT NULL,
                query_preview TEXT,
                timestamp REAL NOT NULL,
                ttl INTEGER NOT NULL
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_project_timestamp 
            ON embeddings(project_id, timestamp)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Initialized semantic cache database at {self.db_path}")
    
    def add_embedding(self, embedding: List[float], data: Any, 
                     query_preview: str = "", ttl: int = 86400) -> None:
        """Add embedding with associated data to cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO embeddings 
                (project_id, embedding_json, data_json, query_preview, timestamp, ttl)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.project_id,
                json.dumps(embedding),
                json.dumps(data),
                query_preview[:200],
                time.time(),
                ttl
            ))
            
            conn.commit()
            self.stats['sets'] += 1
            logger.debug(f"Added embedding to semantic cache")
            
        except Exception as e:
            logger.error(f"Failed to add embedding: {e}")
        finally:
            conn.close()
    
    def find_similar(self, query_embedding: List[float], 
                    threshold: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Find most similar cached result above threshold"""
        if threshold is None:
            threshold = self.similarity_threshold
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get all non-expired embeddings for this project
            current_time = time.time()
            cursor.execute('''
                SELECT id, embedding_json, data_json, timestamp, ttl
                FROM embeddings
                WHERE project_id = ?
                AND (timestamp + ttl) > ?
            ''', (self.project_id, current_time))
            
            rows = cursor.fetchall()
            
            if not rows:
                self.stats['misses'] += 1
                return None
            
            # Convert query embedding to numpy array
            query_vec = np.array(query_embedding)
            
            # Find most similar embedding
            best_similarity = -1
            best_result = None
            
            for row_id, emb_json, data_json, timestamp, ttl in rows:
                # Parse stored embedding
                stored_vec = np.array(json.loads(emb_json))
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_vec, stored_vec)
                
                if similarity > best_similarity and similarity >= threshold:
                    best_similarity = similarity
                    best_result = {
                        'data': json.loads(data_json),
                        'similarity': similarity,
                        'cache_age': current_time - timestamp
                    }
            
            if best_result:
                self.stats['hits'] += 1
                logger.debug(f"Semantic cache hit with similarity: {best_similarity:.3f}")
                return best_result
            else:
                self.stats['misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"Error searching semantic cache: {e}")
            self.stats['misses'] += 1
            return None
        finally:
            conn.close()
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    def get(self, key: str) -> Optional[Any]:
        """Not implemented for semantic cache - use find_similar instead"""
        raise NotImplementedError("Use find_similar() for semantic cache lookups")
    
    def set(self, key: str, value: Any, ttl: int = 86400) -> None:
        """Not implemented for semantic cache - use add_embedding instead"""
        raise NotImplementedError("Use add_embedding() to add to semantic cache")
    
    def delete(self, key: str) -> bool:
        """Delete by ID (not implemented for semantic cache)"""
        return False
    
    def clear(self) -> None:
        """Clear all cache entries for this project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM embeddings WHERE project_id = ?', (self.project_id,))
            conn.commit()
            logger.info(f"Cleared semantic cache for project {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to clear semantic cache: {e}")
        finally:
            conn.close()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            current_time = time.time()
            
            # Count entries to be deleted
            cursor.execute('''
                SELECT COUNT(*) FROM embeddings
                WHERE project_id = ? AND (timestamp + ttl) <= ?
            ''', (self.project_id, current_time))
            
            count = cursor.fetchone()[0]
            
            # Delete expired entries
            cursor.execute('''
                DELETE FROM embeddings
                WHERE project_id = ? AND (timestamp + ttl) <= ?
            ''', (self.project_id, current_time))
            
            conn.commit()
            
            if count > 0:
                self.stats['evictions'] += count
                logger.info(f"Cleaned up {count} expired semantic cache entries")
                
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")
            return 0
        finally:
            conn.close()
    
    def get_cache_size(self) -> Dict[str, int]:
        """Get cache size statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT COUNT(*), SUM(LENGTH(embedding_json) + LENGTH(data_json))
                FROM embeddings
                WHERE project_id = ?
            ''', (self.project_id,))
            
            count, total_size = cursor.fetchone()
            
            return {
                'entry_count': count or 0,
                'total_bytes': total_size or 0,
                'avg_entry_bytes': (total_size // count) if count else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache size: {e}")
            return {'entry_count': 0, 'total_bytes': 0, 'avg_entry_bytes': 0}
        finally:
            conn.close() 