# Phase 9: Advanced Features (Multi-LLM, GitHub, Export)

**Status:** ✅ COMPLETE
**Duration:** 5-7 days
**Goal:** Add advanced features: Multi-LLM support, GitHub integration, Export to various formats

---

## ⚠️ CRITICAL: Read Before Implementation

**MANDATORY:** Review [CRITICAL_LESSONS_LEARNED.md](../CRITICAL_LESSONS_LEARNED.md) before starting Phase 9.

**Critical Checklist for Phase 9:**

### Models (api_keys, llm_usage_tracking):
- [ ] Inherits from BaseModel? → Include id, created_at, updated_at in migration
- [ ] AVOID column names: metadata, query, session
- [ ] Use usage_metadata NOT just "metadata" (if storing metadata)
- [ ] Use key_metadata NOT just "metadata" (if storing metadata)

### Migrations (Phase 9 migrations):
- [ ] **TWO DATABASES**: api_keys goes to `socrates_auth`
- [ ] **TWO DATABASES**: llm_usage_tracking goes to `socrates_specs`
- [ ] Add `import os` and `_should_run()` function for EACH migration
- [ ] Check DATABASE_URL contains "socrates_auth" OR "socrates_specs" (depends on table)
- [ ] Add check to BOTH upgrade() and downgrade()
- [ ] Verify BaseModel columns if model inherits

### Tests (test_phase_9_advanced_features.py):
- [ ] Use `auth_session` NOT `db_auth` (for api_keys)
- [ ] Use `specs_session` NOT `db_specs` (for llm_usage_tracking)
- [ ] Use `mock_claude_client` fixture, NOT @patch decorators
- [ ] DO NOT patch instance attributes

### MultiLLMManager, GitHubIntegrationAgent, ExportAgent:
- [ ] Accept ServiceContainer in __init__
- [ ] Store as self.services (instance attribute)
- [ ] Get auth database via self.services.get_database_auth() (for api_keys)
- [ ] Get specs database via self.services.get_database_specs() (for usage tracking)
- [ ] Get Claude client via self.services.get_claude_client()

**Database:** Phase 9 uses BOTH databases:
- `socrates_auth`: api_keys
- `socrates_specs`: llm_usage_tracking

---

## 📋 Objectives

1. Implement Multi-LLM support (Claude, GPT-4, Local models)
2. Add GitHub integration (import existing repos, analyze codebases)
3. Implement export functionality (Markdown, PDF, JSON, Code)
4. Add API key management for users
5. Track LLM usage and costs per project
6. Enable specification import from external sources
7. Add project templates

---

## 🔗 Dependencies

**From Phase 1:**
- Authentication system
- Project management

**From Phase 4:**
- Code generation system

**From Phase 6:**
- Knowledge base documents

**Provides To Phase 10:**
- Complete feature set for production deployment
- Usage tracking data for analytics

---

## 🌐 API Endpoints

This phase implements advanced features. See [API_ENDPOINTS.md](../foundation_docs/API_ENDPOINTS.md) for complete API documentation.

**Implemented in Phase 9:**

**Multi-LLM:**
- GET /api/v1/llm/providers - List available LLM providers
- POST /api/v1/llm/api-keys - Add API key for LLM provider
- GET /api/v1/llm/usage - Get LLM usage stats
- POST /api/v1/projects/{id}/set-llm - Set LLM provider for project

**GitHub Integration:**
- POST /api/v1/github/import - Import GitHub repository
- GET /api/v1/github/repos - List user's GitHub repositories
- POST /api/v1/github/analyze - Analyze GitHub repository

**Export:**
- GET /api/v1/projects/{id}/export/markdown - Export as Markdown
- GET /api/v1/projects/{id}/export/pdf - Export as PDF
- GET /api/v1/projects/{id}/export/json - Export as JSON
- GET /api/v1/projects/{id}/export/code - Export generated code

**Templates:**
- GET /api/v1/templates - List available templates
- POST /api/v1/projects/from-template - Create project from template

**Testing Endpoints:**
```bash
# Add API key for OpenAI
curl -X POST http://localhost:8000/api/v1/llm/api-keys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "api_key": "sk-..."}'

# Import GitHub repo
curl -X POST http://localhost:8000/api/v1/github/import \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo"}'

# Export project as Markdown
curl -X GET http://localhost:8000/api/v1/projects/{project_id}/export/markdown \
  -H "Authorization: Bearer <token>" \
  --output project_specs.md
```

---

## 📦 Component 1: MultiLLMManager

