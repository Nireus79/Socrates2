"""
Sentry error tracking initialization and configuration.

This module handles:
- Sentry SDK initialization
- Sensitive data scrubbing
- Performance monitoring
- Release tagging
"""
import logging
import re
from typing import Any, Dict, Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# Try to import SqlAlchemyIntegration, but it may not be available in all versions
try:
    from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration
    HAS_SQLALCHEMY_INTEGRATION = True
except ImportError:
    HAS_SQLALCHEMY_INTEGRATION = False

from ..core.config import settings

logger = logging.getLogger(__name__)


def scrub_string(s: str) -> str:
    """
    Scrub sensitive patterns from string.

    Removes:
    - Passwords: password="xxx" or password:xxx
    - API keys: api_key="xxx" or api_key:xxx
    - Tokens: token="xxx" or token:xxx
    - Bearer tokens in Authorization headers

    Args:
        s: String to scrub

    Returns:
        Scrubbed string with sensitive values replaced with "***"
    """
    if not isinstance(s, str):
        return s

    # Remove passwords: password="xxx" or password:xxx or password='xxx'
    s = re.sub(
        r'password["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
        'password="***"',
        s,
        flags=re.IGNORECASE
    )

    # Remove API keys: api_key="xxx" or api_key:xxx
    s = re.sub(
        r'api_key["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
        'api_key="***"',
        s,
        flags=re.IGNORECASE
    )

    # Remove tokens: token="xxx" or token:xxx
    s = re.sub(
        r'(token|secret)["\']?\s*[:=]\s*["\']?[^"\'\s,}]+',
        r'\1="***"',
        s,
        flags=re.IGNORECASE
    )

    # Remove bearer tokens
    s = re.sub(
        r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',
        'Bearer ***',
        s,
        flags=re.IGNORECASE
    )

    # Remove database passwords (postgresql://user:password@host)
    s = re.sub(
        r'://([^:]+):([^@]+)@',
        r'://\1:***@',
        s
    )

    return s


def scrub_sensitive_data(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Sentry before_send hook to remove sensitive data from error events.

    This function is called for every event before it's sent to Sentry.
    It scrubs:
    - Exception messages
    - Request headers (Authorization, API keys)
    - Request body
    - Stack trace values

    Args:
        event: Sentry event dictionary
        hint: Additional hint data including exception details

    Returns:
        Scrubbed event or None to drop the event
    """
    # Scrub exception values
    if 'exception' in event:
        for exc in event['exception'].get('values', []):
            if 'value' in exc:
                exc['value'] = scrub_string(exc['value'])
            if 'module' in exc:
                exc['module'] = scrub_string(exc['module'])

            # Scrub stack trace
            if 'stacktrace' in exc:
                for frame in exc['stacktrace'].get('frames', []):
                    if 'function' in frame:
                        frame['function'] = scrub_string(frame['function'])
                    if 'vars' in frame and isinstance(frame['vars'], dict):
                        for key, value in frame['vars'].items():
                            if isinstance(value, str):
                                frame['vars'][key] = scrub_string(value)

    # Scrub request headers
    if 'request' in event:
        if 'headers' in event['request'] and isinstance(event['request']['headers'], dict):
            # Remove sensitive headers
            sensitive_headers = [
                'Authorization',
                'X-API-Key',
                'X-Auth-Token',
                'X-Access-Token',
                'Cookie',
                'Set-Cookie'
            ]
            for header in sensitive_headers:
                if header in event['request']['headers']:
                    event['request']['headers'][header] = '***'

        # Scrub request body
        if 'data' in event['request'] and isinstance(event['request']['data'], str):
            event['request']['data'] = scrub_string(event['request']['data'])

        if 'url' in event['request']:
            event['request']['url'] = scrub_string(event['request']['url'])

    # Scrub message
    if 'message' in event and isinstance(event['message'], str):
        event['message'] = scrub_string(event['message'])

    # Scrub contexts
    if 'contexts' in event:
        for context_name, context_data in event['contexts'].items():
            if isinstance(context_data, dict):
                for key, value in context_data.items():
                    if isinstance(value, str):
                        context_data[key] = scrub_string(value)

    return event


def init_sentry() -> None:
    """
    Initialize Sentry error tracking.

    This should be called early in application startup, before creating
    the FastAPI app instance.

    Sentry configuration includes:
    - Error tracking and aggregation
    - Performance monitoring
    - Release tagging
    - Data scrubbing for security

    Does nothing if SENTRY_DSN is not configured.
    """
    if not settings.SENTRY_DSN:
        logger.debug("Sentry DSN not configured, error tracking disabled")
        return

    try:
        # Build integrations list
        integrations = [
            FastApiIntegration(),
            LoggingIntegration(
                level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
                event_level=logging.ERROR
            ),
        ]

        # Add SqlAlchemy integration if available
        if HAS_SQLALCHEMY_INTEGRATION:
            integrations.append(SqlAlchemyIntegration())

        sentry_sdk.init(
            # Core configuration
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            release=settings.APP_VERSION,

            # Integrations
            integrations=integrations,

            # Performance monitoring
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,

            # Data scrubbing
            before_send=scrub_sensitive_data,

            # Options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send PII by default
            include_source_context=True,
        )

        logger.info(f"Sentry initialized: {settings.ENVIRONMENT} ({settings.APP_VERSION})")
        logger.debug(f"Traces sample rate: {settings.SENTRY_TRACES_SAMPLE_RATE * 100}%")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}", exc_info=True)
        # Don't fail app startup if Sentry initialization fails
