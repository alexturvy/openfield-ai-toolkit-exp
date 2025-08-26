"""Quick test script to verify commercial model integration."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from insight_synthesizer.llm_providers import get_llm_provider

def test_providers():
    """Test different LLM providers."""
    
    # Test configurations
    configs = {
        "ollama": {
            'provider': 'ollama',
            'model_name': 'mistral',
            'base_url': 'http://localhost:11434',
            'temperature': 0.1
        },
        "openai": {
            'provider': 'openai',
            'model_name': 'gpt-3.5-turbo',  # Cheaper for testing
            'api_key': os.getenv('OPENAI_API_KEY'),
            'temperature': 0.1
        },
        "anthropic": {
            'provider': 'anthropic', 
            'model_name': 'claude-3-haiku-20240307',  # Cheaper for testing
            'api_key': os.getenv('ANTHROPIC_API_KEY'),
            'temperature': 0.1
        }
    }
    
    test_prompt = """Analyze this user quote and return JSON with structure:
    {
        "theme": "main theme",
        "sentiment": "positive/negative/neutral"
    }
    
    Quote: "The login process is really confusing. I keep forgetting where the button is."
    """
    
    for provider_name, config in configs.items():
        print(f"\n{'='*50}")
        print(f"Testing {provider_name.upper()} provider")
        print(f"{'='*50}")
        
        try:
            if provider_name != "ollama" and not config.get('api_key'):
                print(f"⚠️  Skipping {provider_name} - no API key found")
                continue
                
            provider = get_llm_provider(config)
            result = provider.generate(
                test_prompt, 
                "You are a UX researcher. Respond only with valid JSON."
            )
            
            print(f"✅ Success!")
            print(f"Response: {result}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Set API keys as environment variables or directly here for testing
    # os.environ['OPENAI_API_KEY'] = 'your-key-here'
    # os.environ['ANTHROPIC_API_KEY'] = 'your-key-here'
    
    test_providers()