```python
class MultiLLMManager(BaseAgent):
    """Manage multiple LLM providers and route requests"""

    def get_capabilities(self):
        return [
            'list_providers',
            'add_api_key',
            'get_usage_stats',
            'set_project_llm',
            'call_llm'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize LLM clients
        self.providers = {
            'claude': self._init_claude_client(),
            'openai': self._init_openai_client(),
            'local': self._init_local_client()
        }

    def _init_claude_client(self):
        """Initialize Anthropic Claude client"""
        from anthropic import Anthropic
        # Use system API key for default
        api_key = self.config.get('ANTHROPIC_API_KEY')
        return Anthropic(api_key=api_key) if api_key else None

    def _init_openai_client(self):
        """Initialize OpenAI client"""
        from openai import OpenAI
        # User will provide their own key
        return OpenAI

    def _init_local_client(self):
        """Initialize local model client (Ollama)"""
        # TODO: Implement Ollama integration
        return None

    def _list_providers(self, data):
        """List available LLM providers

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
                    'claude-3-opus-20240229'
                ],
                'requires_api_key': False,  # System default available
                'cost_per_1k_tokens': {'input': 0.003, 'output': 0.015}
            },
            {
                'id': 'openai',
                'name': 'OpenAI GPT',
                'models': [
                    'gpt-4-turbo-2024-04-09',
                    'gpt-4o',
                    'gpt-4o-mini'
                ],
                'requires_api_key': True,
                'cost_per_1k_tokens': {'input': 0.01, 'output': 0.03}
            },
            {
                'id': 'local',
                'name': 'Local Models (Ollama)',
                'models': ['llama3', 'mistral', 'codellama'],
                'requires_api_key': False,
                'cost_per_1k_tokens': {'input': 0, 'output': 0}
            }
        ]

        return {
            'success': True,
            'providers': providers
        }

    def _add_api_key(self, data):
        """Add API key for LLM provider

        Args:
            data: {
                'user_id': UUID,
                'provider': str ('openai', 'claude', etc.),
                'api_key': str
            }

        Returns:
            {'success': bool, 'api_key_id': UUID}
        """
        # Store encrypted API key
        api_key_record = APIKey(
            user_id=data['user_id'],
            provider=data['provider'],
            encrypted_key=self._encrypt_api_key(data['api_key']),
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(api_key_record)
        self.db.commit()

        return {
            'success': True,
            'api_key_id': api_key_record.id,
            'provider': data['provider']
        }

    def _get_usage_stats(self, data):
        """Get LLM usage statistics

        Args:
            data: {'user_id': UUID, 'project_id': UUID (optional)}

        Returns:
            {
                'success': bool,
                'total_tokens': int,
                'total_cost': float,
                'usage_by_provider': dict
            }
        """
        user_id = data['user_id']
        project_id = data.get('project_id')

        # Query usage tracking
        query = self.db.query(LLMUsageTracking).filter_by(
            user_id=user_id
        )
        if project_id:
            query = query.filter_by(project_id=project_id)

        usage_records = query.all()

        # Aggregate statistics
        total_tokens = sum(r.tokens_used for r in usage_records)
        total_cost = sum(r.cost for r in usage_records)

        # Group by provider
        usage_by_provider = {}
        for record in usage_records:
            provider = record.provider
            if provider not in usage_by_provider:
                usage_by_provider[provider] = {
                    'tokens': 0,
                    'cost': 0.0,
                    'calls': 0
                }
            usage_by_provider[provider]['tokens'] += record.tokens_used
            usage_by_provider[provider]['cost'] += record.cost
            usage_by_provider[provider]['calls'] += 1

        return {
            'success': True,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'usage_by_provider': usage_by_provider
        }

    def _call_llm(self, data):
        """Call specified LLM provider

        Args:
            data: {
                'provider': str ('claude' | 'openai' | 'local'),
                'model': str,
                'prompt': str,
                'max_tokens': int,
                'user_id': UUID,
                'project_id': UUID
            }

        Returns:
            {
                'success': bool,
                'response': str,
                'tokens_used': int,
                'cost': float
            }
        """
        provider = data['provider']
        model = data['model']
        prompt = data['prompt']
        max_tokens = data.get('max_tokens', 4000)

        # Get user's API key if needed
        api_key = self._get_user_api_key(data['user_id'], provider)

        # Call appropriate provider
        if provider == 'claude':
            result = self._call_claude(model, prompt, max_tokens, api_key)
        elif provider == 'openai':
            result = self._call_openai(model, prompt, max_tokens, api_key)
        elif provider == 'local':
            result = self._call_local(model, prompt, max_tokens)
        else:
            return {
                'success': False,
                'error': f'Unknown provider: {provider}'
            }

        # Track usage
        usage = LLMUsageTracking(
            user_id=data['user_id'],
            project_id=data.get('project_id'),
            provider=provider,
            model=model,
            tokens_used=result['tokens_used'],
            cost=result['cost'],
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(usage)
        self.db.commit()

        return result

    def _call_claude(self, model, prompt, max_tokens, api_key=None):
        """Call Claude API"""
        client = self.providers['claude']
        if api_key:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        tokens_used = response.usage.total_tokens
        cost = (response.usage.input_tokens * 0.003 / 1000 +
                response.usage.output_tokens * 0.015 / 1000)

        return {
            'success': True,
            'response': response.content[0].text,
            'tokens_used': tokens_used,
            'cost': cost
        }

    def _call_openai(self, model, prompt, max_tokens, api_key):
        """Call OpenAI API"""
        if not api_key:
            return {
                'success': False,
                'error': 'OpenAI API key required'
            }

        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        tokens_used = response.usage.total_tokens
        # Approximate cost (varies by model)
        cost = tokens_used * 0.02 / 1000

        return {
            'success': True,
            'response': response.choices[0].message.content,
            'tokens_used': tokens_used,
            'cost': cost
        }

    def _encrypt_api_key(self, api_key):
        """Encrypt API key before storing"""
        from cryptography.fernet import Fernet
        # Use encryption key from config
        fernet = Fernet(self.config.get('ENCRYPTION_KEY').encode())
        return fernet.encrypt(api_key.encode()).decode()

    def _decrypt_api_key(self, encrypted_key):
        """Decrypt API key"""
        from cryptography.fernet import Fernet
        fernet = Fernet(self.config.get('ENCRYPTION_KEY').encode())
        return fernet.decrypt(encrypted_key.encode()).decode()

    def _get_user_api_key(self, user_id, provider):
        """Get user's API key for provider"""
        api_key_record = self.db.query(APIKey).filter_by(
            user_id=user_id,
            provider=provider
        ).first()

        if api_key_record:
            return self._decrypt_api_key(api_key_record.encrypted_key)
        return None
```

