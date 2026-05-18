
  Generating Architecture Diagram:
  Generating an ASCII architecture diagram to visualize the system components and data flow.


✦ Here is an ASCII representation of the LLM-Reasoner architecture, illustrating the flow from user input to the final
  reasoned response.

    1        USER INTERFACE LAYER
    2       +----------------------+      +-----------------------+
    3       |      CLI (Click)     |      |    Web UI (Streamlit) |
    4       |  (commands.py)       |      |    (interface.py)     |
    5       +----------+-----------+      +-----------+-----------+
    6                  |                              |
    7                  +--------------+---------------+
    8                                 |
    9                                 v
   10       +-----------------------------------------------------+
   11       |                REASONING ENGINE                     |
   12       |               (llm_reasoner/engine.py)              |
   13       |                                                     |
   14       |  +-------------+       +-------------------------+  |
   15       |  | ReasonChain | <---> | Step Parsing & Repair   |  |
   16       |  | (Async Gen) |       | (json-repair / Regex)   |  |
   17       |  +-------------+       +-------------------------+  |
   18       |         ^                       ^                   |
   19       |         |                       |                   |
   20       |         v                       v                   |
   21       |  +-----------------------------------------------+  |
   22       |  |       System Prompt & Chain Configuration     |  |
   23       |  |             (llm_reasoner/settings.py)        |  |
   24       |  +-----------------------------------------------+  |
   25       +-------------------------+---------------------------+
   26                                 |
   27                                 v
   28       +-----------------------------------------------------+
   29       |                MODEL ORCHESTRATOR                   |
   30       |               (llm_reasoner/models.py)              |
   31       |                                                     |
   32       |  +------------------+       +--------------------+  |
   33       |  |  Model Registry  | <---> | Persistence Layer  |  |
   34       |  |  (ModelConfigs)  |       | (~/models.json)    |  |
   35       |  +---------+--------+       +--------------------+  |
   36       |            |                                        |
   37       |            v                                        |
   38       |  +-----------------------------------------------+  |
   39       |  |             LiteLLM Unified Interface          |  |
   40       |  |      (Cost Tracking & Multi-Provider SDK)     |  |
   41       |  +----------------------+------------------------+  |
   42       +-------------------------+---------------------------+
   43                                 |
   44              ___________________|___________________
   45             /                   |                   \
   46            v                    v                    v
   47     +------------+       +------------+       +------------+
   48     |   OpenAI   |       | Anthropic  |       |   Google   |
   49     | (GPT-4o/o1)|       | (Claude 3) |       | (Gemini)   |
   50     +------------+       +------------+       +------------+

  🔑 Key Flow Points:
   1. Request: User enters a query via CLI or Web UI.
   2. Logic: ReasonChain prepares the prompt using the SYSTEM_PROMPT from settings.py.
   3. Dispatch: The Model Orchestrator resolves the model config and sends the request through LiteLLM.
   4. Processing: The engine receives the raw output, sends it through the Repair & Parsing module to ensure structured
      JSON, and extracts cost/usage data.
   5. Iteration: The process loops, feeding previous "steps" back into the model context until the reasoning is
      complete.
   6. Persistence: Any custom model changes or default selections made during the process are saved to the Local JSON
      store.

