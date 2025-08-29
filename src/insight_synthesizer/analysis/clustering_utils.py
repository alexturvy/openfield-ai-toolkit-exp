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
    """Return HDBSCAN params tuned to encourage 5-10 meaningful themes."""
    if n_samples < 50:
        min_size = 3
    elif n_samples < 200:
        min_size = 5
    else:
        min_size = 7

    return {
        'min_cluster_size': min_size,
        'min_samples': 2,
        'cluster_selection_method': 'eom',
        'metric': 'euclidean'
    }