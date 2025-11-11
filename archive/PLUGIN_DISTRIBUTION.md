# Plugin Distribution Guide

Complete guide for publishing and distributing Socrates IDE plugins across all platforms.

## Visual Assets Requirements

### VS Code Extension

#### Icon (128x128 PNG)
- **Filename:** `icon.png`
- **Location:** Root of extension directory
- **Format:** PNG, square, transparent background
- **Content:** Socrates logo or symbol

#### Screenshots (1280x720 PNG)
Required screenshots:
1. `screenshot-project-browser.png` - Project selection and browsing
2. `screenshot-specifications.png` - Specification viewer
3. `screenshot-code-generation.png` - Code generation interface
4. `screenshot-conflict-detection.png` - Conflict highlighting

#### Marketplace Banner (1280x340 PNG)
- **Filename:** `banner.png`
- **Content:** Marketing banner with Socrates branding

### JetBrains Plugins

#### Plugin Icon (80x80 SVG)
- **Filename:** `plugin-icon.svg`
- **Viewbox:** 0 0 80 80
- **Content:** Socrates symbol in SVG format

#### Screenshots (800x600 PNG)
Required screenshots:
1. `jetbrains-project-browser.png` - Tool window
2. `jetbrains-specifications.png` - Specification panel
3. `jetbrains-code-generation.png` - Code generation dialog
4. `jetbrains-conflict-inspection.png` - Conflict detection

#### Plugin Logo (40x40 SVG)
- **Filename:** `logo.svg`
- **For:** JetBrains Marketplace display

## Version Management

### Version Numbering
- **Format:** MAJOR.MINOR.PATCH
- **Example:** 1.0.0
- **Pattern:** Follow Semantic Versioning

### Changelog Format
```
## [1.0.0] - 2025-11-15

### Added
- Feature description

### Fixed
- Bug fix description

### Changed
- Change description
```

## VS Code Extension Publication

### Step 1: Prepare Extension
```bash
# Install dependencies
npm install

# Run tests
npm test

# Build VSIX package
vsce package
```

### Step 2: Create VSCE Token
1. Visit https://marketplace.visualstudio.com/manage
2. Create Personal Access Token (PAT)
3. Store securely

### Step 3: Publish to VS Code Marketplace
```bash
# Login with token
vsce login <publisher-id>

# Publish extension
vsce publish

# Or publish specific version
vsce publish 1.0.0
```

### Step 4: Marketplace Configuration
- **Publisher ID:** socrates2
- **Extension Name:** socrates2
- **Display Name:** Socrates
- **Repository:** GitHub URL
- **License:** MIT
- **Home Page:** https://socrates2.io

## JetBrains Plugin Publication

### Step 1: Prepare Plugin
```bash
# Build plugin
gradle build

# Create signed JAR
gradle signPlugin

# Verify plugin structure
gradle verifyPlugin
```

### Step 2: Register JetBrains Account
1. Visit https://plugins.jetbrains.com/user
2. Create account with email
3. Generate API token

### Step 3: Upload to JetBrains Marketplace
```bash
# Upload plugin
gradle publishPlugin \
  -Dorg.gradle.project.intellijPublishToken=<TOKEN> \
  -Dorg.gradle.project.pluginVerifierIdeVersions=2024.1
```

### Step 4: Marketplace Information

**Plugin Details:**
- **Name:** Socrates
- **Category:** IDE Integration
- **Vendor:** Socrates
- **License:** MIT
- **Plugin ID:** com.socrates2.jetbrains

**Supported IDEs:**
- IntelliJ IDEA (2023.1+)
- PyCharm (2023.1+)
- WebStorm (2023.1+)
- CLion (2023.1+)
- Rider (2023.1+)
- GoLand (2023.1+)
- RubyMine (2023.1+)
- AppCode (2023.1+)
- PhpStorm (2023.1+)

## Language Server Publication

### Step 1: Prepare Package
```bash
# Install build tools
pip install build wheel

# Build package
python -m build

# Create distribution
python setup.py sdist bdist_wheel
```

