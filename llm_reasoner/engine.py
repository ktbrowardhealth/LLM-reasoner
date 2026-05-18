"""Core reasoning chain implementation."""

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, List, Optional, Any, Union, cast

try:
    from litellm import acompletion, completion_cost
    from litellm.utils import ModelResponse
except ImportError:
    raise ImportError(
        "litellm is required for ReasonChain. "
        "Install it with `pip install litellm>=1.0.0`"
    )

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

from .settings import (
    SYSTEM_PROMPT, 
    MIN_STEPS, 
    DEFAULT_MAX_TOKENS, 
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT
)
from .models import ModelConfig, model_registry

class ReasoningError(Exception):
    """Error during reasoning chain execution."""
    pass

@dataclass
class Step:
    """A single step in the reasoning chain."""
    number: int
    title: str
    content: str
    confidence: float
    thinking_time: float
    is_final: bool = False
    usage: Optional[Dict[str, int]] = None
    cost: float = 0.0

    @staticmethod
    def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from text that might contain non-JSON content."""
        def try_parse(json_str: str) -> Optional[Dict[str, Any]]:
            try:
                # Try direct JSON parsing first
                return json.loads(json_str)
            except json.JSONDecodeError:
                # If direct fails and repair_json is available, try repairing it
                if repair_json:
                    try:
                        repaired = repair_json(json_str)
                        if repaired:
                            parsed = json.loads(repaired)
                            if isinstance(parsed, dict):
                                return parsed
                    except Exception:
                        pass
            return None

        text = text.strip()
        # 1. Try to parse the whole text
        result = try_parse(text)
        if result:
            return result

        # 2. Look for JSON in markdown code blocks
        json_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        for block in json_blocks:
            result = try_parse(block)
            if result:
                return result

        # 3. Try to find any JSON-like structure (more aggressive)
        # Look for the first '{' and the last '}'
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            result = try_parse(text[start:end+1])
            if result:
                return result

        return None

    @classmethod
    def _parse_xml_like_format(cls, text: str) -> Dict[str, Any]:
        """Parse XML-like format into a dictionary."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return {'title': 'Empty Step', 'content': '', 'confidence': 0.0, 'next_action': 'final_answer'}

        first_line = lines[0]
        # Only treat as title if it looks like a step header or is very short
        title_match = re.match(r'^(?:Step \d+:?\s*)?(.+)$', first_line)
        
        if (title_match and "Step" in first_line) or (len(first_line) < 50 and len(lines) > 1):
            title = title_match.group(1) if title_match else first_line
            content_text = '\n'.join(lines[1:]) if len(lines) > 1 else first_line
        else:
            title = f"Step"
            content_text = text.strip()

        # Extract thinking sections
        thinking_pattern = r'<thinking>(.*?)</thinking>'
        thinking_matches = re.findall(thinking_pattern, content_text, re.DOTALL)
        
        # Clean up content and determine if it's a final answer
        content = re.sub(thinking_pattern, '', content_text, flags=re.DOTALL).strip()
        is_final = bool(re.search(r'(?i)final[_ ]?answer|conclusion', content))

        return {
            'title': title,
            'content': content or content_text, # Fallback to original if sub removed everything
            'confidence': 0.8,
            'next_action': 'final_answer' if is_final else 'continue'
        }

    @classmethod
    def from_response(cls, number: int, response_data: Dict[str, Any], thinking_time: float) -> 'Step':
        """Create a step from an LLM response."""
        try:
            content = cast(str, response_data['choices'][0]['message']['content'])
            usage = response_data.get('usage')
            cost = response_data.get('cost', 0.0)

            # Handle string responses
            parsed_data = cls._extract_json_from_text(content)
            if not parsed_data:
                parsed_data = cls._parse_xml_like_format(content)

            if not parsed_data:
                raise ValueError("Empty or invalid response format")

            # Extract required fields with fallbacks
            title = parsed_data.get('title', '')
            if not title:
                first_line = content.split('\n')[0].strip()
                title_match = re.match(r'^(?:Step \d+:?\s*)?(.+)$', first_line)
                if title_match:
                    title = title_match.group(1)

            # Determine if this is a final answer
            next_action = str(parsed_data.get('next_action', '')).lower()
            is_final = (next_action == 'final_answer' or 
                       bool(re.search(r'(?i)final[_ ]?answer|conclusion', 
                                    parsed_data.get('content', ''))))

            return cls(
                number=number,
                title=title or f"Step {number}",
                content=parsed_data.get('content', content),
                confidence=float(parsed_data.get('confidence', 0.8)),
                thinking_time=thinking_time,
                is_final=is_final,
                usage=dict(usage) if usage else None,
                cost=cost
            )
        except (KeyError, ValueError) as e:
            raise ReasoningError(f"Invalid response format: {str(e)}") from e

@dataclass
class ReasonChain:
    """Main reasoning chain implementation."""
    model_config: ModelConfig = field(default_factory=model_registry.get_default_model)
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    timeout: float = DEFAULT_TIMEOUT
    min_steps: int = MIN_STEPS

    def __init__(
        self,
        model: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        timeout: float = DEFAULT_TIMEOUT,
        min_steps: int = MIN_STEPS
    ) -> None:
        """Initialize the reasoning chain."""
        self.model_config = (
            model_registry.get_model(model)
            if model
            else model_registry.get_default_model()
        )
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.min_steps = min_steps
        self.chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]

    async def generate(self, query: str) -> AsyncIterator[str]:
        """Generate reasoning steps for a query."""
        async for step in self.generate_with_metadata(query):
            yield step.content

    async def _make_completion_request(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Make a completion request with timeout."""
        try:
            response = await asyncio.wait_for(
                acompletion(
                    model=self.model_config.name,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                ),
                timeout=self.timeout
            )

            # Handle LiteLLM's ModelResponse type
            if isinstance(response, ModelResponse):
                if not response.choices or not response.choices[0].message:
                    raise ReasoningError("No valid choices in API response")
                content = response.choices[0].message.content
                if content is None:
                    raise ReasoningError("No content in API response")
                
                # Calculate cost if possible
                try:
                    cost = completion_cost(completion_response=response)
                except Exception:
                    cost = 0.0

                return {
                    'choices': [{'message': {'content': content}}],
                    'usage': getattr(response, 'usage', {}),
                    'cost': cost or 0.0
                }

            raise ReasoningError(f"Unexpected response type: {type(response)}")

        except asyncio.TimeoutError:
            raise ReasoningError(f"Request timed out after {self.timeout} seconds")
        except Exception as e:
            raise ReasoningError(f"API request failed: {str(e)}")

    async def generate_with_metadata(self, query: str) -> AsyncIterator[Step]:
        """Generate reasoning steps with metadata for a query."""
        try:
            self.chat_history.append({"role": "user", "content": query})
            step_number = 1

            while True:
                start_time = time.time()
                response_data = await self._make_completion_request(self.chat_history)

                thinking_time = time.time() - start_time
                step = Step.from_response(step_number, response_data, thinking_time)

                # Add step to chat history for context
                self.chat_history.append({
                    "role": "assistant",
                    "content": f"Step {step_number}: {step.content}"
                })

                yield step

                if step.is_final and step_number >= self.min_steps:
                    break

                step_number += 1

        except Exception as e:
            raise ReasoningError(f"Error during reasoning: {str(e)}") from e

    def clear_history(self) -> None:
        """Clear chat history except for the system prompt."""
        self.chat_history = [self.chat_history[0]]  # Keep system prompt
