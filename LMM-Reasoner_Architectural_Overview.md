
  Codebase Architectural Overview: Providing a comprehensive architectural overview of the LLM-Reasoner codebase.

  ✓  ReadFile  GEMINI.md

✦ The LLM-Reasoner codebase is a highly modular Python framework designed to enforce systematic, step-by-step reasoning
  on top of standard Large Language Models.

  🏗️ High-Level Architecture

  The project follows a decoupled architecture where the core logic is separated from the user interfaces and model
  management.

  1. Core Reasoning Engine (llm_reasoner/engine.py)
  This is the "brain" of the project.
   - ReasonChain: An asynchronous generator that manages the conversation loop. It maintains the chat history and
     iteratively prompts the model until a "final answer" is reached or the minimum step count is met.
   - Step Dataclass: Captures every individual thought process, including the title, content, confidence score, thinking
     time, token usage, and cost.
   - Robust Parsing: Uses json-repair to handle malformed LLM outputs and features a multi-stage extraction strategy
     (Whole Text -> Markdown Blocks -> Aggressive Brackets -> XML Fallback).

  2. Model Orchestration (llm_reasoner/models.py)
  Provides a unified interface for interacting with dozens of LLM providers.
   - LiteLLM Integration: Abstracts away provider-specific APIs (OpenAI, Anthropic, Gemini, etc.), allowing the same
     reasoning logic to work across different models.
   - Persistence: Custom model registrations and default settings are saved to ~/.llm_reasoner/models.json, ensuring
     configurations survive across different terminal sessions.
   - Validation: Uses Pydantic (ModelConfig) to ensure model parameters like context windows are correctly formatted.

  3. Global Configuration (llm_reasoner/settings.py)
  Centralizes the "rules of engagement" for the AI.
   - System Prompt: A carefully crafted set of instructions that forces the LLM to use Chain-of-Thought (CoT) and output
     its reasoning in a structured JSON format.
   - Hyperparameters: Defines default max tokens, temperature, and the mandatory minimum reasoning steps.

  4. Multi-Interface Layer
  The logic is exposed through two primary channels:
   - CLI (llm_reasoner/commands.py): A power-user interface built with Click and Rich. It provides real-time progress
     bars, formatted panels for reasoning steps, and a final cost/token summary table.
   - Web UI (llm_reasoner/interface.py): A Streamlit-based dashboard that offers a more visual experience, including
     sliders for temperature/steps and interactive metrics for monitoring the reasoning process.

  🔄 Data Flow
   1. Input: User provides a query via CLI or UI.
   2. Setup: ReasonChain is initialized with selected model and parameters.
   3. Execution Loop:
      - acompletion is called via LiteLLM.
      - Response is sanitized and repaired by the engine.
      - Metadata (tokens, cost, time) is extracted.
      - A Step object is yielded to the interface.
      - Step content is added back to chat history for context.
   4. Finalization: Loop terminates when is_final is true and min_steps are met. A summary report is generated.

  🛠️ Key Technical Strengths
   - Resilience: Can recover from incomplete or malformed JSON responses.
   - Observability: Real-time tracking of thinking time, confidence, and financial cost.
   - Flexibility: Users can register and use any LiteLLM-supported model without modifying the source code.

