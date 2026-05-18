 To test LLM-Reasoner from the command line, you have several options depending on whether you want to run the full
  reasoning chain, list models, or run the automated test suite.

  1. Run a Reasoning Query (The Main Feature)
  The primary way to use the CLI is the reason command. This will show you the step-by-step thinking process in your
  terminal.

   1 # Basic usage (uses your default model)
   2 llm-reasoner reason "Explain the difference between a mutex and a semaphore."
   3
   4 # Force a minimum number of reasoning steps
   5 llm-reasoner reason "How would I design a rate-limiter for a distributed system?" --min-steps 5
   6
   7 # Use a specific model and enable debug mode (to see token usage/costs)
   8 llm-reasoner reason "What is the Big O complexity of a Red-Black Tree search?" --model gpt-4 --debug

  2. Manage Models
  Before testing, you might want to see which models are available or add your own.

   1 # List all configured models and see which one is the current default
   2 llm-reasoner models
   3
   4 # Register a custom model (useful for Azure, local LLMs, or newer providers)
   5 llm-reasoner register-model my-local-llama ollama --context-window 8192
   6
   7 # Set a new default model
   8 llm-reasoner set-model gpt-4o

  3. Run the Automated Test Suite
  If you want to verify the codebase's integrity (especially after the recent persistence and parsing updates), use
  pytest.

   1 # Run all tests (Engine, Registry, Persistence, Robust Parsing)
   2 python -m pytest
   3
   4 # Run only the new persistence tests
   5 python -m pytest tests/test_persistence.py
   6
   7 # Run only the robust parsing/repair tests
   8 python -m pytest tests/test_robust_parsing.py

  4. Testing the UI (from CLI)
  You can also launch the web-based dashboard directly from your terminal:

   1 llm-reasoner ui --port 8501

  🚨 Quick Check: API Keys
  Since this is a wrapper, ensure your environment variables are set for the provider you are testing:

   1 # For Windows (PowerShell)
   2 $env:OPENAI_API_KEY="your-key"
   3 $env:ANTHROPIC_API_KEY="your-key"
   4
   5 # For Linux/Mac
   6 export OPENAI_API_KEY="your-key"

  Pro Tip: Use the --debug flag with reason. It provides a detailed Summary Table at the end, showing you the total
  tokens used, the estimated cost of the entire "thinking" process, and the total execution time.
