# GEMINI.md - LLM-Reasoner

This document provides project-specific context and instructions for the LLM-Reasoner repository.

## Project Overview

**LLM-Reasoner** is a Python-based tool designed to transform standard Large Language Models (LLMs) into methodical thinkers using dynamic Chain-of-Thought (CoT), reflection, and verbal reinforcement learning. It achieves this by wrapping LLM calls in a structured reasoning loop.

### Core Architecture

- **Reasoning Engine (`llm_reasoner/engine.py`):** The heart of the project. It manages the `ReasonChain`, which iteratively prompts the LLM to provide step-by-step reasoning in a structured JSON format.
- **Model Registry (`llm_reasoner/models.py`):** Uses **LiteLLM** to provide a unified interface for multiple providers (OpenAI, Anthropic, Google, Azure, etc.). Model configurations and default settings are persisted in `~/.llm_reasoner/models.json`.
- **System Prompt (`llm_reasoner/settings.py`):** Defines the strict instructions that force the LLM to output its thinking process, confidence scores, and next actions.
- **Interfaces:**
    - **CLI (`llm_reasoner/commands.py`):** A `click`-based command-line interface.
    - **UI (`llm_reasoner/interface.py`):** A `streamlit` web dashboard for interactive reasoning.

### Key Technologies

- **Python 3.8+**
- **LiteLLM**: Multi-provider LLM support.
- **Pydantic**: Data validation and model configuration.
- **Streamlit**: Web-based user interface.
- **Rich**: Enhanced terminal output and progress bars.
- **Click**: Command-line argument parsing.
- **Pytest**: Testing framework.

## Building and Running

### Installation

```bash
# Basic installation
pip install .

# Development installation with all dependencies
pip install -e .[dev]
```

### Key Commands

- **Run Reasoning (CLI):** `llm-reasoner reason "Your question here"`
    - Options: `--model`, `--max-tokens`, `--temperature`, `--min-steps`.
- **Launch UI:** `llm-reasoner ui`
- **List Models:** `llm-reasoner models`
- **Register Custom Model:** `llm-reasoner register-model <name> <provider> --context-window <size>`
- **Set Default Model:** `llm-reasoner set-model <model_name>`

### Environment Variables

The project respects standard LLM provider environment variables:
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, etc.
- `LLM_REASONER_MAX_TOKENS`: Default max tokens for reasoning steps.
- `LLM_REASONER_TEMPERATURE`: Default temperature.
- `LLM_REASONER_MIN_STEPS`: Minimum reasoning steps to enforce.

## Testing

The project uses `pytest` with `pytest-asyncio`.

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v
```

Tests are located in the `tests/` directory and cover engine initialization, model registry, step parsing, and basic generation.

## Development Conventions

1.  **Async/Await:** The reasoning engine is fully asynchronous. Always use `async for` when consuming the `ReasonChain.generate_with_metadata` generator.
2.  **Structured JSON:** The engine depends on the LLM's ability to output valid JSON. If a model fails to output JSON, the engine attempts to fallback to an XML-like format, but JSON is the primary expectation.
3.  **Type Safety:** Use Pydantic models (like `ModelConfig`) for configuration and dataclasses (like `Step`) for internal data representation.
4.  **Logging & Debugging:** Use the `--debug` flag in the CLI to see detailed execution logs and tracebacks.
5.  **Extensibility:** New models can be registered via the CLI or by updating `model_registry` in Python. The project uses LiteLLM naming conventions for models and providers.
