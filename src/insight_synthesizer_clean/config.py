"""Typed configuration for the clean pipeline with env overrides."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    provider: str = "ollama"  # or "openai"
    model: str = "mistral"
    temperature: float = 0.1


@dataclass
class ProcessingConfig:
    max_chunk_chars: int = 1500
    min_chunk_chars: int = 200


@dataclass
class PipelineConfig:
    llm: LLMConfig = None  # type: ignore[assignment]
    processing: ProcessingConfig = None  # type: ignore[assignment]

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        cfg = cls(llm=LLMConfig(), processing=ProcessingConfig())
        cfg.llm.provider = os.getenv("LLM_PROVIDER", cfg.llm.provider)
        cfg.llm.model = os.getenv("LLM_MODEL", cfg.llm.model)
        t = os.getenv("LLM_TEMPERATURE")
        if t is not None:
            try:
                cfg.llm.temperature = float(t)
            except ValueError:
                pass
        return cfg

