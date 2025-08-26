"""Clustering analysis for semantic text chunks."""

from typing import List, Tuple, Union, Optional
from dataclasses import dataclass
import numpy as np
import umap
import hdbscan
from sklearn.preprocessing import normalize
from sklearn.metrics import silhouette_score
from rich.console import Console
from ..config import CLUSTERING_CONFIG
from ..utils import ProgressReporter
from ..utils.progress_reporter import ProcessType
from .clustering_utils import get_adaptive_clustering_params

console = Console()


@dataclass
class Cluster:
    """Cluster of semantically similar text chunks."""
    cluster_id: int
    chunks: List
    size: int


def perform_clustering(chunks: List, progress_reporter: Optional[ProgressReporter] = None, progress_manager=None) -> Tuple[List, List[Cluster]]:
    """
    Perform clustering on embeddings using UMAP + HDBSCAN.
    
    Args:
        chunks: List of chunk objects with embeddings
        progress_reporter: Optional progress reporter for transparency
        
    Returns:
        Tuple of (updated chunks, cluster objects)
    """
    embeddings = np.array([chunk.embedding for chunk in chunks if chunk.embedding is not None])
    if len(embeddings) == 0:
        raise ValueError("No valid embeddings for clustering")
    
    if progress_reporter:
        progress_reporter.start_process(
            ProcessType.CLUSTERING_ANALYSIS,
            details={
                "total_chunks": len(chunks),
                "valid_embeddings": len(embeddings),
                "embedding_dimension": embeddings.shape[1],
                "umap_components": CLUSTERING_CONFIG['umap']['n_components'],
                "min_cluster_size": CLUSTERING_CONFIG['hdbscan']['min_cluster_size']
            },
            rationale="Using UMAP + HDBSCAN to identify dense groups of semantically similar content without bias"
        )
    
    embeddings = normalize(embeddings)
    
    # UMAP dimensionality reduction
    if progress_manager:
        from ..utils.progress_manager import ProgressStage
        progress_manager.set_stage_status(ProgressStage.CLUSTERING, "Performing dimensionality reduction with UMAP")
    else:
        console.print("Performing dimensionality reduction...")
        
    umap_config = CLUSTERING_CONFIG['umap']
    reducer = umap.UMAP(
        n_neighbors=umap_config['n_neighbors'],
        min_dist=umap_config['min_dist'],
        n_components=umap_config['n_components'],
        metric=umap_config['metric'],
        random_state=umap_config['random_state']
    )
    reduced_embeddings = reducer.fit_transform(embeddings)
    
    if progress_manager:
        progress_manager.log_info(f"Reduced embeddings from {embeddings.shape[1]} to {reduced_embeddings.shape[1]} dimensions")
    
    if progress_reporter:
        progress_reporter.update_metrics({
            "dimensionality_reduction": "complete",
            "reduced_dimensions": reduced_embeddings.shape[1]
        })
    
    # HDBSCAN clustering with adaptive parameters
    if progress_manager:
        progress_manager.set_stage_status(ProgressStage.CLUSTERING, "Performing HDBSCAN clustering")
    else:
        console.print("Performing clustering...")
        
    # Get adaptive parameters based on dataset size
    adaptive_params = get_adaptive_clustering_params(len(embeddings))
    
    # Log the adaptive parameters being used
    if progress_manager:
        progress_manager.log_info(f"Using adaptive clustering params for {len(embeddings)} samples: {adaptive_params}")
    
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=adaptive_params['min_cluster_size'],
        min_samples=adaptive_params['min_samples'],
        metric=adaptive_params['metric'],
        cluster_selection_method=adaptive_params['cluster_selection_method']
    )
    cluster_labels = clusterer.fit_predict(reduced_embeddings)
    
    # Calculate clustering quality metrics
    unique_labels = set(cluster_labels)
    noise_count = sum(1 for label in cluster_labels if label == -1)
    valid_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
    
    # Calculate silhouette score for quality assessment
    silhouette_avg = 0.0
    if valid_clusters > 1 and len(set(cluster_labels)) > 1:
        try:
            silhouette_avg = silhouette_score(reduced_embeddings, cluster_labels)
        except:
            silhouette_avg = 0.0
    
    # Update chunks with cluster IDs
    valid_idx = 0
    for chunk in chunks:
        if chunk.embedding is not None:
            chunk.cluster_id = int(cluster_labels[valid_idx])
            valid_idx += 1
    
    # Create clusters
    cluster_groups = {}
    for chunk in chunks:
        if chunk.cluster_id is not None and chunk.cluster_id != -1:
            if chunk.cluster_id not in cluster_groups:
                cluster_groups[chunk.cluster_id] = []
            cluster_groups[chunk.cluster_id].append(chunk)
    
    clusters = [
        Cluster(cluster_id=cid, chunks=chunks_list, size=len(chunks_list))
        for cid, chunks_list in cluster_groups.items()
    ]
    
    # Analyze cluster composition for participant vs interviewer content and speaker distribution
    participant_clusters = 0
    speaker_diversity_clusters = 0
    total_speakers_across_clusters = set()
    
    for cluster in clusters:
        # Analyze speaker composition in this cluster
        cluster_speakers = set()
        participant_content = 0
        interviewer_content = 0
        
        for chunk in cluster.chunks:
            if hasattr(chunk, '_adaptive_metadata') and chunk._adaptive_metadata:
                speaker = chunk._adaptive_metadata.get('speaker')
                is_interviewer = chunk._adaptive_metadata.get('is_interviewer', False)
                
                if speaker:
                    cluster_speakers.add(speaker)
                    total_speakers_across_clusters.add(speaker)
                    
                    if is_interviewer:
                        interviewer_content += 1
                    else:
                        participant_content += 1
        
        # Store speaker information in cluster for later use
        cluster.speaker_metadata = {
            'speakers': list(cluster_speakers),
            'speaker_count': len(cluster_speakers),
            'participant_chunks': participant_content,
            'interviewer_chunks': interviewer_content,
            'is_participant_focused': participant_content >= 2,
            'has_speaker_diversity': len(cluster_speakers) > 1
        }
        
        if participant_content >= 2:  # Clusters with substantial participant content
            participant_clusters += 1
            
        if len(cluster_speakers) > 1:  # Clusters with multiple speakers
            speaker_diversity_clusters += 1
    
    if progress_manager:
        progress_manager.log_success(f"Found {len(clusters)} clusters from {len(embeddings)} chunks")
        progress_manager.set_stage_status(ProgressStage.CLUSTERING, f"Clustering complete: {len(clusters)} clusters identified")
    else:
        console.print(f"Found {len(clusters)} clusters from {len(embeddings)} chunks")
    
    if progress_reporter:
        progress_reporter.complete_process({
            "clusters_found": len(clusters),
            "noise_chunks": noise_count,
            "participant_focused_clusters": participant_clusters,
            "speaker_diversity_clusters": speaker_diversity_clusters,
            "total_unique_speakers": len(total_speakers_across_clusters),
            "silhouette_score": f"{silhouette_avg:.3f}",
            "largest_cluster": max((c.size for c in clusters), default=0),
            "avg_cluster_size": f"{sum(c.size for c in clusters) // len(clusters) if clusters else 0}"
        })
    
    return chunks, clusters