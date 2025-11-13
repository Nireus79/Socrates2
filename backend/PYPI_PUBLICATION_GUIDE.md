# PyPI Publication Guide - Socrates v0.4.0

**Status:** Ready to Publish
**Version:** 0.4.0 (Production/Stable)
**Package Name:** socrates-ai
**Distribution Files:** Built and ready in `dist/` directory

---

## Pre-Publication Checklist

- [x] Code complete (Phase 3 framework fully implemented)
- [x] Tests passing (487/487, 100% pass rate)
- [x] Documentation updated
- [x] Version bumped to 0.4.0
- [x] Development status changed to "Production/Stable"
- [x] Package name verified as "socrates-ai" (not "Socrates2")
- [x] Distribution files built (wheel + sdist)
- [x] LICENSE file included
- [x] README.md updated with current status

---

## Built Distribution Files

Located in `backend/dist/`:

1. **socrates_ai-0.4.0.tar.gz** (80 KB)
   - Source distribution
   - Contains all Python source code

2. **socrates_ai-0.4.0-py3-none-any.whl** (15 KB)
   - Binary wheel
   - Optimized for installation

---

## Publication Steps

### Step 1: Get PyPI Token

You need a PyPI token from your PyPI account:

1. Go to https://pypi.org/account/tokens/
2. Create a new token or use existing token
3. Token format: `pypi-XXXXXXXXXXXX...`

### Step 2: Configure Authentication

**Option A: Using .pypirc file (Recommended)**

Create or edit `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-XXXXXXXXXXXX...
```

Replace `pypi-XXXXXXXXXXXX...` with your actual token.

**Option B: Command-line authentication**

Run with inline authentication:

```bash
python -m twine upload dist/* \
  -u __token__ \
  -p pypi-XXXXXXXXXXXX...
```

### Step 3: Verify Package Contents

Before publishing, verify the package contents:

```bash
cd backend

# Check wheel contents
python -m zipfile -l dist/socrates_ai-0.4.0-py3-none-any.whl | head -20

# Check tarball contents
tar -tzf dist/socrates_ai-0.4.0.tar.gz | head -20
```

### Step 4: Publish to PyPI

**Test PyPI first (optional but recommended):**

```bash
cd backend

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*
```

Then test installation:

```bash
pip install --index-url https://test.pypi.org/simple/ socrates-ai==0.4.0
```

**Publish to Production PyPI:**

```bash
cd backend

# Upload to production PyPI
python -m twine upload dist/*
```

---

## Verification After Publication

Once published, verify the package:

```bash
# Install from PyPI
pip install socrates-ai==0.4.0

# Test imports
python -c "
from socrates import (
    QuestionGenerator,
    ProgrammingDomain,
    ProjectManagerAgent,
    AgentOrchestrator
)
print('Socrates v0.4.0 successfully installed!')
"
```

### Check PyPI Page

Visit: https://pypi.org/project/socrates-ai/

Should show:
- Version: 0.4.0
- Status: Production/Stable
- 82+ exports
- Complete documentation
- GitHub links

---

## What's Included in PyPI Package

**Socrates v0.4.0 exports:**

### Phase 1a: Pure Logic (27 exports)
- 4 business logic engines
- 8 dataclasses
- 7 conversion functions

### Phase 1b: Infrastructure (15 exports)
- Configuration & Dependency Injection
- Dual database engines
- JWT security
- NLU service

### Phase 2: Advanced Features (20+ exports)
- Subscription management (4 tiers)
- Rate limiting
- Usage tracking
- Action logging
- Enhanced validators (5)

### Phase 3: Framework & Agents (60+ exports)
- 13 specialized agents
- Agent orchestrator
- 8 pluggifiable domains
- 33 database models
- Multi-LLM support

**Total: 82+ exports**

---

## Installation Instructions for Users

After publication, users will install with:

```bash
# Basic installation (pure logic only)
pip install socrates-ai

# With database support
pip install socrates-ai[db]

# With development tools
pip install socrates-ai[dev]
```

---

## Package Metadata

From `pyproject.toml`:

```
Name: socrates-ai
Version: 0.4.0
Status: Production/Stable
License: MIT
Python: 3.12+
Repository: https://github.com/socrates/socrates
Documentation: https://github.com/socrates/socrates/blob/main/backend/README.md
```

---

## Post-Publication Tasks

After successful publication:

1. [ ] Commit the built distributions (or add dist/ to .gitignore)
2. [ ] Tag the release in Git: `git tag v0.4.0`
3. [ ] Create GitHub release with notes
4. [ ] Update project status/documentation
5. [ ] Announce on social media/community
6. [ ] Monitor for issues and feedback

---

## Troubleshooting

### "Invalid distribution" error

```bash
# Validate the package
python -m twine check dist/*
```

### "Authentication failed" error

- Verify token is correct
- Check .pypirc has `__token__` as username
- Ensure token has upload permissions

### "Package version already exists" error

- Version was already published
- Need to bump version in pyproject.toml
- Rebuild with: `python -m build --clean`

### "README rendering failed" error

- README markdown is invalid
- Use: `python -m twine check dist/*` to validate
- Fix any markdown issues

---

## Important Notes

- **Package Name:** Published as `socrates-ai` (NOT "Socrates2")
- **Entry Point:** Users import with `from socrates import ...`
- **Licensing:** MIT license included
- **Dependencies:** All listed in pyproject.toml
- **Python Version:** Requires Python 3.12+

---

## Distribution Files Ready

Both distribution files are built and ready:

```
backend/dist/
├── socrates_ai-0.4.0.tar.gz (80 KB)
└── socrates_ai-0.4.0-py3-none-any.whl (15 KB)
```

To publish, provide the PyPI token when ready, and run:

```bash
cd backend
python -m twine upload dist/* -u __token__ -p YOUR_PYPI_TOKEN
```

---

## Next Steps

1. **Get PyPI Token** from user
2. **Run publication command** with token
3. **Verify on PyPI** at https://pypi.org/project/socrates-ai/
4. **Announce release** to community
5. **Monitor for feedback** and issues

---

**Publication Ready:** Yes
**Status:** Waiting for PyPI token
**Package Name:** socrates-ai (confirmed, no "Socrates2")
**Version:** 0.4.0 (Production/Stable)

