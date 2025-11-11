# Contributing to Socrates

Thank you for your interest in contributing to Socrates! This document provides guidelines and instructions for contributing.

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and adhere to our principles:

- Be respectful and inclusive
- Welcome differing opinions and experiences
- Focus on constructive criticism
- Report inappropriate behavior to dev@socrates2.io

## How to Contribute

### 1. Report Bugs

Found a bug? Please create an issue with:

- **Clear title:** Describe the bug concisely
- **Description:** Detailed explanation of the problem
- **Steps to reproduce:** How to reliably reproduce the issue
- **Expected vs actual behavior:** What should happen vs what does happen
- **Environment:** IDE version, OS, plugin version
- **Screenshots:** If applicable

**Label:** `bug`

### 2. Suggest Enhancements

Have an idea? Please create an issue with:

- **Clear title:** Feature description
- **Detailed description:** What would you like and why
- **Use cases:** How would users benefit
- **Possible solutions:** Any technical suggestions
- **Additional context:** Screenshots, examples, references

**Label:** `enhancement`

### 3. Submit Code Changes

#### Prerequisites
- Git knowledge
- IDE installed (VS Code or JetBrains)
- Relevant programming language environment:
  - TypeScript for VS Code extension
  - Kotlin for JetBrains plugins
  - Python for LSP server

#### Process

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/Socrates.git
   cd Socrates
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
   - Use descriptive names: `feature/`, `fix/`, `docs/`, `test/`

3. **Make your changes**
   - Follow the coding standards (see below)
   - Add tests for new functionality
   - Update documentation
   - Keep commits focused and well-described

4. **Run tests**
   ```bash
   # VS Code Extension
   cd extensions/vs-code
   npm test

   # JetBrains Plugins
   cd plugins/jetbrains
   ./gradlew test

   # LSP Server
   cd backend/lsp
   pytest
   ```

5. **Commit with clear messages**
   ```bash
   git commit -m "feat: Add awesome feature

   Detailed description of the change.
   Explain why this change was needed.
   Reference any relevant issues: #123"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Title: Clear description of changes
   - Description: Detail the changes and motivation
   - Link related issues: "Fixes #123"
   - Ensure CI/CD passes

### 4. Improve Documentation

Documentation improvements are always welcome:

- README files
- Code comments and docstrings
- Architecture documentation
- User guides
- API documentation

## Coding Standards

### TypeScript (VS Code Extension)

```typescript
// Use strict types
function processSpecification(spec: Specification): Promise<GeneratedCode> {
  // Implementation
}

// Use async/await
async function fetchData(): Promise<Data> {
  return await api.get('/data');
}

// Document public APIs
/**
 * Generate code from specification
 * @param spec - Input specification
 * @param language - Target language
 * @returns Generated code object
 */
```

**Standards:**
- Use strict mode (`"strict": true` in tsconfig.json)
- Full type annotations on public APIs
- JSDoc comments for public functions
- 2-space indentation
- Prefer `const` over `let`
- Use arrow functions where appropriate

### Kotlin (JetBrains Plugins)

```kotlin
// Use nullable types correctly
suspend fun getProject(id: String): Project? {
    return try {
        api.getProject(id)
    } catch (e: Exception) {
        null
    }
}

