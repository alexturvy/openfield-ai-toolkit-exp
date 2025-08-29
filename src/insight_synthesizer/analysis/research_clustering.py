"""Research-aware clustering that balances semantic similarity with research relevance."""

import numpy as np
from typing import List, Optional, Tuple, Dict
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
import umap
import hdbscan

from .clustering import Cluster
from .clustering_utils import get_min_cluster_size
from .embeddings import TextChunk
from ..research.goal_manager import ResearchGoalManager
from ..utils import ProgressReporter
from rich.console import Console

console = Console()


class ResearchAwareClusterer:
    """Clustering that balances semantic similarity with research relevance."""
    
    def __init__(self, goal_manager: ResearchGoalManager,
                 semantic_weight: float = 0.3,
                 research_weight: float = 0.7,
                 progress_reporter: Optional[ProgressReporter] = None):
        """
        Initialize research-aware clusterer.
        
        Args:
            goal_manager: Research goal manager with questions and embeddings
            semantic_weight: Weight for semantic similarity (0-1)
            research_weight: Weight for research relevance (0-1)
            progress_reporter: Optional progress reporter
        """
        self.goal_manager = goal_manager
        self.semantic_weight = semantic_weight
        self.research_weight = research_weight
        self.progress_reporter = progress_reporter or ProgressReporter()
        
        # Validate weights
        if not np.isclose(semantic_weight + research_weight, 1.0):
            total = semantic_weight + research_weight
            self.semantic_weight = semantic_weight / total
            self.research_weight = research_weight / total
            console.print(f"[yellow]Normalized weights to {self.semantic_weight:.2f}/{self.research_weight:.2f}[/]")
    
    def create_hybrid_embeddings(self, chunks: List[TextChunk], 
                                embeddings: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create embeddings that combine semantic and research relevance.
        
        Args:
            chunks: List of text chunks
            embeddings: Semantic embeddings for chunks
            
        Returns:
            Tuple of (hybrid_embeddings, relevance_scores)
        """
        # Calculate research relevance scores for each chunk
        relevance_scores = np.array([
            self.goal_manager.calculate_relevance_score(chunk.text) 
            for chunk in chunks
        ])
        
        # Log relevance distribution
        # Debug: Relevance scores calculated
        
        # Create research-oriented embeddings
        research_embeddings = self._create_research_embeddings(chunks, relevance_scores)
        
        # Normalize both embedding sets
        semantic_normalized = normalize(embeddings)
        research_normalized = normalize(research_embeddings)
        
        # Create weighted hybrid
        hybrid = (self.semantic_weight * semantic_normalized + 
                 self.research_weight * research_normalized)
        
        # Normalize final hybrid embeddings
        hybrid_normalized = normalize(hybrid)
        
        return hybrid_normalized, relevance_scores
    
    def _create_research_embeddings(self, chunks: List[TextChunk], 
                                   relevance_scores: np.ndarray) -> np.ndarray:
        """
        Create pseudo-embeddings based on research relevance.
        
        Args:
            chunks: Text chunks
            relevance_scores: Relevance score for each chunk
            
        Returns:
            Research-oriented embeddings
        """
        research_embeddings = []
        
        for i, (chunk, score) in enumerate(zip(chunks, relevance_scores)):
            # Identify which research questions this chunk addresses
            relevant_qs = self.goal_manager.identify_relevant_questions(chunk.text)
            
            if relevant_qs and score > 0.3:  # Has meaningful relevance
                # Create weighted combination of relevant question embeddings
                weights = np.array([r[1] for r in relevant_qs])
                indices = [r[0] for r in relevant_qs]
                
                # Normalize weights
                weights = weights / weights.sum()
                
                # Weighted average of question embeddings
                weighted_embedding = np.zeros_like(self.goal_manager.question_embeddings[0])
                for idx, weight in zip(indices, weights):
                    if idx < len(self.goal_manager.question_embeddings):
                        weighted_embedding += weight * self.goal_manager.question_embeddings[idx]
                
                # Scale by overall relevance score
                weighted_embedding *= score
                research_embeddings.append(weighted_embedding)
            else:
                # Low relevance - use average of all questions with low weight
                avg_embedding = np.mean(self.goal_manager.question_embeddings, axis=0)
                research_embeddings.append(avg_embedding * 0.1)  # Low weight
        
        return np.array(research_embeddings)
    
    def cluster_with_research_focus(self, chunks: List[TextChunk], 
                                   embeddings: np.ndarray,
                                   min_cluster_size: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        Perform clustering with research awareness.
        
        Args:
            chunks: Text chunks to cluster
            embeddings: Semantic embeddings
            min_cluster_size: Minimum cluster size (auto-calculated if None)
            
        Returns:
            Tuple of (cluster_labels, reduced_embeddings, clustering_info)
        """
        # Create hybrid embeddings
        self.progress_reporter.update_metrics({
            "status": "Creating research-aware embeddings"
        })
        hybrid_embeddings, relevance_scores = self.create_hybrid_embeddings(chunks, embeddings)
        
        # Store relevance scores in chunks for later use
        for chunk, score in zip(chunks, relevance_scores):
            chunk.research_relevance = score
        
        # Apply UMAP for dimensionality reduction
        self.progress_reporter.update_metrics({
            "status": "Reducing dimensionality with research awareness"
        })
        
        # Adjust UMAP parameters based on data size
        n_neighbors = min(15, len(chunks) - 1)
        n_components = min(5, len(chunks) - 2)
        
        reducer = umap.UMAP(
            n_neighbors=n_neighbors,
            n_components=n_components,
            min_dist=0.1,
            metric='cosine',
            random_state=42,
            verbose=False
        )
        
        reduced_embeddings = reducer.fit_transform(hybrid_embeddings)
        
        # Determine min_cluster_size if not provided
        if min_cluster_size is None:
            min_cluster_size = get_min_cluster_size(len(chunks))
        
        # Adjust for research-aware clustering
        # Lower threshold slightly to account for research-focused grouping
        adjusted_min_cluster_size = max(2, int(min_cluster_size * 0.8))
        
        self.progress_reporter.update_metrics({
            "status": f"Clustering with min_size={adjusted_min_cluster_size}"
        })
        
        # Cluster with HDBSCAN
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=adjusted_min_cluster_size,
            min_samples=max(1, adjusted_min_cluster_size // 2),
            metric='euclidean',
            cluster_selection_method='eom',
            allow_single_cluster=True
        )
        
        cluster_labels = clusterer.fit_predict(reduced_embeddings)
        
        # Post-process: rescue high-relevance noise points
        cluster_labels = self._post_process_clusters(
            chunks, cluster_labels, hybrid_embeddings, relevance_scores
        )
        
        # Calculate clustering info
        clustering_info = self._calculate_clustering_info(
            cluster_labels, relevance_scores, chunks
        )
        
        return cluster_labels, reduced_embeddings, clustering_info
    
    def _post_process_clusters(self, chunks: List[TextChunk], 
                              cluster_labels: np.ndarray,
                              embeddings: np.ndarray,
                              relevance_scores: np.ndarray) -> np.ndarray:
        """
        Post-process clusters to ensure research-relevant content isn't isolated.
        
        Args:
            chunks: Text chunks
            cluster_labels: Initial cluster assignments
            embeddings: Hybrid embeddings
            relevance_scores: Research relevance scores
            
        Returns:
            Adjusted cluster labels
        """
        # Find noise points with high research relevance
        noise_mask = cluster_labels == -1
        high_relevance_threshold = np.percentile(relevance_scores[relevance_scores > 0], 60)
        high_relevance_mask = relevance_scores > high_relevance_threshold
        
        rescue_candidates = np.where(noise_mask & high_relevance_mask)[0]
        
        if len(rescue_candidates) > 0 and np.any(cluster_labels >= 0):
            # Debug: Attempting to rescue high-relevance noise points
            
            # Try to assign to nearest cluster
            for idx in rescue_candidates:
                chunk_embedding = embeddings[idx]
                
                # Calculate distances to all clusters
                min_distance = float('inf')
                best_cluster = -1
                
                for cluster_id in np.unique(cluster_labels):
                    if cluster_id == -1:
                        continue
                    
                    cluster_mask = cluster_labels == cluster_id
                    cluster_embeddings = embeddings[cluster_mask]
                    
                    # Use average distance to cluster members
                    distances = np.linalg.norm(
                        cluster_embeddings - chunk_embedding, axis=1
                    )
                    avg_distance = np.mean(distances)
                    
                    if avg_distance < min_distance:
                        min_distance = avg_distance
                        best_cluster = cluster_id
                
                # Assign if reasonably close (within 1 std dev of cluster distances)
                if best_cluster != -1:
                    cluster_mask = cluster_labels == best_cluster
                    cluster_embeddings = embeddings[cluster_mask]
                    
                    # Calculate threshold based on cluster's internal distances
                    internal_distances = []
                    for i, emb1 in enumerate(cluster_embeddings):
                        for j, emb2 in enumerate(cluster_embeddings):
                            if i < j:
                                internal_distances.append(np.linalg.norm(emb1 - emb2))
                    
                    if internal_distances:
                        threshold = np.mean(internal_distances) + np.std(internal_distances)
                        
                        if min_distance <= threshold:
                            cluster_labels[idx] = best_cluster
                            # Debug: Rescued high-relevance chunk
        
        return cluster_labels
    
    def _calculate_clustering_info(self, cluster_labels: np.ndarray,
                                  relevance_scores: np.ndarray,
                                  chunks: List[TextChunk]) -> Dict:
        """
        Calculate statistics about the clustering results.
        
        Args:
            cluster_labels: Cluster assignments
            relevance_scores: Research relevance scores
            chunks: Text chunks
            
        Returns:
            Dictionary with clustering statistics
        """
        unique_clusters = set(cluster_labels[cluster_labels >= 0])
        
        info = {
            'total_clusters': len(unique_clusters),
            'noise_points': np.sum(cluster_labels == -1),
            'avg_relevance_by_cluster': {},
            'high_relevance_clusters': 0,
            'research_focused_clusters': 0
        }
        
        for cluster_id in unique_clusters:
            cluster_mask = cluster_labels == cluster_id
            cluster_relevance = relevance_scores[cluster_mask]
            
            avg_relevance = np.mean(cluster_relevance)
            info['avg_relevance_by_cluster'][int(cluster_id)] = float(avg_relevance)
            
            # Count high relevance clusters
            if avg_relevance > 0.5:
                info['high_relevance_clusters'] += 1
            
            # Check if cluster is research-focused (>70% high relevance chunks)
            high_relevance_ratio = np.sum(cluster_relevance > 0.4) / len(cluster_relevance)
            if high_relevance_ratio > 0.7:
                info['research_focused_clusters'] += 1
        
        return info


def create_research_aware_clusters(chunks: List[TextChunk], 
                                  embeddings: np.ndarray,
                                  goal_manager: ResearchGoalManager,
                                  progress_reporter: Optional[ProgressReporter] = None) -> List[Cluster]:
    """
    Helper function to create research-aware clusters.
    
    Args:
        chunks: Text chunks to cluster
        embeddings: Semantic embeddings
        goal_manager: Research goal manager
        progress_reporter: Optional progress reporter
        
    Returns:
        List of Cluster objects
    """
    clusterer = ResearchAwareClusterer(
        goal_manager, 
        progress_reporter=progress_reporter
    )
    
    cluster_labels, reduced_embeddings, clustering_info = clusterer.cluster_with_research_focus(
        chunks, embeddings
    )
    
    # Log clustering info
    if progress_reporter:
        # Debug: Research-aware clustering complete
        pass
    
    # Create Cluster objects
    clusters = []
    for cluster_id in set(cluster_labels[cluster_labels >= 0]):
        cluster_mask = cluster_labels == cluster_id
        cluster_chunks = [chunks[i] for i in np.where(cluster_mask)[0]]
        
        # Calculate cluster-level research relevance
        cluster_relevance = np.mean([
            getattr(chunk, 'research_relevance', 0) for chunk in cluster_chunks
        ])
        
        cluster = Cluster(
            cluster_id=int(cluster_id),
            chunks=cluster_chunks,
            size=len(cluster_chunks)
        )
        
        # Add research metadata
        cluster.research_relevance = cluster_relevance
        cluster.addressed_questions = _identify_cluster_questions(
            cluster_chunks, goal_manager
        )
        
        clusters.append(cluster)
    
    # Sort by research relevance
    clusters.sort(key=lambda c: c.research_relevance, reverse=True)
    
    return clusters


def _identify_cluster_questions(chunks: List[TextChunk], 
                                goal_manager: ResearchGoalManager) -> List[int]:
    """Identify which research questions a cluster addresses."""
    # Combine all chunk texts
    combined_text = " ".join([chunk.text for chunk in chunks])
    
    # Get relevant questions with high threshold
    relevant_questions = goal_manager.identify_relevant_questions(
        combined_text, threshold=0.5
    )
    
    return [q[0] for q in relevant_questions]