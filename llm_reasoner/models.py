"""Model configuration and registry for reasoning chains."""

import os
import json
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass

try:
    from litellm import completion
    from litellm.utils import ModelResponse
except ImportError:
    raise ImportError(
        "litellm is required for ReasonChain. "
        "Install it with `pip install litellm>=1.0.0`"
    )

from pydantic import BaseModel, ConfigDict, field_validator, Field

# Constants for persistence
CONFIG_DIR = Path.home() / ".llm_reasoner"
CONFIG_FILE = CONFIG_DIR / "models.json"

class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    name: str = Field(..., description="Name of the model")
    provider: str = Field(..., description="Provider of the model")
    context_window: Optional[int] = Field(None, description="Maximum context window size")
    default: bool = Field(False, description="Whether this is the default model")

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "gpt-4o",
                    "provider": "openai",
                    "context_window": 128000,
                    "default": True
                }
            ]
        }
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate model name."""
        if not v or not isinstance(v, str):
            raise ValueError("Model name cannot be empty")
        return v.strip()

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider name."""
        # Allow any provider string to support custom providers
        return v.lower()

    @field_validator('context_window')
    @classmethod
    def validate_context_window(cls, v: Optional[int]) -> Optional[int]:
        """Validate context window size."""
        if v is not None and v <= 0:
            raise ValueError("Context window must be a positive integer")
        return v

class ModelRegistry:
    """Registry managing available models and their configurations."""

    def __init__(self):
        self._models = self._initialize_models()
        self._load_persisted_models()
        self._set_initial_default()

    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """Initialize available models."""
        models = {
            'gpt-4o': ModelConfig(
                name='gpt-4o',
                provider='openai',
                context_window=128000,
            ),
            'gpt-4o-mini': ModelConfig(
                name='gpt-4o-mini',
                provider='openai',
                context_window=128000,
            ),
            'claude-3-5-sonnet-latest': ModelConfig(
                name='claude-3-5-sonnet-latest',
                provider='anthropic',
                context_window=200000,
            ),
            'claude-3-5-haiku-latest': ModelConfig(
                name='claude-3-5-haiku-latest',
                provider='anthropic',
                context_window=200000,
            ),
            'gemini-1.5-pro': ModelConfig(
                name='gemini-1.5-pro',
                provider='google',
                context_window=1000000,
            ),
            'gemini-1.5-flash': ModelConfig(
                name='gemini-1.5-flash',
                provider='google',
                context_window=1000000,
            ),
            'deepseek-chat': ModelConfig(
                name='deepseek-chat',
                provider='deepseek',
                context_window=64000,
            ),
        }
        return models

    def _load_persisted_models(self) -> None:
        """Load persisted models from the configuration file."""
        if not CONFIG_FILE.exists():
            return

        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                for name, config_data in data.items():
                    self._models[name] = ModelConfig(**config_data)
        except (json.JSONDecodeError, Exception):
            # Silently fail and use defaults if config is corrupted
            pass

    def _save_models(self) -> None:
        """Save current model configurations to the configuration file."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            data = {name: config.model_dump() for name, config in self._models.items()}
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception:
            # Silently fail if saving is not possible
            pass

    def _set_initial_default(self) -> None:
        """Set an initial default model based on available API keys."""
        if not any(model.default for model in self._models.values()):
            if os.getenv('OPENAI_API_KEY'):
                default_model = 'gpt-4o-mini'
            elif os.getenv('ANTHROPIC_API_KEY'):
                default_model = 'claude-3-5-sonnet-latest'
            elif os.getenv('GOOGLE_API_KEY'):
                default_model = 'gemini-1.5-flash'
            else:
                default_model = 'gpt-4o-mini'

            if default_model in self._models:
                model_dict = self._models[default_model].model_dump()
                model_dict['default'] = True
                self._models[default_model] = ModelConfig(**model_dict)

    def register_model(self, name: str, provider: str, context_window: Optional[int] = None) -> None:
        """Register a new model with the registry.

        Args:
            name: Name of the model
            provider: Provider of the model (can be custom)
            context_window: Optional maximum context window size
        """
        self._models[name] = ModelConfig(
            name=name,
            provider=provider,
            context_window=context_window,
            default=False
        )
        self._save_models()

    def get_model(self, model_name: str) -> ModelConfig:
        """Get model configuration by name."""
        if model_name not in self._models:
            raise ValueError(f"Model {model_name} not found in available models")
        return self._models[model_name]

    def get_default_model(self) -> ModelConfig:
        """Get the current default model configuration."""
        default_model = next(
            (model for model in self._models.values() if model.default),
            None
        )
        if not default_model:
            raise RuntimeError("No default model configured")
        return default_model

    def set_default_model(self, model_name: str) -> None:
        """Set a new default model."""
        if model_name not in self._models:
            raise ValueError(f"Model {model_name} not found in available models")

        for name, model in self._models.items():
            model_dict = model.model_dump()
            model_dict['default'] = (name == model_name)
            self._models[name] = ModelConfig(**model_dict)
        self._save_models()

    def list_models(self) -> Dict[str, ModelConfig]:
        """List all available models."""
        return self._models

# Initialize the global model registry
model_registry = ModelRegistry()