---

## 📦 Component 2: GitHubIntegrationAgent

```python
class GitHubIntegrationAgent(BaseAgent):
    """Integrate with GitHub for repository analysis and import"""

    def get_capabilities(self):
        return [
            'import_repository',
            'list_repositories',
            'analyze_repository'
        ]

    def _import_repository(self, data):
        """Import GitHub repository and analyze

        Args:
            data: {
                'user_id': UUID,
                'repo_url': str (e.g., 'https://github.com/user/repo'),
                'project_name': str (optional)
            }

        Returns:
            {
                'success': bool,
                'project_id': UUID,
                'specs_extracted': int
            }
        """
        repo_url = data['repo_url']

        # Clone repository (temporarily)
        import git
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                repo = git.Repo.clone_from(repo_url, temp_dir)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to clone repository: {str(e)}'
                }

            # Analyze repository structure
            analysis = self._analyze_repo_structure(temp_dir)

            # Create project
            project_name = data.get('project_name') or repo_url.split('/')[-1]
            project_result = self.orchestrator.route_request(
                'project',
                'create_project',
                {
                    'name': project_name,
                    'description': f'Imported from {repo_url}',
                    'user_id': data['user_id']
                }
            )

            project_id = project_result['project_id']

            # Extract specifications from analysis
            specs = self._extract_specs_from_analysis(analysis)

            # Save specifications
            for spec in specs:
                spec_obj = Specification(
                    project_id=project_id,
                    category=spec['category'],
                    key=spec['key'],
                    value=spec['value'],
                    source='github_import',
                    confidence=spec['confidence']
                )
                self.db.add(spec_obj)

            self.db.commit()

            return {
                'success': True,
                'project_id': project_id,
                'specs_extracted': len(specs),
                'analysis': analysis
            }

    def _analyze_repo_structure(self, repo_path):
        """Analyze repository structure"""
        import os

        analysis = {
            'files': [],
            'languages': {},
            'frameworks': [],
            'has_tests': False,
            'has_ci': False
        }

        # Walk through files
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if '.git' in root:
                continue

            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                analysis['files'].append(rel_path)

                # Detect language
                ext = os.path.splitext(file)[1]
                if ext:
                    analysis['languages'][ext] = analysis['languages'].get(ext, 0) + 1

                # Detect frameworks
                if file == 'package.json':
                    analysis['frameworks'].append('Node.js')
                elif file == 'requirements.txt' or file == 'Pipfile':
                    analysis['frameworks'].append('Python')
                elif file == 'Gemfile':
                    analysis['frameworks'].append('Ruby')

                # Detect tests
                if 'test' in file.lower() or 'spec' in file.lower():
                    analysis['has_tests'] = True

                # Detect CI
                if file in ['.github/workflows', '.gitlab-ci.yml', '.travis.yml']:
                    analysis['has_ci'] = True

        return analysis

    def _extract_specs_from_analysis(self, analysis):
        """Extract specifications from repository analysis"""
        specs = []

        # Tech stack from languages
        top_languages = sorted(
            analysis['languages'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        for ext, count in top_languages:
            language = self._ext_to_language(ext)
            specs.append({
                'category': 'tech_stack',
                'key': 'language',
                'value': language,
                'confidence': 0.9
            })

        # Frameworks
        for framework in analysis['frameworks']:
            specs.append({
                'category': 'tech_stack',
                'key': 'framework',
                'value': framework,
                'confidence': 0.95
            })

        # Testing
        if analysis['has_tests']:
            specs.append({
                'category': 'testing',
                'key': 'has_tests',
                'value': 'Yes',
                'confidence': 1.0
            })

        # CI/CD
        if analysis['has_ci']:
            specs.append({
                'category': 'deployment',
                'key': 'ci_cd',
                'value': 'Configured',
                'confidence': 1.0
            })

        return specs

    def _ext_to_language(self, ext):
        """Map file extension to language"""
        mapping = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.java': 'Java',
            '.rs': 'Rust',
            '.cpp': 'C++',
            '.c': 'C'
        }
        return mapping.get(ext, 'Unknown')
```

