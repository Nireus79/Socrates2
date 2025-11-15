# Socrates CLI - Interactive Specification Generator

A Claude Code-style CLI interface for interactive specification gathering and AI-powered project development.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/Socrates.git
cd Socrates

# Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# OR
.venv\Scripts\activate             # Windows

# Install dependencies
pip install -r requirements.txt

# Run Socrates
python socrates.py
```

## Features

- **Natural Language Intent Parsing** - Convert natural language to CLI commands
- **Dual Chat Modes**:
  - Socratic Mode: Pure Q&A for specification gathering
  - Direct Mode: Chat + Commands for development
- **Code Generation** - AI-powered code generation from specifications
- **Document Management** - Upload and search project documents
- **GitHub Integration** - Import repositories and analyze code
- **LLM Selection** - Choose from multiple AI models

## Documentation

- **[Quick Start](docs/user/QUICKSTART.md)** - 5-minute setup guide
- **[User Guide](docs/user/USER_GUIDE_v2.md)** - Comprehensive command reference
- **[Architecture](docs/technical/ARCHITECTURE.md)** - System design and components
- **[Deployment](docs/deployment/DEPLOYMENT_PREP.md)** - Release procedures
- **[Contributing](docs/project/CONTRIBUTING.md)** - How to contribute
- **[Security](docs/project/SECURITY.md)** - Security considerations

## Project Structure

```
Socrates/
├── src/                          # Source code
│   ├── Socrates.py              # Main CLI application
│   ├── intent_parser.py         # Natural language parsing
│   ├── api_client_extension.py  # API client
│   ├── cli_logger.py            # Logging utilities
│   └── socrates_cli_lib.py      # Library functions
│
├── tests/                        # Test suite
│   └── test_edge_cases.py       # Edge case tests
│
├── docs/                         # Documentation
│   ├── user/                    # End-user guides
│   ├── technical/               # Technical documentation
│   ├── deployment/              # Deployment guides
│   └── project/                 # Project documentation
│
├── backend/                      # Backend-related files
├── cli/                          # CLI framework (legacy)
├── library/                      # Library documentation
└── _archive/                     # Archived documents
```

## System Requirements

- Python 3.12 or higher
- PostgreSQL 17+ (for backend)
- Virtual environment

## Installation

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code quality checks
black src/
flake8 src/
mypy src/
```

### Production Deployment

See [Deployment Guide](docs/deployment/DEPLOYMENT_PREP.md) for complete deployment instructions.

## Key Commands

### Chat Modes
```
/mode socratic    # Q&A mode
/mode direct      # Chat + Commands mode
```

### Project Management
```
/project create NAME    # Create project
/projects              # List projects
/project select NAME   # Select project
```

### Code Generation
```
/code generate         # Generate code
/code status          # Check status
/code download        # Download code
```

### Documentation
```
/doc upload FILE      # Upload document
/doc list            # List documents
/doc search QUERY    # Search documents
```

## Architecture Highlights

- **Modular Design**: Separate modules for intent parsing, API communication, and logging
- **Two-Level Intent Parsing**: Pattern matching + Claude fallback
- **Mode-Aware Chat**: Socratic and Direct modes for different workflows
- **Extensible Command Framework**: 51+ command handlers
- **Rich Terminal UI**: Tables, panels, syntax highlighting

## Status

- **Version**: 1.0.0
- **Status**: Production Ready
- **Last Updated**: 2025-11-15
- **Deployment Readiness**: 75%

## Development Notes

### Code Organization
- Main entry point: `src/Socrates.py` (4520 lines)
- Intent parser: `src/intent_parser.py` (346 lines)
- Supporting modules: API client, logger, library

### Testing
- Edge case pattern tests: 3/3 passing (100%)
- Integration tests: In progress
- E2E tests: Planned for v1.1

### Performance
- Target: < 2s for all operations
- Optimization opportunities: Caching (30-50% improvement), Connection pooling (100-200ms improvement)

## Contributing

1. Read [Contributing Guide](docs/project/CONTRIBUTING.md)
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit with conventional messages
4. Submit pull request to `develop` branch

## Security

See [Security Policy](docs/project/SECURITY.md) for vulnerability reporting and security best practices.

## License

[Add your license here]

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/Socrates/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/Socrates/discussions)
- **Email**: support@socrates.dev

## Changelog

See [CHANGELOG](docs/project/CHANGELOG.md) for version history and release notes.

---

**Built with ❤️ using Claude AI**

For detailed documentation, visit the [docs](docs/) directory.
