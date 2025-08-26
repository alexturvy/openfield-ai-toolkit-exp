"""Utilities for clustering configuration."""


def get_min_cluster_size(n_samples: int) -> int:
    """
    Dynamically determine minimum cluster size based on dataset size.
    
    Args:
        n_samples: Number of samples in dataset
        
    Returns:
        Appropriate minimum cluster size
    """
    if n_samples < 10:
        return 2  # Very small dataset
    elif n_samples < 50:
        return min(3, n_samples // 3)  # Small dataset
    elif n_samples < 100:
        return min(5, n_samples // 10)  # Medium dataset
    else:
        return min(10, n_samples // 20)  # Large dataset


def get_adaptive_clustering_params(n_samples: int) -> dict:
    """
    Get clustering parameters adapted to dataset size.
    
    This is an improved version that handles edge cases better.
    
    Args:
        n_samples: Number of samples to cluster
        
    Returns:
        Dictionary of HDBSCAN parameters optimized for the dataset size
    """
    
    if n_samples < 5:
        # Very small datasets - use leaf clustering method
        return {
            'min_cluster_size': 2,
            'min_samples': 1,
            'cluster_selection_method': 'leaf',  # More aggressive clustering
            'metric': 'euclidean'
        }
    elif n_samples < 20:
        # Small datasets
        return {
            'min_cluster_size': min(3, n_samples // 3),
            'min_samples': 2,
            'cluster_selection_method': 'eom',
            'metric': 'euclidean'
        }
    elif n_samples < 50:
        # Medium datasets
        return {
            'min_cluster_size': min(5, n_samples // 8),
            'min_samples': 3,
            'cluster_selection_method': 'eom',
            'metric': 'euclidean'
        }
    else:
        # Large datasets
        return {
            'min_cluster_size': min(10, n_samples // 10),
            'min_samples': 5,
            'cluster_selection_method': 'eom',
            'metric': 'euclidean'
        }