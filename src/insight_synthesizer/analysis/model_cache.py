"""Singleton cache for expensive models to improve performance."""

from sentence_transformers import SentenceTransformer
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ModelCache:
    """Singleton cache for expensive models."""
    _instance = None
    _embedding_model: Optional[SentenceTransformer] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_embedding_model(self, model_name: str = 'all-MiniLM-L6-v2') -> SentenceTransformer:
        """
        Get or create cached embedding model.
        
        Args:
            model_name: Name of the sentence transformer model
            
        Returns:
            Cached SentenceTransformer instance
        """
        if self._embedding_model is None:
            logger.info(f"Loading embedding model {model_name} (one-time cost)...")
            self._embedding_model = SentenceTransformer(model_name)
            logger.info(f"Embedding model {model_name} loaded successfully")
        return self._embedding_model
    
    def clear_cache(self):
        """Clear cached models to free memory."""
        if self._embedding_model is not None:
            logger.info("Clearing embedding model from cache")
            self._embedding_model = None
            
    def get_cache_status(self) -> dict:
        """Get information about cached models."""
        return {
            'embedding_model_loaded': self._embedding_model is not None,
            'embedding_model_name': self._embedding_model.get_sentence_embedding_dimension() if self._embedding_model else None
        }


# Global instance for easy access
_model_cache = ModelCache()


def get_embedding_model(model_name: str = 'all-MiniLM-L6-v2') -> SentenceTransformer:
    """
    Convenience function to get cached embedding model.
    
    Args:
        model_name: Name of the sentence transformer model
        
    Returns:
        Cached SentenceTransformer instance
    """
    return _model_cache.get_embedding_model(model_name)


def clear_model_cache():
    """Convenience function to clear the model cache."""
    _model_cache.clear_cache()