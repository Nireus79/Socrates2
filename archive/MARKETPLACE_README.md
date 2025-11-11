# Socrates IDE Plugins - Marketplace Documentation

## Overview

Socrates is an intelligent IDE integration platform that brings specification-aware development to your favorite IDEs. It provides real-time conflict detection, code generation, and specification management across VS Code, JetBrains IDEs, and via Language Server Protocol.

## Supported IDEs

### VS Code Extension
- **Platform:** Visual Studio Code 1.60+
- **Features:** Project browser, specification viewer, conflict detection, code generation
- **Status:** Fully supported

### JetBrains Plugins
- **IntelliJ IDEA:** Full IDE support for Java/Kotlin development
- **PyCharm:** Python-specific patterns and tools
- **WebStorm:** JavaScript/TypeScript and modern web framework support
- **Other JetBrains IDEs:** Compatible through base IntelliJ plugin

### Language Server Protocol (LSP)
- **Support:** All LSP-compatible editors
- **Features:** Hover documentation, code completion, diagnostics, formatting
- **Setup:** Manual configuration of LSP server endpoint

## Key Features

### Specification Management
- Create and organize specifications by category
- Version control for specifications
- Maturity scoring and tracking
- Bulk import/export capabilities
- Search and filter specifications

### Code Generation
Supported languages:
- **Python** (3.8+) - Classes, dataclasses, async patterns
- **JavaScript** (ES6+) - Classes, arrow functions, async/await
- **TypeScript** - Strict mode, generics, decorators
- **Go** - Structs, concurrent patterns, error handling
- **Java** - Classes, builder pattern, annotations
- **Rust** - Structs, async/await, serde support
- **C#** - Classes with LINQ, JSON serialization
- **Kotlin** - Data classes, coroutines, DSL builders

### IDE Features

#### Hover Documentation
- Display specification details on hover
- Show category, value, and metadata
- Markdown-formatted documentation

#### Code Completion
- Specification-aware completions
- Search-based filtering
- Display specification details in completion items

#### Diagnostics
- Real-time conflict detection
- Severity-based highlighting
- Quick navigation to conflict details

#### Code Actions
- Quick fixes for conflicts
- Generate code from specifications
- View conflict details and resolution options

#### Go to Definition
- Navigate to specification definition
- Track specification references

#### Code Formatting
- Language-specific formatting
- Black (Python), Prettier (JavaScript), gofmt (Go) style
- IntelliJ standard formatting

### Project Management
- Create and manage projects
- Track project maturity scores
- Monitor specification coverage
- View activity timeline
- Batch operations support

### Conflict Detection
- Automatic conflict identification
- Severity classification (low, medium, high, critical)
- Resolution recommendations
- Historical tracking

## Installation

### VS Code
1. Open Extensions in VS Code
2. Search for "Socrates"
3. Click Install
4. Reload VS Code
5. Configure API endpoint in settings

### IntelliJ IDEA / PyCharm / WebStorm
1. Open IDE settings
2. Go to Plugins → Marketplace
3. Search "Socrates"
4. Click Install and Restart IDE
5. Configure API endpoint in settings

### Language Server Protocol
1. Install LSP server: `pip install socrates-lsp`
2. Configure in your editor
3. Restart editor to connect

## Configuration

### API Endpoint
Set your Socrates backend API endpoint:
- VS Code: Settings → Socrates → API URL
- JetBrains: Settings → Tools → Socrates → API URL

### Authentication
1. Register/login to Socrates backend
2. Generate API token
3. Configure token in IDE settings
4. Token is securely stored

### Project Selection
1. Open Socrates panel in IDE
2. Select project from list
3. Specifications auto-load for selected project

## Usage Examples

### VS Code
```
1. Open Socrates panel (Ctrl+Shift+S)
2. Select project
3. Browse specifications
4. Hover over spec reference for details
5. Right-click to generate code
```

### IntelliJ IDEA / PyCharm
```
1. Open Socrates tool window
2. Select project from dropdown
3. View specifications by category
4. Click "Generate Code" to create implementation
5. Use inspection markers for conflicts
```

### Language Server
```
Features available in any LSP-compatible editor:
- Hover: Shows specification details
- Completion: Type @ or . to see spec completions
- Diagnostics: Red squiggles for conflicts
- Code Actions: Alt+Enter for quick fixes
```

## API Requirements

### Backend Requirements
- API version: v1
- Authentication: Bearer token (JWT)
- Base URL: Configurable

### Required Endpoints
```
GET    /api/v1/projects
GET    /api/v1/projects/{id}
GET    /api/v1/projects/{id}/specifications
GET    /api/v1/specifications/{id}
GET    /api/v1/projects/{id}/conflicts
POST   /api/v1/specifications/{id}/generate
GET    /api/v1/auth/me
GET    /health
```

## Performance

### Caching
- Specifications: 5-minute cache
- Projects: 10-minute cache
- Conflicts: Real-time (no cache)
- User: Session cache

### Optimization
- Lazy loading of large datasets
- Background operations with progress
- Request batching where applicable
- Cancellation support

## Troubleshooting

### Connection Issues
1. Verify API endpoint is correct
2. Check network connectivity
3. Verify authentication token
4. Check API server health: `GET /health`

### Code Generation Issues
1. Verify specification exists
2. Check code formatting settings
3. Ensure language is supported
4. Review error messages in output

### IDE Performance
1. Clear specification cache
2. Disable diagnostics temporarily
3. Reduce maximum completion items
4. Check IDE memory usage

## Supported Languages & Frameworks

### Python
- Django, FastAPI, Flask
- pytest, unittest
- Type hints, asyncio
- Dataclasses, Pydantic

### JavaScript/TypeScript
- React, Vue, Angular
- Jest, Mocha, Cypress
- Node.js, Express
- ESM modules, async/await

### Go
- Goroutines, channels
- Error handling patterns
- gRPC support
- Cobra CLI framework

### Java
- Spring, Quarkus
- JUnit, TestNG
- Jakarta EE
- Maven, Gradle

### Other Languages
- Rust (cargo, async-std)
- C# (.NET, LINQ)
- Kotlin (JVM, Android)

## Version History

### Phase 6.1 - VS Code Extension
- Full VS Code integration
- Specification browser
- Code generation
- Basic conflict detection

### Phase 6.2 - JetBrains Plugins
- Base IntelliJ IDEA plugin
- IDE-specific UI components
- Inspections and intentions
- Advanced code analysis

### Phase 6.3 - Language Server Protocol
- LSP server implementation
- Multi-IDE support
- Hover, completion, diagnostics
- Code formatting

### Phase 6.4 - Code Generation
- 8+ language support
- Template-based generation
- Language-specific patterns
- Advanced features (async, generics, builders)

## Support & Documentation

### Help Resources
- [Getting Started Guide](./GETTING_STARTED.md)
- [Configuration Guide](./CONFIGURATION.md)
- [API Documentation](./API.md)
- [Troubleshooting](./TROUBLESHOOTING.md)

### Community
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share experiences
- Wiki: Community documentation and guides

### Commercial Support
For enterprise support, training, and consulting:
- Contact: support@socrates.io
- Website: https://socrates.io

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! See CONTRIBUTING.md for guidelines.

## Acknowledgments

Built with:
- VS Code Extension API
- JetBrains Plugin SDK
- Language Server Protocol
- Jinja2 templates
- Modern async/await patterns

---

**Version:** 1.0.0
**Last Updated:** November 2025
**Status:** Production Ready