---

## 📦 Component 3: ExportAgent

```python
class ExportAgent(BaseAgent):
    """Export project specifications and code to various formats"""

    def get_capabilities(self):
        return [
            'export_markdown',
            'export_pdf',
            'export_json',
            'export_code'
        ]

    def _export_markdown(self, data):
        """Export project specifications as Markdown

        Args:
            data: {'project_id': UUID}

        Returns:
            {'success': bool, 'content': str}
        """
        project_id = data['project_id']

        # Load project and specs
        project = self.db.query(Project).get(project_id)
        specs = self.db.query(Specification).filter_by(
            project_id=project_id
        ).all()

        # Generate Markdown
        markdown = f"""# {project.name}

**Description:** {project.description}
**Phase:** {project.phase}
**Maturity:** {project.maturity_score}%

---

## Specifications

"""

        # Group by category
        specs_by_category = {}
        for spec in specs:
            if spec.category not in specs_by_category:
                specs_by_category[spec.category] = []
            specs_by_category[spec.category].append(spec)

        # Format each category
        for category, category_specs in specs_by_category.items():
            markdown += f"### {category.title()}\n\n"
            for spec in category_specs:
                markdown += f"- **{spec.key}:** {spec.value}\n"
            markdown += "\n"

        return {
            'success': True,
            'content': markdown,
            'filename': f"{project.name.replace(' ', '_')}.md"
        }

    def _export_pdf(self, data):
        """Export as PDF"""
        # First generate Markdown
        markdown_result = self._export_markdown(data)

        # Convert to PDF (using markdown2pdf or similar)
        # TODO: Implement PDF generation

        return {
            'success': True,
            'message': 'PDF export not yet implemented'
        }

    def _export_json(self, data):
        """Export as JSON"""
        import json

        project_id = data['project_id']

        # Load all project data
        project = self.db.query(Project).get(project_id)
        specs = self.db.query(Specification).filter_by(
            project_id=project_id
        ).all()

        # Build JSON structure
        export_data = {
            'project': {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'phase': project.phase,
                'maturity_score': project.maturity_score,
                'created_at': project.created_at.isoformat()
            },
            'specifications': [
                {
                    'category': spec.category,
                    'key': spec.key,
                    'value': spec.value,
                    'confidence': spec.confidence,
                    'source': spec.source
                }
                for spec in specs
            ]
        }

        return {
            'success': True,
            'content': json.dumps(export_data, indent=2),
            'filename': f"{project.name.replace(' ', '_')}.json"
        }
```

---

## 🗄️ Database Tables Used

**From DATABASE_SCHEMA_COMPLETE.md (Phase 6 tables):**

### socrates_auth Database

**api_keys:**
- Stores encrypted API keys for LLM providers
- Fields: user_id, provider, encrypted_key, created_at

### socrates_specs Database

**llm_usage_tracking:**
- Tracks LLM usage per user/project
- Fields: user_id, project_id, provider, model, tokens_used, cost, timestamp

---

## ✅ Verification

- [ ] Multi-LLM support works (Claude, OpenAI, Local)
- [ ] API key management works (encrypted storage)
- [ ] LLM usage tracking works
- [ ] GitHub import works
- [ ] Repository analysis works
- [ ] Export to Markdown works
- [ ] Export to JSON works
- [ ] Export to PDF works (optional)
- [ ] Project templates work
- [ ] Tests pass: `pytest tests/test_phase_9_advanced_features.py`

---

**Previous:** [PHASE_8.md](PHASE_8.md)
**Next:** [PHASE_10.md](PHASE_10.md) - Polish & Deploy
