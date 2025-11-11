"""
LSP Server Configuration

Configuration for Socrates Language Server Protocol server.
"""

import os
from dataclasses import dataclass


@dataclass
class LSPConfig:
    """LSP Server Configuration"""

    # API Configuration
    api_url: str = os.getenv("SOCRATES_API_URL", "http://localhost:8000")
    api_timeout: int = int(os.getenv("SOCRATES_API_TIMEOUT", "30"))

    # Server Configuration
    listen_host: str = os.getenv("LSP_HOST", "localhost")
    listen_port: int = int(os.getenv("LSP_PORT", "8080"))

    # Logging Configuration
    log_file: str = os.getenv("LSP_LOG_FILE", "/tmp/socrates2-lsp.log")
    log_level: str = os.getenv("LSP_LOG_LEVEL", "INFO")

    # Feature Configuration
    enable_hover: bool = os.getenv("LSP_ENABLE_HOVER", "true").lower() == "true"
    enable_completion: bool = os.getenv("LSP_ENABLE_COMPLETION", "true").lower() == "true"
    enable_diagnostics: bool = os.getenv("LSP_ENABLE_DIAGNOSTICS", "true").lower() == "true"
    enable_code_actions: bool = os.getenv("LSP_ENABLE_CODE_ACTIONS", "true").lower() == "true"
    enable_formatting: bool = os.getenv("LSP_ENABLE_FORMATTING", "true").lower() == "true"

    # Caching Configuration
    cache_ttl: int = int(os.getenv("LSP_CACHE_TTL", "300"))  # 5 minutes
    enable_caching: bool = os.getenv("LSP_ENABLE_CACHING", "true").lower() == "true"

    # Sync Configuration
    text_document_sync_kind: int = int(os.getenv("LSP_SYNC_KIND", "1"))  # 1 = Full, 2 = Incremental

    # Completion Configuration
    max_completion_items: int = int(os.getenv("LSP_MAX_COMPLETIONS", "50"))
    completion_trigger_chars: list = ["."]

    # Code Generation Configuration
    code_gen_timeout: int = int(os.getenv("LSP_CODEGEN_TIMEOUT", "30"))
    supported_languages: list = [
        "python", "javascript", "typescript", "go", "java", "rust", "csharp", "kotlin"
    ]

    def __post_init__(self):
        """Validate configuration"""
        if not self.api_url:
            raise ValueError("API URL must be configured")
        if self.api_timeout < 5:
            raise ValueError("API timeout must be at least 5 seconds")
        if self.listen_port < 1024:
            raise ValueError("Listen port must be >= 1024")
