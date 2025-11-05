# LLM ABSTRACTION LAYER

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🔴 CRITICAL - Must design before Phase 0 implementation

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Why Abstraction is Critical](#why-abstraction-is-critical)
3. [Architecture](#architecture)
4. [LLMProvider Interface](#llmprovider-interface)
5. [Provider Implementations](#provider-implementations)
6. [Provider Selection](#provider-selection)
7. [Configuration Management](#configuration-management)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Testing Strategy](#testing-strategy)
11. [Migration Path](#migration-path)

---

## OVERVIEW

**Problem**: Hardcoding LLM clients creates technical debt that requires massive refactoring later.

**Solution**: Abstract LLM provider interface from day 1, even if only using Claude initially.

### What This Enables

✅ **Phase 3**: Multi-LLM support (Claude, OpenAI, Gemini, Ollama) without refactoring
✅ **Future-proofing**: New LLM providers added without changing existing code
✅ **Testing**: Easy mocking of LLM calls in tests
✅ **Flexibility**: Users choose their preferred LLM
✅ **Cost Optimization**: Switch providers based on price/performance

---

## WHY ABSTRACTION IS CRITICAL

### Without Abstraction (❌ Technical Debt)

```python
# services/socratic_service.py
from anthropic import Anthropic

class SocraticService:
    def __init__(self, db):
        self.db = db
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)  # ❌ Hardcoded

    def ask_question(self, session_id: str, role: str) -> str:
        # ❌ Hardcoded to Claude
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text


# What happens in Phase 3 when we add OpenAI support?
# 🔥 Must refactor EVERY service that uses LLM
# 🔥 Must add if/else branching everywhere
# 🔥 Code becomes unmaintainable mess
```

### With Abstraction (✅ Future-Proof)

```python
# services/socratic_service.py
from llm.llm_service import LLMService

class SocraticService:
    def __init__(self, db, llm_service: LLMService):
        self.db = db
        self.llm = llm_service  # ✅ Abstract interface

    def ask_question(self, session_id: str, role: str) -> str:
        # ✅ Works with ANY provider
        response = self.llm.generate(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.7,
        )
        return response


# What happens in Phase 3 when we add OpenAI support?
# ✅ Implement OpenAIProvider class
# ✅ No changes to existing services
# ✅ User configures provider in .env
# ✅ System switches provider automatically
```

---

## ARCHITECTURE

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Application Layer                                           │
│ (Services, Agents, Controllers)                             │
└────────────────────┬────────────────────────────────────────┘
                     │ Uses
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ LLMService                                                  │
│ - Manages provider selection                                │
│ - Handles errors, retries                                   │
│ - Tracks usage, rate limiting                               │
└────────────────────┬────────────────────────────────────────┘
                     │ Delegates to
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ LLMProvider Interface (Abstract)                            │
│ - generate(prompt, **kwargs) -> str                         │
│ - generate_stream(prompt, **kwargs) -> Iterator[str]        │
│ - get_model_info() -> dict                                  │
│ - health_check() -> bool                                    │
└────────────────────┬────────────────────────────────────────┘
                     │ Implemented by
        ┌────────────┼────────────┬──────────────┐
        ▼            ▼            ▼              ▼
┌──────────────┐ ┌────────────┐ ┌───────────┐ ┌──────────────┐
│ClaudeProvider│ │OpenAIProvid│ │GeminiProv │ │OllamaProvid  │
│              │ │er          │ │ider       │ │er (local)    │
│- Claude API  │ │- OpenAI API│ │- Gemini API│ │- Local models│
└──────────────┘ └────────────┘ └───────────┘ └──────────────┘
```

---

## LLMPROVIDER INTERFACE

### Base Abstract Class

```python
# llm/base_provider.py
from abc import ABC, abstractmethod
from typing import Iterator, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    metadata: Dict[str, Any]

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM providers must implement this interface to ensure
    compatibility with Socrates2.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text completion.

        Args:
            prompt: User prompt
            system_prompt: System instructions (optional)
            max_tokens: Maximum tokens to generate
            temperature: Randomness (0.0 = deterministic, 1.0 = creative)
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse object

        Raises:
            LLMProviderError: If generation fails
        """
        pass

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> Iterator[str]:
        """
        Generate text completion with streaming.

        Args:
            Same as generate()

        Yields:
            str: Text chunks as they're generated

        Raises:
            LLMProviderError: If generation fails
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.

        Returns:
            dict with keys:
            - provider: Provider name (e.g., "claude", "openai")
            - model: Model name (e.g., "claude-3-5-sonnet-20241022")
            - max_tokens: Maximum context length
            - supports_streaming: Whether streaming is supported
            - cost_per_1k_tokens: Cost information
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if provider is healthy and API key is valid.

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text (provider-specific tokenizer).

        Args:
            text: Text to count tokens for

        Returns:
            Token count
        """
        pass
```

---

## PROVIDER IMPLEMENTATIONS

### Claude Provider (Phase 0)

```python
# llm/providers/claude_provider.py
from anthropic import Anthropic
from llm.base_provider import LLMProvider, LLMResponse
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider implementation."""

    def __init__(self, api_key: str = None):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key (defaults to settings)
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens_limit = 200000

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate text using Claude."""
        try:
            messages = [{"role": "user", "content": prompt}]

            # Build request
            request_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }

            if system_prompt:
                request_params["system"] = system_prompt

            # Add any provider-specific kwargs
            request_params.update(kwargs)

            # Call Claude API
            response = self.client.messages.create(**request_params)

            # Parse response
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=tokens_used,
                finish_reason=response.stop_reason,
                metadata={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            )

        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            raise LLMProviderError(f"Claude generation failed: {str(e)}")

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> Iterator[str]:
        """Generate text with streaming."""
        try:
            messages = [{"role": "user", "content": prompt}]

            request_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
                "stream": True,
            }

            if system_prompt:
                request_params["system"] = system_prompt

            with self.client.messages.stream(**request_params) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Claude streaming error: {str(e)}")
            raise LLMProviderError(f"Claude streaming failed: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get Claude model information."""
        return {
            "provider": "claude",
            "model": self.model,
            "max_tokens": self.max_tokens_limit,
            "supports_streaming": True,
            "cost_per_1k_input_tokens": 0.003,  # $3 per million
            "cost_per_1k_output_tokens": 0.015,  # $15 per million
        }

    def health_check(self) -> bool:
        """Check Claude API health."""
        try:
            # Make minimal API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return response is not None
        except Exception as e:
            logger.error(f"Claude health check failed: {str(e)}")
            return False

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using Claude's tokenizer.
        Note: Anthropic doesn't provide public tokenizer, use approximation.
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
```

### OpenAI Provider (Phase 3)

```python
# llm/providers/openai_provider.py
from openai import OpenAI
from llm.base_provider import LLMProvider, LLMResponse
from config.settings import settings
import tiktoken
import logging

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider implementation."""

    def __init__(self, api_key: str = None):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to settings)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4-turbo-preview"
        self.max_tokens_limit = 128000
        self.tokenizer = tiktoken.encoding_for_model(self.model)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate text using OpenAI."""
        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            # Parse response
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=tokens_used,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                },
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMProviderError(f"OpenAI generation failed: {str(e)}")

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> Iterator[str]:
        """Generate text with streaming."""
        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            # Call OpenAI streaming API
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                **kwargs
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            raise LLMProviderError(f"OpenAI streaming failed: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information."""
        return {
            "provider": "openai",
            "model": self.model,
            "max_tokens": self.max_tokens_limit,
            "supports_streaming": True,
            "cost_per_1k_input_tokens": 0.01,  # GPT-4 Turbo
            "cost_per_1k_output_tokens": 0.03,
        }

    def health_check(self) -> bool:
        """Check OpenAI API health."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return response is not None
        except Exception as e:
            logger.error(f"OpenAI health check failed: {str(e)}")
            return False

    def count_tokens(self, text: str) -> int:
        """Count tokens using OpenAI's tokenizer."""
        return len(self.tokenizer.encode(text))
```

---

## PROVIDER SELECTION

### LLMService (Facade)

```python
# llm/llm_service.py
from llm.base_provider import LLMProvider, LLMResponse
from llm.providers.claude_provider import ClaudeProvider
from llm.providers.openai_provider import OpenAIProvider
from llm.providers.gemini_provider import GeminiProvider
from llm.providers.ollama_provider import OllamaProvider
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """
    LLM service facade.

    Manages provider selection, error handling, rate limiting.
    """

    def __init__(self, provider: str = None):
        """
        Initialize LLM service.

        Args:
            provider: Provider name ("claude", "openai", "gemini", "ollama")
                     If None, uses settings.DEFAULT_LLM_PROVIDER
        """
        self.provider_name = provider or settings.DEFAULT_LLM_PROVIDER
        self.provider = self._create_provider(self.provider_name)

    def _create_provider(self, provider_name: str) -> LLMProvider:
        """
        Create provider instance.

        Args:
            provider_name: Provider name

        Returns:
            LLMProvider instance

        Raises:
            ValueError: If provider not supported
        """
        providers = {
            "claude": ClaudeProvider,
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
            "ollama": OllamaProvider,
        }

        provider_class = providers.get(provider_name.lower())

        if not provider_class:
            raise ValueError(
                f"Unsupported LLM provider: {provider_name}. "
                f"Supported: {list(providers.keys())}"
            )

        logger.info(f"Initializing LLM provider: {provider_name}")
        return provider_class()

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text completion.

        Args:
            Same as LLMProvider.generate()

        Returns:
            LLMResponse

        Raises:
            LLMProviderError: If generation fails
        """
        try:
            return self.provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> Iterator[str]:
        """Generate text with streaming."""
        try:
            yield from self.provider.generate_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
        except Exception as e:
            logger.error(f"LLM streaming failed: {str(e)}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get current provider model info."""
        return self.provider.get_model_info()

    def health_check(self) -> bool:
        """Check provider health."""
        return self.provider.health_check()

    def count_tokens(self, text: str) -> int:
        """Count tokens using provider's tokenizer."""
        return self.provider.count_tokens(text)

    def switch_provider(self, provider_name: str):
        """
        Switch to different LLM provider.

        Args:
            provider_name: New provider name

        Raises:
            ValueError: If provider not supported
        """
        logger.info(f"Switching LLM provider from {self.provider_name} to {provider_name}")
        self.provider_name = provider_name
        self.provider = self._create_provider(provider_name)
```

---

## CONFIGURATION MANAGEMENT

### Settings

```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Default LLM provider
    DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "claude")

    # Claude (Anthropic) configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", 200000))

    # OpenAI configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", 128000))

    # Gemini configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

    # Ollama configuration (local)
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

    def validate(self):
        """Validate LLM configuration."""
        provider = self.DEFAULT_LLM_PROVIDER

        if provider == "claude" and not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude provider")

        if provider == "openai" and not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")

        if provider == "gemini" and not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")

settings = Settings()
```

### .env Example

```bash
# .env

# LLM Configuration
DEFAULT_LLM_PROVIDER=claude  # claude, openai, gemini, ollama

# Claude (Anthropic)
ANTHROPIC_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=200000

# OpenAI (Phase 3+)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=128000

# Gemini (Phase 3+)
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-pro

# Ollama (local, Phase 3+)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
```

---

## ERROR HANDLING

### Custom Exceptions

```python
# llm/exceptions.py

class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass

class LLMRateLimitError(LLMProviderError):
    """Rate limit exceeded."""
    pass

class LLMAuthenticationError(LLMProviderError):
    """API key invalid or expired."""
    pass

class LLMTimeoutError(LLMProviderError):
    """Request timed out."""
    pass

class LLMInvalidRequestError(LLMProviderError):
    """Invalid request parameters."""
    pass
```

### Retry Logic

```python
# llm/llm_service.py
import time
from tenacity import retry, stop_after_attempt, wait_exponential

class LLMService:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def generate_with_retry(
        self,
        prompt: str,
        **kwargs
    ) -> LLMResponse:
        """
        Generate with automatic retry on transient errors.

        Retries up to 3 times with exponential backoff:
        - Attempt 1: Immediate
        - Attempt 2: Wait 2 seconds
        - Attempt 3: Wait 4 seconds
        """
        return self.generate(prompt, **kwargs)
```

---

## RATE LIMITING

```python
# llm/rate_limiter.py
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter for LLM API calls.

    Prevents exceeding provider rate limits.
    """

    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            "claude": {"requests_per_minute": 50, "tokens_per_minute": 100000},
            "openai": {"requests_per_minute": 60, "tokens_per_minute": 90000},
            "gemini": {"requests_per_minute": 60, "tokens_per_minute": 80000},
            "ollama": {"requests_per_minute": 1000, "tokens_per_minute": 1000000},  # Local
        }

    def can_make_request(self, provider: str, tokens: int = 1000) -> bool:
        """
        Check if request is allowed.

        Args:
            provider: Provider name
            tokens: Estimated tokens for request

        Returns:
            True if allowed, False if rate limit exceeded
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Remove old requests
        self.requests[provider] = [
            (req_time, req_tokens)
            for req_time, req_tokens in self.requests[provider]
            if req_time > cutoff
        ]

        # Check request limit
        limit = self.limits.get(provider, self.limits["claude"])
        request_count = len(self.requests[provider])
        token_count = sum(tokens for _, tokens in self.requests[provider])

        if request_count >= limit["requests_per_minute"]:
            logger.warning(f"Rate limit exceeded for {provider}: too many requests")
            return False

        if token_count + tokens > limit["tokens_per_minute"]:
            logger.warning(f"Rate limit exceeded for {provider}: too many tokens")
            return False

        # Record request
        self.requests[provider].append((now, tokens))
        return True
```

---

## TESTING STRATEGY

### Mock LLM Provider

```python
# tests/mocks/mock_llm_provider.py
from llm.base_provider import LLMProvider, LLMResponse
from typing import Iterator, Dict, Any

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, responses: list = None):
        """
        Initialize mock provider.

        Args:
            responses: List of predefined responses (cycles through)
        """
        self.responses = responses or ["Mocked response"]
        self.call_count = 0

    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Return mocked response."""
        response_text = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1

        return LLMResponse(
            content=response_text,
            model="mock-model",
            tokens_used=len(response_text.split()),
            finish_reason="stop",
            metadata={"prompt": prompt},
        )

    def generate_stream(self, *args, **kwargs) -> Iterator[str]:
        """Return mocked streaming response."""
        response = self.generate(*args, **kwargs)
        for word in response.content.split():
            yield word + " "

    def get_model_info(self) -> Dict[str, Any]:
        """Return mock model info."""
        return {
            "provider": "mock",
            "model": "mock-model",
            "max_tokens": 100000,
            "supports_streaming": True,
            "cost_per_1k_tokens": 0.0,
        }

    def health_check(self) -> bool:
        """Always healthy."""
        return True

    def count_tokens(self, text: str) -> int:
        """Count words as tokens."""
        return len(text.split())
```

### Using Mock in Tests

```python
# tests/test_socratic_service.py
import pytest
from tests.mocks.mock_llm_provider import MockLLMProvider
from llm.llm_service import LLMService
from services.socratic_service import SocraticService

def test_socratic_question_generation(db_session):
    """Test Socratic service generates questions."""
    # Create mock LLM
    mock_provider = MockLLMProvider(
        responses=["What problem does your app solve?"]
    )

    # Create LLM service with mock
    llm_service = LLMService.__new__(LLMService)
    llm_service.provider = mock_provider

    # Create Socratic service
    socratic_service = SocraticService(db_session, llm_service)

    # Generate question
    question = socratic_service.ask_question(
        session_id="test-session",
        role="product_manager",
    )

    # Verify
    assert question == "What problem does your app solve?"
    assert mock_provider.call_count == 1
```

---

## MIGRATION PATH

### Phase 0: Abstraction Layer (Without Hardcoding)

```python
# ✅ Day 1: Use abstraction from the start
from llm.llm_service import LLMService

class SocraticService:
    def __init__(self, db, llm_service: LLMService = None):
        self.db = db
        self.llm = llm_service or LLMService()  # Defaults to Claude

    def ask_question(self, session_id: str, role: str) -> str:
        response = self.llm.generate(prompt=prompt)
        return response.content
```

### Phase 3: Add New Provider (Zero Refactoring)

```python
# ✅ Add Ollama provider (no changes to existing services)

# 1. Implement OllamaProvider
# llm/providers/ollama_provider.py
class OllamaProvider(LLMProvider):
    # ... implementation

# 2. Register in LLMService
# llm/llm_service.py
providers = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,  # ← New provider
}

# 3. User configures in .env
DEFAULT_LLM_PROVIDER=ollama

# 4. Done! All services now use Ollama
```

---

## VERIFICATION CHECKLIST

Before Phase 0 implementation:

- [ ] LLMProvider abstract class defined
- [ ] ClaudeProvider implemented (Phase 0)
- [ ] LLMService facade created
- [ ] Provider selection mechanism works
- [ ] Configuration loaded from .env
- [ ] Error handling implemented
- [ ] Rate limiting implemented
- [ ] MockLLMProvider for testing created
- [ ] All services use LLMService (not hardcoded)
- [ ] Tests pass with mock provider

---

**Document Status:** ✅ Complete
**Reviewed By:** Pending
**Approved By:** Pending
**Date:** November 5, 2025

---

*This abstraction layer ensures Phase 3 multi-LLM support requires NO refactoring.*
