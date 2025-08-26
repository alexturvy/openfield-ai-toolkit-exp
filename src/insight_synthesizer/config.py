"""Simplified configuration for Insight Synthesizer."""

# Document processing
PROCESSING_CONFIG = {
    'supported_extensions': ['.txt', '.rtf', '.docx', '.pdf'],
    'embedding_model': 'all-MiniLM-L6-v2',
    'max_chunk_size': 1500,
    'min_chunk_size': 200,
}

# Fixed clustering parameters that work for 5-50 documents
CLUSTERING_CONFIG = {
    'umap': {
        'n_neighbors': min(10, 15),  # Will be adjusted based on data
        'min_dist': 0.1,
        'n_components': 5,
        'metric': 'cosine',
        'random_state': 42
    },
    'hdbscan': {
        'min_cluster_size': 3,
        'min_samples': 2,
        'metric': 'euclidean',
        'cluster_selection_method': 'eom'
    }
}

# Analysis lenses with descriptions and specific prompts
ANALYSIS_LENSES = {
    'pain_points': {
        'description': 'Identify user frustrations and challenges',
        'focus': 'Focus on identifying frustrations, obstacles, and negative experiences',
        'extra_field': ('severity', 'Rate the severity as "low", "medium", or "high"')
    },
    'opportunities': {
        'description': 'Find potential improvements and enhancements',
        'focus': 'Focus on improvements, enhancements, and positive potential',
        'extra_field': ('potential_impact', 'Assess potential impact as "low", "medium", or "high"')
    },
    'jobs_to_be_done': {
        'description': 'Understand core user motivations and goals',
        'focus': 'Focus on core user motivations and goals',
        'extra_field': ('user_context', 'Describe when users typically need this job done')
    },
    'mental_models': {
        'description': 'Uncover user assumptions and beliefs',
        'focus': 'Focus on user assumptions and beliefs about the system',
        'extra_field': ('accuracy', 'Assess if this model is "accurate", "partially accurate", or "inaccurate"')
    },
    'decision_factors': {
        'description': 'Identify key adoption/abandonment factors',
        'focus': 'Focus on factors influencing adoption or abandonment decisions',
        'extra_field': ('influence_level', 'Rate influence as "low", "medium", or "high"')
    },
    'feature_focus': {
        'description': 'Analyze feedback about specific features',
        'focus': 'Focus on specific feature feedback and usability',
        'extra_field': ('user_sentiment', 'Assess sentiment as "positive", "neutral", or "negative"')
    }
}

# Keep ANALYSIS_LENSES as is - it's good

# Legacy LLM configuration for compatibility
LLM_CONFIG = {
    'model_name': 'mistral',
    'base_url': 'http://localhost:11434',
    'timeout': 120,
    'retry_delay': 5,
    'max_retries': 3,
    'temperature': 0.1,
}

def get_config():
    """Get complete configuration dictionary."""
    return {
        'processing': PROCESSING_CONFIG,
        'llm': LLM_CONFIG,
        'clustering': CLUSTERING_CONFIG,
        'lenses': ANALYSIS_LENSES
    }

def get_lens_config(lens_name: str):
    """Get configuration for specific analysis lens."""
    if lens_name not in ANALYSIS_LENSES:
        raise ValueError(f"Unknown lens: {lens_name}. Available: {list(ANALYSIS_LENSES.keys())}")
    
    return ANALYSIS_LENSES[lens_name]