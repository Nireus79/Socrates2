# Phase 4: Code Generation & Maturity Gates

**Status:** ⏳ PENDING
**Duration:** 3-4 days
**Goal:** Generate code when project reaches 100% maturity

---

## 📋 Objectives

1. Create CodeGeneratorAgent
2. Implement maturity gate (blocks if < 100%)
3. Load ALL specifications for code generation
4. Generate complete codebase via Claude API
5. Save generated code to database

---

## 🔗 Dependencies

**From Phase 3:**
- All conflict-free specifications in database
- Project.maturity_score accurately calculated
- No pending conflicts

**Provides To Phase 5:**
- Working code generation
- Maturity-gated workflow (Quality Control will enhance this)

---

## 📦 Key Deliverable: CodeGeneratorAgent

```python
class CodeGeneratorAgent(BaseAgent):
    def get_capabilities(self):
        return ['generate_code']

    def _generate_code(self, data):
        project_id = data['project_id']

        # GATE 1: Check maturity
        project = self.db.query(Project).get(project_id)
        if project.maturity_score < 100.0:
            return {
                'success': False,
                'error': f'Project maturity is {project.maturity_score}%. Need 100%.',
                'error_code': 'MATURITY_NOT_REACHED',
                'maturity_score': project.maturity_score,
                'missing_categories': self._identify_gaps(project_id)
            }

        # Load ALL specifications
        specs = self.db.query(Specification).filter_by(
            project_id=project_id
        ).all()

        # Group by category
        grouped = self._group_specs_by_category(specs)

        # Build comprehensive prompt (10,000+ tokens)
        prompt = self._build_code_generation_prompt(project, grouped)

        # Call Claude API with high token limit
        response = self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=15000,
            messages=[{"role": "user", "content": prompt}]
        )

        code = response.content[0].text

        # Save to database
        codebase = GeneratedCodebase(
            project_id=project_id,
            code=code,
            model_used="claude-3-5-sonnet-20241022",
            tokens_used=response.usage.total_tokens
        )
        self.db.add(codebase)
        self.db.commit()

        return {
            'success': True,
            'codebase_id': codebase.id,
            'code': code,
            'tokens_used': response.usage.total_tokens
        }

    def _build_code_generation_prompt(self, project, grouped_specs):
        return f"""Generate a complete, production-ready codebase.

PROJECT: {project.name}
DESCRIPTION: {project.description}

SPECIFICATIONS:

GOALS:
{self._format_specs(grouped_specs.get('goals', []))}

REQUIREMENTS:
{self._format_specs(grouped_specs.get('requirements', []))}

TECH STACK:
{self._format_specs(grouped_specs.get('tech_stack', []))}

SCALABILITY:
{self._format_specs(grouped_specs.get('scalability', []))}

SECURITY:
{self._format_specs(grouped_specs.get('security', []))}

... [all 10 categories]

Generate complete codebase including:
1. Project structure
2. Database schema and migrations
3. Backend API implementation
4. Frontend (if specified)
5. Tests (unit + integration)
6. Docker configuration
7. README with setup instructions

Return the code organized by files.
"""
```

---

## 🧪 Critical Tests

```python
def test_maturity_gate_blocks():
    """Test code generation blocked when maturity < 100%"""
    result = code_agent.process_request('generate_code', {
        'project_id': incomplete_project.id
    })
    assert result['success'] == False
    assert 'MATURITY_NOT_REACHED' in result['error_code']
    assert result['maturity_score'] < 100.0

def test_code_generation_success():
    """Test generates code when maturity = 100%"""
    result = code_agent.process_request('generate_code', {
        'project_id': complete_project.id
    })
    assert result['success'] == True
    assert 'code' in result
    assert len(result['code']) > 1000  # Generated substantial code

def test_all_specs_included():
    """Test generated code includes ALL specifications"""
    result = code_agent.process_request('generate_code', {...})
    code = result['code']

    # Verify specs are in code
    assert 'PostgreSQL' in code  # Tech stack spec
    assert 'FastAPI' in code  # Framework spec
    assert 'pytest' in code  # Testing spec
```

---

## ✅ Verification

- [ ] CodeGeneratorAgent created
- [ ] Maturity gate blocks if < 100%
- [ ] Loads all specifications
- [ ] Generates code via Claude API
- [ ] Generated code is valid (syntax check)
- [ ] Code saved to database
- [ ] Tests pass

---

**Previous:** [PHASE_3.md](./PHASE_3.md)
**Next:** [PHASE_5.md](./PHASE_5.md)