// Use coroutines for async
class ProjectService(private val apiClient: SocratesApiClient) {
    suspend fun loadProjects(): Result<List<Project>> {
        return try {
            Result.success(apiClient.getProjects())
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

// Document with KDoc
/**
 * Load project from API
 * @param projectId the project identifier
 * @return [Result] with project data or error
 */
```

**Standards:**
- Use Kotlin idioms
- Coroutines for async operations
- Result<T> for error handling
- KDoc comments for public APIs
- 4-space indentation
- Prefer `val` over `var`

### Python (LSP Server)

```python
"""Module docstring explaining purpose"""

from typing import Optional, Dict, List

async def get_hover_information(
    uri: str,
    line: int,
    character: int,
    document_text: str,
    project_id: Optional[str] = None
) -> Optional[Dict]:
    """
    Fetch hover information for specification reference.

    Args:
        uri: Document URI
        line: Line number
        character: Character position
        document_text: Full document text
        project_id: Optional project context

    Returns:
        Hover information or None if not found

    Raises:
        ValueError: If input validation fails
    """
    # Implementation
```

**Standards:**
- Type hints on all functions
- Docstrings for all public functions (Google style)
- 4-space indentation
- PEP 8 compliance
- Use `async`/`await` for async operations
- Descriptive variable names

### Templates (Jinja2)

```jinja2
{#- Class template for {{ name }} -#}
class {{ name }}:
    """{{ docstring }}"""

    def __init__(self) -> None:
        {#- Constructor documentation -#}
        self.id: str = self.generate_id()

    {% if async -%}
    async def process(self) -> None:
        """Async process method"""
        pass
    {% endif -%}
```

**Standards:**
- Clear section comments
- Language-specific idioms
- Type hints in generated code
- Docstrings for all classes and methods

## Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Test additions/changes
- `chore`: Build, dependencies, tooling

**Examples:**
```
feat(code-gen): Add Rust code generation template

- Implement struct generation with serde support
- Add async/await pattern support
- Include builder pattern implementation

Fixes #456
```

```
fix(lsp): Correct specification reference extraction

Extract specification references at cursor position correctly
handling @spec.key patterns. Prevent regex edge cases.

Fixes #123
```

## Testing Guidelines

### Test Coverage Requirements
- Minimum 80% code coverage
- All public APIs must have tests
- Edge cases and error conditions tested
- Integration tests for major workflows

### Writing Tests

**TypeScript (Jest):**
```typescript
describe('SpecificationService', () => {
  let service: SpecificationService;

  beforeEach(() => {
    service = new SpecificationService(mockApiClient);
  });

  it('should load specifications from API', async () => {
    const specs = await service.loadSpecifications('proj-1');
    expect(specs).toHaveLength(3);
    expect(specs[0].key).toBe('api.endpoint');
  });

  it('should handle API errors gracefully', async () => {
    mockApiClient.getSpecifications.mockRejectedValue(new Error('API error'));
    const specs = await service.loadSpecifications('proj-1');
    expect(specs).toEqual([]);
  });
});
```

**Python (Pytest):**
```python
@pytest.mark.asyncio
async def test_get_specifications():
    """Test specification retrieval"""
    client = MockApiClient()
    specs = await client.get_specifications('proj-1')
    assert len(specs) == 3
    assert specs[0].key == 'api.endpoint'

@pytest.mark.asyncio
async def test_handle_api_error():
    """Test error handling in API client"""
    client = MockApiClient()
    client.should_fail = True
    with pytest.raises(ApiError):
        await client.get_specifications('proj-1')
```

## Documentation Updates

When adding features, update relevant documentation:

1. **Code Comments:** Inline documentation for complex logic
2. **Docstrings/JSDoc:** All public APIs
3. **README:** User-facing features
4. **Architecture Docs:** System design changes
5. **CHANGELOG:** User-visible changes

## Pull Request Process

1. **PR Title:** Clear, descriptive, following commit conventions
2. **PR Description:**
   - What changes were made
   - Why these changes were needed
   - How to test the changes
   - Links to related issues
3. **Code Review:** Address feedback promptly
4. **CI/CD:** Ensure all checks pass
5. **Merge:** After approval by maintainers

## Development Setup

### VS Code Extension
```bash
cd extensions/vs-code
npm install
npm run compile
npm test
code --extensionDevelopmentPath=. .
```

### JetBrains Plugins
```bash
cd plugins/jetbrains
./gradlew build
./gradlew runIde  # Run in IDE sandbox
```

### LSP Server
```bash
cd backend/lsp
pip install -e ".[dev]"
python -m pytest
```

## Release Process

Releases follow [Semantic Versioning](https://semver.org/):

1. Update version numbers
2. Update CHANGELOG.md
3. Create git tag
4. Publish to marketplaces
5. Announce release

## Getting Help

- **GitHub Issues:** Report bugs and request features
- **GitHub Discussions:** Ask questions
- **Email:** dev@socrates2.io
- **Documentation:** See README and CONTRIBUTING.md files

## License

By contributing, you agree your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributors page

---

Thank you for contributing to Socrates! Your efforts help make IDE integration better for everyone.
