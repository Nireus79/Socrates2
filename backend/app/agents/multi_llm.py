"""
MultiLLMManager - Manage multiple LLM providers and route requests.
"""
from typing import Dict, Any, List
from datetime import datetime, timezone

from .base import BaseAgent
from ..models.api_key import APIKey
from ..models.llm_usage_tracking import LLMUsageTracking
from ..core.dependencies import ServiceContainer


class MultiLLMManager(BaseAgent):
    """
    MultiLLMManager - Manage multiple LLM providers.

    Capabilities:
    - list_providers: List available LLM providers
    - add_api_key: Add encrypted API key for provider
    - get_usage_stats: Get LLM usage statistics
    - set_project_llm: Set default LLM for project (placeholder)
    - call_llm: Call specified LLM provider (placeholder)
    """

    def __init__(self, agent_id: str, name: str, services: ServiceContainer):
        """Initialize MultiLLMManager"""
        super().__init__(agent_id, name, services)

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        return [
            'list_providers',
            'add_api_key',
            'get_usage_stats',
            'set_project_llm',
            'call_llm'
        ]

    def _list_providers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List available LLM providers.

        Returns:
            {
                'success': bool,
                'providers': List[dict]
            }
        """
        providers = [
            {
                'id': 'claude',
                'name': 'Anthropic Claude',
                'models': [
                    'claude-3-5-sonnet-20241022',
                    'claude-3-5-haiku-20241022',
                    'claude-3-opus-20240229'
                ],
                'requires_api_key': False,  # System default available
                'cost_per_1k_tokens': {
                    'input': 0.003,
                    'output': 0.015
                },
                'status': 'available'
            },
            {
                'id': 'openai',
                'name': 'OpenAI GPT',
                'models': [
                    'gpt-4o',
                    'gpt-4o-mini',
                    'gpt-4-turbo'
                ],
                'requires_api_key': True,
                'cost_per_1k_tokens': {
                    'input': 0.01,
                    'output': 0.03
                },
                'status': 'requires_user_key'
            },
            {
                'id': 'gemini',
                'name': 'Google Gemini',
                'models': [
                    'gemini-1.5-pro',
                    'gemini-1.5-flash'
                ],
                'requires_api_key': True,
                'cost_per_1k_tokens': {
                    'input': 0.0035,
                    'output': 0.0105
                },
                'status': 'requires_user_key'
            },
            {
                'id': 'ollama',
                'name': 'Local Models (Ollama)',
                'models': [
                    'llama3.2',
                    'mistral',
                    'codellama'
                ],
                'requires_api_key': False,
                'cost_per_1k_tokens': {
                    'input': 0,
                    'output': 0
                },
                'status': 'not_implemented'
            }
        ]

        return {
            'success': True,
            'providers': providers
        }

    def _add_api_key(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add API key for LLM provider.

        Args:
            data: {
                'user_id': UUID,
                'provider': str ('openai', 'claude', 'gemini', 'ollama', 'other'),
                'api_key': str
            }

        Returns:
            {'success': bool, 'api_key_id': UUID}
        """
        user_id = data.get('user_id')
        provider = data.get('provider')
        api_key = data.get('api_key')

        if not all([user_id, provider, api_key]):
            return {
                'success': False,
                'error': 'user_id, provider, and api_key are required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Validate provider
        valid_providers = ['claude', 'openai', 'gemini', 'ollama', 'other']
        if provider not in valid_providers:
            return {
                'success': False,
                'error': f'Invalid provider. Must be one of: {", ".join(valid_providers)}',
                'error_code': 'VALIDATION_ERROR'
            }

        # Get auth database
        db_auth = self.services.get_database_auth()

        # Check if user already has key for this provider
        existing = db_auth.query(APIKey).filter_by(
            user_id=user_id,
            provider=provider
        ).first()

        if existing:
            # Update existing key
            existing.api_key_encrypted = self._encrypt_api_key(api_key)
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc)
            db_auth.commit()

            self.logger.info(f"Updated API key for user {user_id}, provider {provider}")

            return {
                'success': True,
                'api_key_id': str(existing.id),
                'provider': provider,
                'action': 'updated'
            }
        else:
            # Create new key
            api_key_record = APIKey(
                user_id=user_id,
                provider=provider,
                api_key_encrypted=self._encrypt_api_key(api_key),
                is_active=True
            )
            db_auth.add(api_key_record)
            db_auth.commit()

            self.logger.info(f"Added API key for user {user_id}, provider {provider}")

            return {
                'success': True,
                'api_key_id': str(api_key_record.id),
                'provider': provider,
                'action': 'created'
            }

    def _get_usage_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get LLM usage statistics.

        Args:
            data: {
                'user_id': UUID,
                'project_id': UUID (optional)
            }

        Returns:
            {
                'success': bool,
                'total_tokens': int,
                'total_cost': float,
                'usage_by_provider': dict
            }
        """
        user_id = data.get('user_id')
        project_id = data.get('project_id')

        if not user_id:
            return {
                'success': False,
                'error': 'user_id is required',
                'error_code': 'VALIDATION_ERROR'
            }

        # Get specs database
        db_specs = self.services.get_database_specs()

        # Query usage tracking
        query = db_specs.query(LLMUsageTracking).filter_by(user_id=user_id)
        if project_id:
            query = query.filter_by(project_id=project_id)

        usage_records = query.all()

        # Aggregate statistics
        total_tokens = sum(r.tokens_total for r in usage_records)
        total_cost = sum(float(r.cost_usd) if r.cost_usd else 0 for r in usage_records)

        # Group by provider
        usage_by_provider = {}
        for record in usage_records:
            provider = record.provider
            if provider not in usage_by_provider:
                usage_by_provider[provider] = {
                    'tokens_input': 0,
                    'tokens_output': 0,
                    'tokens_total': 0,
                    'cost': 0.0,
                    'calls': 0,
                    'avg_latency_ms': 0
                }

            usage_by_provider[provider]['tokens_input'] += record.tokens_input
            usage_by_provider[provider]['tokens_output'] += record.tokens_output
            usage_by_provider[provider]['tokens_total'] += record.tokens_total
            usage_by_provider[provider]['cost'] += float(record.cost_usd) if record.cost_usd else 0
            usage_by_provider[provider]['calls'] += 1

        # Calculate average latencies
        for provider in usage_by_provider:
            provider_records = [r for r in usage_records if r.provider == provider]
            latencies = [r.latency_ms for r in provider_records if r.latency_ms]
            if latencies:
                usage_by_provider[provider]['avg_latency_ms'] = sum(latencies) / len(latencies)

        return {
            'success': True,
            'total_tokens': total_tokens,
            'total_cost': round(total_cost, 6),
            'total_calls': len(usage_records),
            'usage_by_provider': usage_by_provider
        }

    def _set_project_llm(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set default LLM provider for project (placeholder).

        Args:
            data: {
                'project_id': UUID,
                'provider': str,
                'model': str
            }

        Returns:
            {'success': bool}
        """
        # TODO: Implement project-level LLM configuration
        # This would store preferred provider/model in project settings

        return {
            'success': True,
            'message': 'Project LLM configuration not yet implemented',
            'note': 'LLM provider can be specified per request'
        }

    def _call_llm(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call specified LLM provider (placeholder).

        Args:
            data: {
                'provider': str ('claude' | 'openai' | 'gemini' | 'ollama'),
                'model': str,
                'prompt': str,
                'max_tokens': int,
                'user_id': UUID,
                'project_id': UUID (optional)
            }

        Returns:
            {
                'success': bool,
                'response': str,
                'tokens_used': int,
                'cost': float
            }
        """
        # TODO: Implement actual LLM provider calls
        # This would:
        # 1. Get user's API key for provider (if needed)
        # 2. Call appropriate provider API
        # 3. Track usage in LLMUsageTracking table
        # 4. Return response

        provider = data.get('provider', 'claude')

        return {
            'success': True,
            'message': f'LLM call to {provider} not yet implemented',
            'note': 'Use SocraticCounselorAgent for Claude interactions'
        }

    def _encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt API key before storing.

        Uses simple base64 encoding as placeholder.
        TODO: Implement proper Fernet encryption with SECRET_KEY
        """
        import base64

        # Simple base64 encoding as placeholder
        # In production, use: from cryptography.fernet import Fernet
        encrypted = base64.b64encode(api_key.encode()).decode()

        self.logger.debug("API key encrypted (placeholder encryption)")

        return encrypted

    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt API key.

        Uses simple base64 decoding as placeholder.
        TODO: Implement proper Fernet decryption with SECRET_KEY
        """
        import base64

        # Simple base64 decoding as placeholder
        decrypted = base64.b64decode(encrypted_key.encode()).decode()

        return decrypted