### Step 2: Publish to PyPI
```bash
# Register on PyPI (https://pypi.org/account/register/)

# Create .pypirc configuration
[distutils]
index-servers =
    pypi

[pypi]
username = __token__
password = <pypi-token>

# Upload to PyPI
twine upload dist/*
```

### Step 3: Setup.py Configuration
```python
setup(
    name='socrates2-lsp',
    version='1.0.0',
    description='Socrates Language Server Protocol implementation',
    author='Socrates',
    author_email='dev@socrates2.io',
    license='MIT',
    packages=['socrates2_lsp'],
    install_requires=[
        'aiohttp>=0.27.0',
        'pydantic>=2.0.0',
        'pyyaml>=6.0',
    ],
    entry_points={
        'console_scripts': [
            'socrates2-lsp=socrates2_lsp.server:main',
        ],
    },
)
```

## Documentation Generation

### README Files Required

#### VS Code: README.md
```markdown
# Socrates for VS Code

Intelligent specification management and code generation.

## Features
- Specification browser
- Real-time conflict detection
- Multi-language code generation
- API integration

## Installation
1. Install from VS Code Marketplace
2. Configure API endpoint
3. Select project

## Documentation
See [full documentation](./docs/README.md)
```

#### JetBrains: plugin-description.md
```markdown
# Socrates for JetBrains IDEs

Specification-aware development for IntelliJ IDEA, PyCharm, WebStorm, and more.

## Key Features
- Project and specification management
- IDE-aware code generation
- Conflict detection and diagnostics
- Language-specific patterns

[Read more...](https://socrates2.io)
```

#### LSP: README.md
```markdown
# Socrates Language Server

LSP implementation for specification-aware development in any LSP-compatible editor.

## Installation
```bash
pip install socrates2-lsp
socrates2-lsp --help
```

## Configuration
See [configuration guide](./docs/CONFIGURATION.md)
```

## Release Checklist

- [ ] Update version in package.json / build.gradle / setup.py
- [ ] Update CHANGELOG.md with release notes
- [ ] Run full test suite
- [ ] Build release packages
- [ ] Test package installation
- [ ] Create GitHub release
- [ ] Publish to all marketplaces
- [ ] Update documentation
- [ ] Post release announcement
- [ ] Monitor feedback

## Security Considerations

### API Security
- Always use HTTPS connections
- Store tokens securely (keychain/vault)
- Implement request signing if required
- Validate SSL certificates

### Code Security
- Sanitize user inputs
- Use safe template rendering
- Escape output in code generation
- Validate generated code before insertion

### Dependency Security
- Regular dependency updates
- Security vulnerability scanning
- License compliance check
- Pin critical dependencies

## Analytics (Optional)

### Usage Metrics
- Track:
  - Install count
  - Active users
  - Most used features
  - Error rates
- Purpose: Improve plugin quality
- Privacy: No user code collection

### Implementation
- Anonymous user ID
- Feature usage tracking
- Error reporting
- Optional telemetry

## Rollback Procedure

### If Issues Detected
1. Disable automatic update (JetBrains)
2. Push patch version with fix
3. Notify users of issue
4. Provide manual rollback instructions
5. Publish post-mortem

### Rollback Steps
```bash
# vs code
vsce unpublish 1.0.0  # Deprecated version

# jetbrains
gradle runPlugin  # Test locally
gradle hidePlugin  # Hide from marketplace

# pypi
pip index versions socrates2-lsp  # Check versions
# Mark newer version as preferred
```

## Support Resources

### For Plugin Users
- GitHub Issues for bugs
- Discussions for questions
- Documentation wiki
- Community forum

### For Developers
- Plugin development documentation
- Sample plugins/extensions
- API reference
- Community Slack

## Marketing & Promotion

### Announcement Channels
1. **GitHub Releases:** Detailed changelog
2. **Twitter:** Quick announcement with features
3. **Blog:** In-depth feature walkthrough
4. **Email:** Newsletter announcement
5. **Community Forums:** Hacker News, Reddit

### Content Ideas
- "Getting Started" tutorial
- Feature showcase videos
- Developer interviews
- Case studies
- Community spotlight

---

**Last Updated:** November 2025
**Version:** 1.0
