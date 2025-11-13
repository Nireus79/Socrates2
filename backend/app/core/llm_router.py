"""
LLM Provider Router - Multi-Provider LLM Management

Handles:
- Provider and model discovery
- User model selection
- Cost calculation
- Usage tracking
- API key management
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid


@dataclass
class LLMModel:
    """LLM Model definition"""
    name: str
    provider: str
    description: str
    context_window: int
    max_output_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    capabilities: List[str]  # ['text', 'vision', 'code', etc.]


@dataclass
class LLMUsageRecord:
    """LLM usage tracking record"""
    id: str
    user_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    session_id: Optional[str] = None
    timestamp: Optional[str] = None


class LLMRouter:
    """Routes requests to appropriate LLM provider"""

    # Define available models by provider
    AVAILABLE_MODELS: Dict[str, List[LLMModel]] = {
        "anthropic": [
            LLMModel(
                name="claude-3.5-sonnet",
                provider="anthropic",
                description="Latest Claude model - best balance of speed and capability",
                context_window=200_000,
                max_output_tokens=4_096,
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
                capabilities=["text", "vision", "code", "analysis"]
            ),
            LLMModel(
                name="claude-3-opus",
                provider="anthropic",
                description="Most capable Claude model - best for complex reasoning",
                context_window=200_000,
                max_output_tokens=4_096,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                capabilities=["text", "vision", "code", "analysis", "reasoning"]
            ),
            LLMModel(
                name="claude-3-haiku",
                provider="anthropic",
                description="Fastest Claude model - best for simple tasks",
                context_window=200_000,
                max_output_tokens=4_096,
                cost_per_1k_input=0.00025,
                cost_per_1k_output=0.00125,
                capabilities=["text", "code"]
            ),
        ],
        "openai": [
            LLMModel(
                name="gpt-4-turbo",
                provider="openai",
                description="Most capable GPT-4 variant",
                context_window=128_000,
                max_output_tokens=4_096,
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
                capabilities=["text", "vision", "code"]
            ),
            LLMModel(
                name="gpt-4",
                provider="openai",
                description="Standard GPT-4 model",
                context_window=8_192,
                max_output_tokens=2_048,
                cost_per_1k_input=0.03,
                cost_per_1k_output=0.06,
                capabilities=["text", "code", "reasoning"]
            ),
            LLMModel(
                name="gpt-3.5-turbo",
                provider="openai",
                description="Fast and cost-effective model",
                context_window=4_096,
                max_output_tokens=2_048,
                cost_per_1k_input=0.0005,
                cost_per_1k_output=0.0015,
                capabilities=["text", "code"]
            ),
        ],
        "google": [
            LLMModel(
                name="gemini-1.5-pro",
                provider="google",
                description="Google's most advanced model",
                context_window=1_000_000,
                max_output_tokens=8_192,
                cost_per_1k_input=0.00075,
                cost_per_1k_output=0.003,
                capabilities=["text", "vision", "code", "video"]
            ),
            LLMModel(
                name="gemini-1.5-flash",
                provider="google",
                description="Fast and efficient model",
                context_window=1_000_000,
                max_output_tokens=8_192,
                cost_per_1k_input=0.000075,
                cost_per_1k_output=0.0003,
                capabilities=["text", "vision", "code"]
            ),
        ],
        "open-source": [
            LLMModel(
                name="llama-2-70b",
                provider="open-source",
                description="Meta's Llama 2 large model",
                context_window=4_096,
                max_output_tokens=2_048,
                cost_per_1k_input=0.001,
                cost_per_1k_output=0.001,
                capabilities=["text", "code"]
            ),
            LLMModel(
                name="mistral-7b",
                provider="open-source",
                description="Efficient open-source model",
                context_window=32_000,
                max_output_tokens=2_048,
                cost_per_1k_input=0.00015,
                cost_per_1k_output=0.00015,
                capabilities=["text", "code"]
            ),
        ]
    }

    # User selections storage (in production, this would be in database)
    USER_SELECTIONS: Dict[str, Dict[str, str]] = {}  # user_id -> {provider, model}

    # Usage tracking (in production, this would be in database)
    USAGE_TRACKING: List[LLMUsageRecord] = []

    def __init__(self):
        """Initialize LLM router"""
        self.default_provider = "anthropic"
        self.default_model = "claude-3.5-sonnet"

    def get_available_models(self) -> Dict[str, Any]:
        """Get all available models grouped by provider"""
        result = {}
        for provider, models in self.AVAILABLE_MODELS.items():
            result[provider] = [
                {
                    "name": model.name,
                    "description": model.description,
                    "context_window": model.context_window,
                    "max_output_tokens": model.max_output_tokens,
                    "cost_per_1k_input": model.cost_per_1k_input,
                    "cost_per_1k_output": model.cost_per_1k_output,
                    "capabilities": model.capabilities,
                }
                for model in models
            ]
        return result

    def get_models_for_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Get models for a specific provider"""
        models = self.AVAILABLE_MODELS.get(provider.lower(), [])
        return [
            {
                "name": model.name,
                "description": model.description,
                "context_window": model.context_window,
                "max_output_tokens": model.max_output_tokens,
                "cost_per_1k_input": model.cost_per_1k_input,
                "cost_per_1k_output": model.cost_per_1k_output,
                "capabilities": model.capabilities,
            }
            for model in models
        ]

    def set_user_model(self, user_id: str, provider: str, model: str) -> Dict[str, Any]:
        """
        Set the preferred LLM provider and model for a user

        In production: Save to User model in database
        """
        provider_lower = provider.lower()

        # Verify provider exists
        if provider_lower not in self.AVAILABLE_MODELS:
            return {
                "success": False,
                "error": f"Provider '{provider}' not supported"
            }

        # Verify model exists for provider
        provider_models = self.AVAILABLE_MODELS[provider_lower]
        model_names = [m.name for m in provider_models]

        if model not in model_names:
            return {
                "success": False,
                "error": f"Model '{model}' not available for provider '{provider}'"
            }

        # Save selection (in-memory for now, database in production)
        self.USER_SELECTIONS[user_id] = {
            "provider": provider_lower,
            "model": model,
            "selected_at": datetime.utcnow().isoformat()
        }

        return {
            "success": True,
            "message": f"Selected {provider} {model}",
            "data": {
                "provider": provider_lower,
                "model": model,
                "selected_at": self.USER_SELECTIONS[user_id]["selected_at"]
            }
        }

    def get_user_model(self, user_id: str) -> Dict[str, Any]:
        """Get the user's currently selected LLM"""
        selection = self.USER_SELECTIONS.get(user_id)

        if not selection:
            # Return default
            selection = {
                "provider": self.default_provider,
                "model": self.default_model,
            }

        # Get model details
        provider = selection["provider"]
        model_name = selection["model"]

        models = self.AVAILABLE_MODELS.get(provider, [])
        model = next((m for m in models if m.name == model_name), None)

        if not model:
            return {
                "success": False,
                "error": "Selected model not found"
            }

        return {
            "success": True,
            "data": {
                "provider": provider,
                "model": model_name,
                "description": model.description,
                "context_window": model.context_window,
                "max_output_tokens": model.max_output_tokens,
                "cost_per_1k_input": model.cost_per_1k_input,
                "cost_per_1k_output": model.cost_per_1k_output,
                "capabilities": model.capabilities,
                "selected_at": selection.get("selected_at"),
            }
        }

    def track_usage(
        self,
        user_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track LLM usage for billing and analytics"""
        models = self.AVAILABLE_MODELS.get(provider.lower(), [])
        model_obj = next((m for m in models if m.name == model), None)

        if not model_obj:
            return {
                "success": False,
                "error": f"Model '{model}' not found"
            }

        # Calculate cost
        input_cost = (input_tokens / 1000) * model_obj.cost_per_1k_input
        output_cost = (output_tokens / 1000) * model_obj.cost_per_1k_output
        total_cost = input_cost + output_cost

        # Record usage (in-memory for now, database in production)
        record = LLMUsageRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            provider=provider.lower(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=total_cost,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat()
        )
        self.USAGE_TRACKING.append(record)

        return {
            "success": True,
            "data": {
                "record_id": record.id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost": round(total_cost, 6),
                "timestamp": record.timestamp
            }
        }

    def get_usage_stats(
        self,
        user_id: str,
        period: str = "month"
    ) -> Dict[str, Any]:
        """Get usage statistics for a user"""
        # Filter records for user
        user_records = [r for r in self.USAGE_TRACKING if r.user_id == user_id]

        if not user_records:
            return {
                "success": True,
                "data": {
                    "period": period,
                    "overall": {
                        "total_tokens": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_cost": 0.0,
                        "request_count": 0
                    },
                    "by_model": {},
                    "by_provider": {}
                }
            }

        # Aggregate stats
        total_input = sum(r.input_tokens for r in user_records)
        total_output = sum(r.output_tokens for r in user_records)
        total_cost = sum(r.cost for r in user_records)

        # By model
        by_model = {}
        for record in user_records:
            key = f"{record.provider}/{record.model}"
            if key not in by_model:
                by_model[key] = {
                    "tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                    "calls": 0
                }
            by_model[key]["tokens"] += record.input_tokens + record.output_tokens
            by_model[key]["input_tokens"] += record.input_tokens
            by_model[key]["output_tokens"] += record.output_tokens
            by_model[key]["cost"] += record.cost
            by_model[key]["calls"] += 1

        # By provider
        by_provider = {}
        for record in user_records:
            if record.provider not in by_provider:
                by_provider[record.provider] = {
                    "tokens": 0,
                    "cost": 0.0,
                    "calls": 0
                }
            by_provider[record.provider]["tokens"] += record.input_tokens + record.output_tokens
            by_provider[record.provider]["cost"] += record.cost
            by_provider[record.provider]["calls"] += 1

        return {
            "success": True,
            "data": {
                "period": period,
                "overall": {
                    "total_tokens": total_input + total_output,
                    "input_tokens": total_input,
                    "output_tokens": total_output,
                    "total_cost": round(total_cost, 2),
                    "request_count": len(user_records)
                },
                "by_model": by_model,
                "by_provider": by_provider
            }
        }

    def get_costs(self) -> Dict[str, Any]:
        """Get cost information for all models"""
        providers = {}

        for provider_name, models in self.AVAILABLE_MODELS.items():
            providers[provider_name] = [
                {
                    "name": model.name,
                    "input_cost_per_1k": model.cost_per_1k_input,
                    "output_cost_per_1k": model.cost_per_1k_output,
                    "context_window": model.context_window,
                }
                for model in models
            ]

        return {
            "success": True,
            "data": {
                "providers": providers,
                "comparison": self._calculate_comparison()
            }
        }

    def _calculate_comparison(self) -> Dict[str, float]:
        """Calculate cost comparison for 1M tokens"""
        comparison = {}

        for provider_name, models in self.AVAILABLE_MODELS.items():
            # Use first model as representative
            if models:
                model = models[0]
                cost = (500 * model.cost_per_1k_input + 500 * model.cost_per_1k_output)
                comparison[provider_name] = round(cost, 2)

        return comparison

    def validate_model(self, provider: str, model: str) -> Dict[str, Any]:
        """Validate that a provider/model combination exists"""
        provider_lower = provider.lower()

        if provider_lower not in self.AVAILABLE_MODELS:
            return {
                "valid": False,
                "error": f"Provider '{provider}' not supported"
            }

        models = self.AVAILABLE_MODELS[provider_lower]
        model_obj = next((m for m in models if m.name == model), None)

        if not model_obj:
            return {
                "valid": False,
                "error": f"Model '{model}' not available for provider '{provider}'"
            }

        return {"valid": True}


# Global singleton instance
_llm_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get or create the global LLM router instance"""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
