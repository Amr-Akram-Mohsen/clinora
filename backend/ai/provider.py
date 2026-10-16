"""
ai/provider.py

AI provider abstraction for Clinora.

Responsibilities:
- Define the internal AIProvider interface that all vendor implementations
  must satisfy.
- Ensure the application and domain layers depend on this abstraction rather
  than any vendor SDK (Anthropic, OpenAI, Gemini, etc.).
- Define structured input/output types so the application layer has a typed
  contract regardless of which provider is active.

Phase 1 status: Interface only. No concrete implementation.
Phase 4 will add AnthropicProvider as the first concrete adapter.

Architecture rules:
- Concrete adapters live in infrastructure/ai/ (not here).
- The application layer uses AIProvider, never AnthropicClient or similar.
- AI outputs must be validated before presentation (never trust raw model JSON).
- The provider does not decide what data it receives — the application controls
  context construction before calling the provider.

Medical safety boundary:
- AI outputs are advisory only. They must be clearly labeled as AI-generated.
- No AI output should be written to clinical records without explicit physician
  confirmation (Phase 4 workflow requirement).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIMessage:
    """A single message in a conversation context."""

    role: str      # "system" | "user" | "assistant"
    content: str


@dataclass
class AIRequest:
    """
    A request to the AI provider.
    The application constructs this from pre-authorized, pre-filtered data.
    """

    messages: list[AIMessage]
    # Optional structured output schema (JSON schema dict).
    # When provided, the provider should attempt to return conforming JSON.
    response_schema: dict[str, Any] | None = None
    max_tokens: int = 2048
    temperature: float = 0.2   # Low temperature for clinical precision


@dataclass
class AIResponse:
    """
    Validated response from the AI provider.
    The provider adapter is responsible for basic structural validation.
    Application code performs clinical safety validation before use.
    """

    content: str
    # Parsed structured output, if response_schema was provided and parsing succeeded
    structured: dict[str, Any] | None = None
    # Token usage for audit/cost tracking
    input_tokens: int = 0
    output_tokens: int = 0
    # Provider-specific metadata (model version, latency, etc.) — for audit only
    provider_metadata: dict[str, Any] = field(default_factory=dict)



class AIProvider(ABC):
    """
    Abstract AI provider interface.

    All AI operations in Clinora go through this interface.
    Vendor-specific logic is fully encapsulated in infrastructure/ai/ adapters.
    """

    @abstractmethod
    async def complete(self, request: AIRequest) -> AIResponse:
        """
        Send a completion request and return a validated response.

        Raises:
            core.errors.ExternalServiceError: If the provider is unavailable.
            core.errors.ValidationError: If the response does not conform to
                the requested schema.
        """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name (e.g., 'anthropic-claude-3-5-sonnet')."""
