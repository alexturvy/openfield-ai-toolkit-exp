"""Configuration for commercial model testing."""

import os
from typing import Dict, Any

# Base configuration - import everything from original
from .config import *

# Override LLM configuration for commercial model
LLM_CONFIG = {
    'provider': 'openai',  # 'openai', 'anthropic', 'ollama'
    'model_name': 'gpt-4o',  # or 'gpt-3.5-turbo', 'claude-3-opus-20240229'
    'api_key': os.getenv('OPENAI_API_KEY'),  # or 'ANTHROPIC_API_KEY'
    'temperature': 0.1,
    'max_tokens': 500,
    'timeout': 30,
    'retry_delay': 2,
    'max_retries': 3,
}

# For Anthropic Claude
# LLM_CONFIG = {
#     'provider': 'anthropic',
#     'model_name': 'claude-3-opus-20240229',
#     'api_key': os.getenv('ANTHROPIC_API_KEY'),
#     'temperature': 0.1,
#     'max_tokens': 500,
#     'timeout': 30,
#     'retry_delay': 2,
#     'max_retries': 3,
# }