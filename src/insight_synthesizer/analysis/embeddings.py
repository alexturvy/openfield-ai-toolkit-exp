"""Embedding generation for text chunks."""

from typing import List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
from ..config import PROCESSING_CONFIG
from ..utils.progress_manager import ProgressStage
from .model_cache import get_embedding_model

logger = logging.getLogger(__name__)


class TextChunk:
    """Legacy compatibility class for existing pipeline."""
    def __init__(self, text: str, source_file, embedding=None, cluster_id=None):
        self.text = text
        self.source_file = source_file
        self.embedding = embedding
        self.cluster_id = cluster_id


def generate_embeddings(chunks: List[Union['AdaptiveChunk', TextChunk]], progress_manager=None) -> List[Union['AdaptiveChunk', TextChunk]]:
    """
    Generate embeddings for text chunks using sentence transformers.
    
    Args:
        chunks: List of chunk objects with text content
        progress_manager: Optional UnifiedProgressManager for progress tracking
        
    Returns:
        List of chunks with embeddings added
    """
    # Use cached model for performance
    model = get_embedding_model(PROCESSING_CONFIG['embedding_model'])
    
    if progress_manager:
        # Use the existing stage context from the pipeline
        for i, chunk in enumerate(chunks):
            try:
                progress_manager.set_stage_status(ProgressStage.EMBEDDING_GENERATION, f"Processing chunk {i+1}/{len(chunks)}")
                chunk.embedding = model.encode(chunk.text)
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                progress_manager.log_error(f"Failed to generate embedding for chunk {i+1}: {e}")
                chunk.embedding = None
            
            progress_manager.update_stage(ProgressStage.EMBEDDING_GENERATION, 1)
    else:
        # Fallback for backwards compatibility
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        from rich.console import Console
        
        console = Console()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Generating embeddings...", total=len(chunks))
            
            for i, chunk in enumerate(chunks):
                try:
                    progress.update(task, description=f"Generating embeddings... ({i+1}/{len(chunks)})")
                    chunk.embedding = model.encode(chunk.text)
                except Exception as e:
                    logger.error(f"Error generating embedding: {e}")
                    chunk.embedding = None
                progress.advance(task, 1)
    
    return chunks