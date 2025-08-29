"""
Unified LLM Client - The ONLY way to call any LLM in this project.
Location: src/insight_synthesizer/llm/client.py

RULES:
1. This is the ONLY file that imports OpenAI or makes Ollama HTTP calls
2. Every other file must use this client
3. Respects USE_COMMERCIAL_MODEL environment variable
4. Falls back gracefully if primary choice fails
"""

import os
import json
import time
import shutil
import subprocess
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from rich.console import Console

console = Console()


@dataclass
class LLMResponse:
    """Standard response from any LLM."""
    content: str
    model_used: str
    provider: str
    response_time: float
    success: bool
    error: Optional[str] = None


class UnifiedLLMClient:
    """
    Singleton LLM client that handles all model interactions.
    
    Usage:
        from insight_synthesizer.llm.client import get_llm_client
        
        client = get_llm_client()
        response = client.generate("What is 2+2?")
        print(response.content)
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the client based on environment settings."""
        if self._initialized:
            return
            
        self.use_commercial = os.environ.get('USE_COMMERCIAL_MODEL', '').lower() == 'true'
        self.provider = None
        self.model = None
        
        # Try commercial first if requested
        if self.use_commercial:
            if self._try_init_openai():
                self._initialized = True
                return
            console.print("[yellow]OpenAI unavailable, trying Ollama...[/]")
        
        # Try Ollama
        if self._try_init_ollama():
            self._initialized = True
            return
            
        # Both failed
        raise RuntimeError(
            "No LLM available. Either:\n"
            "1. Set OPENAI_API_KEY and USE_COMMERCIAL_MODEL=true\n"
            "2. Install Ollama: curl -fsSL https://ollama.com/install.sh | sh"
        )
    
    def _try_init_openai(self) -> bool:
        """Try to initialize OpenAI."""
        try:
            api_key = os.environ.get('OPENAI_API_KEY', '').strip()
            if not api_key or api_key == 'your-key-here':
                console.print("[yellow]No valid OpenAI API key found[/]")
                return False
            
            # Import here to avoid dependency if not using OpenAI
            from openai import OpenAI
            
            self.client = OpenAI(api_key=api_key)
            self.provider = 'openai'
            # Normalize model env to avoid smart quotes / stray characters from copy-paste
            self.model = self._normalize_env_string(os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'))
            
            # Test the connection
            try:
                # Use an ASCII-only, minimal test prompt to avoid locale/encoding issues
                test_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "ok"}],
                    max_tokens=5
                )
            except UnicodeEncodeError as ue:
                # Gracefully handle terminals/shells with non-UTF-8 locales or smart-quote env values
                console.print(
                    "[yellow]OpenAI test call hit a Unicode encoding issue; assuming client is available.\n"
                    "Hint: ensure your shell uses UTF-8 (e.g., export LC_ALL=en_US.UTF-8; export LANG=en_US.UTF-8)\n"
                    "and avoid smart quotes in OPENAI_MODEL.[/]"
                )
                # Consider initialization successful despite test-call encoding error
                console.print(f"[green]✓ Using OpenAI ({self.model})[/]")
                return True
            
            console.print(f"[green]✓ Using OpenAI ({self.model})[/]")
            return True
            
        except Exception as e:
            console.print(f"[yellow]OpenAI init failed: {e}[/]")
            return False
    
    def _try_init_ollama(self) -> bool:
        """Try to initialize Ollama."""
        try:
            # Check if ollama is installed
            if not shutil.which('ollama'):
                console.print("[yellow]Ollama not installed[/]")
                return False
            
            # Check if server is running
            import requests
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code != 200:
                    raise Exception("Not running")
            except:
                # Try to start it
                console.print("[yellow]Starting Ollama server...[/]")
                subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(5)
                
                # Check again
                try:
                    response = requests.get("http://localhost:11434/api/tags", timeout=2)
                    if response.status_code != 200:
                        return False
                except:
                    return False
            
            # Ensure model is available
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True
            )
            
            # Allow overriding the local model via env; default to mistral
            model_name = os.environ.get('OLLAMA_MODEL', 'mistral').strip()
            if model_name not in result.stdout:
                console.print(f"[yellow]Pulling {model_name} model (this may take a minute)...[/]")
                subprocess.run(['ollama', 'pull', model_name], check=True)
            
            self.provider = 'ollama'
            self.model = model_name
            self.base_url = 'http://localhost:11434'
            
            console.print(f"[yellow]✓ Using Ollama ({self.model}) - will be slower[/]")
            return True
            
        except Exception as e:
            console.print(f"[yellow]Ollama init failed: {e}[/]")
            return False
    
    def generate(self, 
                prompt: str,
                system: Optional[str] = None,
                temperature: float = 0.1,
                max_tokens: int = 2000,
                json_mode: bool = False) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt
            temperature: 0.0 = deterministic, 1.0 = creative
            max_tokens: Maximum response length
            json_mode: Whether to force JSON output
            
        Returns:
            LLMResponse with content and metadata
        """
        start_time = time.time()
        
        try:
            if self.provider == 'openai':
                return self._generate_openai(
                    prompt, system, temperature, max_tokens, json_mode
                )
            elif self.provider == 'ollama':
                return self._generate_ollama(
                    prompt, system, temperature, max_tokens, json_mode
                )
            else:
                raise RuntimeError("No LLM provider initialized")
                
        except Exception as e:
            return LLMResponse(
                content="",
                model_used=self.model or "unknown",
                provider=self.provider or "unknown",
                response_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    def _generate_openai(self, prompt: str, system: Optional[str],
                        temperature: float, max_tokens: int,
                        json_mode: bool) -> LLMResponse:
        """Generate using OpenAI."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        start_time = time.time()
        response = self.client.chat.completions.create(**kwargs)
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model_used=self.model,
            provider='openai',
            response_time=time.time() - start_time,
            success=True
        )
    
    def _generate_ollama(self, prompt: str, system: Optional[str],
                        temperature: float, max_tokens: int,
                        json_mode: bool) -> LLMResponse:
        """Generate using Ollama."""
        import requests
        
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        # Cap prediction length for local models to avoid long-running generations
        try:
            max_local_predict = int(os.environ.get('OLLAMA_NUM_PREDICT', '1024'))
        except ValueError:
            max_local_predict = 1024
        num_predict = min(max_tokens, max_local_predict)
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict
            }
        }
        
        if json_mode:
            payload["format"] = "json"
        
        start_time = time.time()
        # Allow configurable timeout for slower local generations
        try:
            timeout_seconds = int(os.environ.get('OLLAMA_TIMEOUT', '300'))
        except ValueError:
            timeout_seconds = 300
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=timeout_seconds
        )
        response.raise_for_status()
        
        return LLMResponse(
            content=response.json()["response"],
            model_used=self.model,
            provider='ollama',
            response_time=time.time() - start_time,
            success=True
        )
    
    def generate_json(self, 
                     prompt: str,
                     system: Optional[str] = None,
                     temperature: float = 0.1,
                     max_tokens: int = 2000) -> tuple[bool, Dict[str, Any]]:
        """
        Generate JSON response from the LLM.
        
        Args:
            prompt: The prompt (should ask for JSON)
            system: Optional system prompt
            temperature: Temperature setting
            max_tokens: Max response length
            
        Returns:
            Tuple of (success: bool, data: dict or error_dict)
        """
        # Ensure system prompt mentions JSON
        if system:
            system = f"{system} Always respond with valid JSON."
        else:
            system = "You are a helpful assistant. Always respond with valid JSON."
        
        response = self.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True
        )
        
        if not response.success:
            return False, {"error": response.error}
        
        try:
            data = json.loads(response.content)
            return True, data
        except json.JSONDecodeError as e:
            return False, {"error": f"Invalid JSON: {e}", "raw": response.content}
    
    @classmethod
    def reset(cls):
        """Reset the singleton (useful for testing)."""
        cls._instance = None
        cls._initialized = False
    
    @classmethod
    def test_connection(cls) -> bool:
        """Test if LLM is working."""
        try:
            client = cls()
            response = client.generate("Say 'yes'", max_tokens=10)
            return response.success and 'yes' in response.content.lower()
        except:
            return False

    @staticmethod
    def _normalize_env_string(value: Optional[str]) -> str:
        """Normalize environment-provided strings to avoid Unicode smart quotes and stray wrappers.
        Ensures ASCII-safe model names and strips surrounding quotes/spaces.
        """
        if not value:
            return 'gpt-4o-mini'
        # Replace common smart quotes with ASCII equivalents
        normalized = (
            value
            .replace('\u2018', "'")  # left single quote
            .replace('\u2019', "'")  # right single quote
            .replace('\u201C', '"')  # left double quote
            .replace('\u201D', '"')  # right double quote
        )
        # Also replace literal characters if they made it through
        normalized = normalized.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"')
        # Strip any surrounding quotes and whitespace
        normalized = normalized.strip().strip("'\"")
        return normalized or 'gpt-4o-mini'


def get_llm_client() -> UnifiedLLMClient:
    """Get the singleton LLM client."""
    return UnifiedLLMClient()


def test_llm() -> bool:
    """Quick test to verify LLM is working."""
    return UnifiedLLMClient.test_connection()


# Example usage for testing
if __name__ == "__main__":
    # Test the client
    client = get_llm_client()
    
    # Test text generation
    print("Testing text generation...")
    response = client.generate("What is 2+2?")
    if response.success:
        print(f"✓ Text generation works: {response.content}")
        print(f"  Model: {response.model_used} via {response.provider}")
        print(f"  Time: {response.response_time:.2f}s")
    else:
        print(f"✗ Text generation failed: {response.error}")
    
    # Test JSON generation
    print("\nTesting JSON generation...")
    success, data = client.generate_json(
        "List 3 colors as JSON array with 'colors' key"
    )
    if success:
        print(f"✓ JSON generation works: {data}")
    else:
        print(f"✗ JSON generation failed: {data}")