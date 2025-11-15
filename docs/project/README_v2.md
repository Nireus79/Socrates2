# Socrates 🧠

**AI-Powered Intelligent Specification & Requirements Engineering Platform**

[![Python 3.12](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791.svg)](https://www.postgresql.org/)
[![Tests Passing](https://img.shields.io/badge/tests-300%2B%20passing-green.svg)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 What is Socrates?

Socrates is an **AI-powered specification and requirements engineering platform** that helps teams:

- **📋 Gather Requirements** - Systematic approach across 7 knowledge domains
- **🤖 Leverage AI** - Claude powers intelligent Socratic questioning
- **🏗️ Build Specifications** - Automatic specification generation from conversations
- **👥 Collaborate** - Team-based specification development with role-based access
- **📊 Analyze** - Completeness metrics, conflict detection, recommendations
- **📄 Export** - Multiple formats (Markdown, PDF, JSON, CSV)

**The Socratic Method at Scale** - Ask better questions to uncover better requirements.

---

## 📚 Documentation

### Quick Navigation

| Role | Start Here | Time |
|------|-----------|------|
| **User** | [Getting Started](docs/user/GETTING_STARTED.md) | 15 min |
| **User** | [User Guide](docs/user/USER_GUIDE.md) | 30 min |
| **Developer** | [Development Setup](docs/developer/DEVELOPMENT_SETUP.md) | 20 min |
| **Developer** | [Architecture Guide](docs/developer/ARCHITECTURE.md) | 45 min |
| **Developer** | [API Reference](docs/developer/API_REFERENCE.md) | 30 min |
| **Operations** | [Deployment Guide](docs/operations/DEPLOYMENT.md) | 45 min |
| **Leadership** | [Project Overview](docs/presentation/PROJECT_OVERVIEW.md) | 15 min |

### Complete Documentation Index

👉 **[View Full Documentation Index →](docs/INDEX.md)**

**Documentation Structure:**
```
docs/
├── user/                  # End-user documentation
├── developer/             # Developer guides and API reference
├── operations/            # Deployment and operations
├── presentation/          # Business and leadership docs
└── technical-specs/       # Technical specifications
```

---

## ✨ Key Features

### 🏗️ Seven Knowledge Domains

Comprehensive coverage across all aspects:

| Domain | Focus | Questions | Topics |
|--------|-------|-----------|--------|
| **Architecture** | 🏗️ System Design | 20 | Components, patterns, scalability |
| **Programming** | 💻 Implementation | 18 | Stack, frameworks, code organization |
| **Testing** | ✅ Quality Assurance | 16 | Test strategy, coverage, metrics |
| **Data Engineering** | 📊 Data Management | 17 | Models, ETL, analytics |
| **Security** | 🔒 Security & Compliance | 19 | Auth, protection, compliance |
| **Business** | 💼 Business Context | 16 | Use cases, goals, ROI |
| **DevOps** | 🚀 Operations | 17 | Infrastructure, deployment, monitoring |

**Total:** 100+ pre-configured questions

### 🤖 AI-Powered Intelligence

- Claude 3.5 Sonnet integration
- Context-aware question generation
- Assumption surfacing and validation
- Cross-domain conflict detection
- Automated recommendation engine
- Natural conversation flow

### 📊 Specification Management

- Automatic specification generation
- Confidence scoring (0-1 scale)
- Multi-category organization
- Status tracking (draft → approved → implemented)
- Version history and change tracking
- Team discussion threads

### 👥 Team Collaboration

- Role-based access control
  - **Owner** - Full control
  - **Editor** - Can modify specs and sessions
  - **Viewer** - Read-only access
- Team member invitations
- Collaborative sessions
- Activity tracking
- Permission management

### 🔄 Multi-Domain Workflows

- Execute across multiple domains simultaneously
- Cross-domain conflict detection
- Integrated recommendations
- Complete specifications in single workflow
- Export results as documents

### 📈 Analysis & Metrics

- **Project Maturity** - Overall progress (0-1 score)
- **Domain Completeness** - Coverage by domain
- **Specification Confidence** - Certainty of each spec
- **Conflict Detection** - Automatic issue identification
- **Missing Items** - Gap analysis
- **Recommendations** - Next actions

### 📤 Export & Integration

**Export Formats:**
- Markdown (GitHub, wikis, docs)
- PDF (printing, distribution)
- JSON (API, tools)
- CSV (spreadsheets, analysis)

**Integrations (Future):**
- GitHub (sync to repos)
- Jira (create issues)
- Confluence (publish)
- Slack (notifications)

---

## 🚀 Quick Start

### 5 Minutes to Running

```bash
# 1. Clone repository
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# 2. Install dependencies
cd backend
pip install -e ".[dev]"

# 3. Set up database
export DATABASE_URL_AUTH="postgresql://user:password@localhost:5432/socrates_auth"
export DATABASE_URL_SPECS="postgresql://user:password@localhost:5432/socrates_specs"
alembic upgrade head

# 4. Start server
python -m uvicorn app.main:app --reload

# 5. Access API
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### First Steps

1. **[Getting Started Guide](docs/user/GETTING_STARTED.md)** - 15 min quick start
2. **[User Guide](docs/user/USER_GUIDE.md)** - Learn all features
3. **Create account** - Register via API or UI
4. **Create project** - Start your first project
5. **Begin session** - Answer domain-specific questions
6. **Review specs** - See gathered specifications

---

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI 0.121.0
- **Server:** Uvicorn with async/await
- **Language:** Python 3.12
- **ORM:** SQLAlchemy 2.0.44
- **Migrations:** Alembic 1.14.0

### Database
- **Primary:** PostgreSQL 17
- **Architecture:** Two-database design
  - socrates_auth (user/auth data)
  - socrates_specs (specifications/projects)
- **ORM:** SQLAlchemy with modern patterns

### Authentication
- **Token:** JWT (HS256)
- **Password:** bcrypt with 10 rounds
- **Validation:** Pydantic with email validation
- **Refresh:** Token rotation strategy

### External Services
- **LLM:** Anthropic Claude 3.5 Sonnet
- **Email:** SendGrid (future)
- **Monitoring:** Sentry (future)

### Development Tools
- **Testing:** pytest with 300+ test methods
- **Formatting:** Black
- **Linting:** Ruff
- **Type Checking:** Mypy
- **CI/CD:** GitHub Actions (template ready)

---

## 📊 Project Statistics

### Code Metrics
| Metric | Value |
|--------|-------|
| **Production Code** | 3,486 lines |
| **Test Code** | 8,937 lines |
| **API Endpoints** | 40+ |
| **Test Methods** | 300+ |
| **Test Pass Rate** | 100% ✅ |
| **Models** | 10+ |
| **Services** | 8+ |
| **Domains** | 7 |

### Test Coverage
- **API Endpoints** - 40+ endpoint tests
- **Authentication** - 30+ auth tests
- **Authorization** - 20+ permission tests
- **Error Handling** - 45+ error case tests
- **End-to-End** - 15+ workflow tests
- **Pagination** - 10+ pagination tests
- **Health Checks** - System monitoring tests

### Documentation
- **User Guides** - 4 documents
- **Developer Guides** - 5+ documents
- **API Reference** - Complete OpenAPI spec
- **Architecture** - System design documentation
- **Operations** - Deployment and ops guides

---

## 🔐 Security Features

✅ **Authentication & Authorization**
- JWT-based authentication
- Bcrypt password hashing
- Refresh token rotation
- Role-based access control

✅ **Data Protection**
- SQL injection prevention (ORM)
- XSS prevention (JSON responses)
- CSRF protection (stateless API)
- Input validation (Pydantic)

✅ **API Security**
- CORS configuration
- Rate limiting (configurable)
- Request validation
- Error handling

✅ **Operations**
- Secure environment variables
- Connection string encryption
- Audit logging (future)
- Compliance ready

---

## 📖 Complete Documentation

### User Documentation
- [Getting Started](docs/user/GETTING_STARTED.md) - Quick start guide
- [User Guide](docs/user/USER_GUIDE.md) - Complete feature guide
- [Tutorials](docs/user/TUTORIALS.md) - Step-by-step examples
- [FAQ](docs/user/FAQ.md) - Frequently asked questions
- [Glossary](docs/user/GLOSSARY.md) - Term definitions

### Developer Documentation
- [Development Setup](docs/developer/DEVELOPMENT_SETUP.md) - Environment setup
- [Architecture Guide](docs/developer/ARCHITECTURE.md) - System design
- [API Reference](docs/developer/API_REFERENCE.md) - Complete API docs
- [Testing Guide](docs/developer/TESTING_GUIDE.md) - Test strategy
- [Contributing Guide](docs/developer/CONTRIBUTING.md) - How to contribute
- [Code Style](docs/developer/CODE_STYLE.md) - Coding standards

### Operations Documentation
- [Deployment Guide](docs/operations/DEPLOYMENT.md) - Production deployment
- [Configuration](docs/operations/CONFIGURATION.md) - System setup
- [Monitoring](docs/operations/MONITORING.md) - Health & metrics
- [Troubleshooting](docs/operations/TROUBLESHOOTING.md) - Problem solving
- [Backup & Recovery](docs/operations/BACKUP.md) - Data protection

### Technical Specifications
- [Database Schema](docs/technical-specs/DATABASE.md) - Data models
- [Security Architecture](docs/technical-specs/SECURITY.md) - Security design
- [Performance Specs](docs/technical-specs/PERFORMANCE.md) - Performance characteristics
- [Scalability](docs/technical-specs/SCALABILITY.md) - Scaling strategies

### Business Documentation
- [Project Overview](docs/presentation/PROJECT_OVERVIEW.md) - Vision & mission
- [Features & Benefits](docs/presentation/FEATURES.md) - Capabilities
- [Product Roadmap](docs/presentation/ROADMAP.md) - Future plans
- [Use Cases](docs/presentation/USE_CASES.md) - Real-world scenarios

---

## 🧪 Testing

### Test Suite

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth_endpoints.py -v

# Run tests by marker
pytest -m api                    # API tests only
pytest -m e2e                    # End-to-end tests
pytest -m error                  # Error handling tests
pytest -m security               # Security tests

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Test Files (35 total)

**Endpoint Tests:**
- test_auth_endpoints.py - 30+ auth tests
- test_projects_endpoints.py - 25+ project tests
- test_questions_endpoints.py - 20+ question tests
- test_specifications_endpoints.py - 25+ spec tests
- test_sessions_endpoints.py - 20+ session tests
- test_teams_endpoints.py - 20+ team tests
- test_workflows_endpoints.py - 20+ workflow tests
- test_domains_endpoints.py - 15+ domain tests

**Cross-Cutting Tests:**
- test_authorization.py - 20+ permission tests
- test_error_handling.py - 45+ error tests
- test_pagination_sorting.py - 20+ pagination tests
- test_e2e_complete_workflow.py - 15+ E2E tests
- test_health_and_system.py - 10+ system tests

---

## 🏗️ Project Structure

```
Socrates/
├── docs/                          # Documentation
│   ├── user/                      # User guides
│   ├── developer/                 # Developer docs
│   ├── operations/                # Operations guides
│   ├── presentation/              # Business docs
│   └── technical-specs/           # Technical specs
│
├── backend/
│   ├── app/
│   │   ├── api/                   # API endpoints (40+)
│   │   ├── models/                # Data models
│   │   ├── services/              # Business logic
│   │   ├── repositories/          # Data access
│   │   ├── domains/               # Knowledge domains (7)
│   │   ├── agents/                # AI agents
│   │   └── core/                  # Core utilities
│   │
│   ├── tests/                     # Test suite (300+ tests)
│   ├── alembic/                   # Database migrations
│   ├── pyproject.toml             # Project configuration
│   ├── requirements.txt           # Production dependencies
│   └── requirements-dev.txt       # Development dependencies
│
├── README.md                      # This file
├── LICENSE                        # MIT License
└── PYCHARM_LOCAL_SETUP_ROADMAP.md # IDE setup guide
```

---

## 🚀 Deployment

### Local Development
See [Development Setup](docs/developer/DEVELOPMENT_SETUP.md)

### Docker Deployment
See [Deployment Guide](docs/operations/DEPLOYMENT.md)

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] API health check passing
- [ ] Tests passing
- [ ] Documentation reviewed
- [ ] Monitoring configured
- [ ] Backup strategy enabled

---

## 💻 API Examples

### Create Project
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "description": "Project description",
    "maturity_score": 0.0
  }'
```

### Start Session
```bash
curl -X POST http://localhost:8000/api/v1/projects/{id}/sessions \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Initial Requirements",
    "domains": ["architecture", "programming"]
  }'
```

### Submit Answer
```bash
curl -X POST http://localhost:8000/api/v1/projects/{id}/sessions/{sid}/answer \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"answer": "Your answer here"}'
```

See [API Reference](docs/developer/API_REFERENCE.md) for complete API documentation.

---

## 🔄 Workflow Example

**Building an E-Commerce Platform:**

```
1. Register Account
   ↓
2. Create Project "E-Commerce Platform"
   ↓
3. Start Session (Architecture Domain)
   ↓ Questions about system design
4. AI generates architecture specifications
   ↓
5. Start Session (Programming Domain)
   ↓ Questions about tech stack
6. AI generates implementation specifications
   ↓
7. Start Session (Security Domain)
   ↓ Questions about security requirements
8. AI generates security specifications
   ↓
9. Review All Specifications
   ↓
10. Create Multi-Domain Workflow
    ↓ Cross-domain analysis
11. Export as Markdown Document
    ↓
12. Share with team
    ↓
13. Begin implementation based on specs
```

---

## 📊 Key Metrics

### Maturity Score
```
0.0 - 0.3    Early stage (concept)
0.3 - 0.6    Moderate (some clarity)
0.6 - 0.8    Mature (well-defined)
0.8 - 1.0    Complete (production-ready)
```

### Confidence Score
```
0.0 - 0.3    Uncertain
0.3 - 0.6    Provisional
0.6 - 0.8    Solid
0.8 - 1.0    Certain
```

---

## 🤝 Contributing

Socrates is open source and welcomes contributions!

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** your changes (`pytest tests/`)
5. **Submit** a pull request

See [Contributing Guide](docs/developer/CONTRIBUTING.md) for details.

---

## 📝 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **GitHub:** https://github.com/Nireus79/Socrates
- **Documentation:** [View Docs](docs/INDEX.md)
- **API Reference:** [API Docs](docs/developer/API_REFERENCE.md)
- **Project Overview:** [Overview](docs/presentation/PROJECT_OVERVIEW.md)

---

## ❓ FAQ

**Q: What is Socratic method?**
A: A teaching method that uses probing questions to guide discovery and uncover knowledge gaps.

**Q: Can I use Socrates for non-software projects?**
A: Yes! The framework applies to any complex requirements gathering (systems, processes, products).

**Q: How long does a specification session take?**
A: 20-45 minutes depending on complexity. No need to rush.

**Q: Can team members see my projects?**
A: Only team members you explicitly invite. Privacy is built in.

See [FAQ](docs/user/FAQ.md) for more questions.

---

## 👥 Support

- **Documentation:** [View Complete Docs](docs/INDEX.md)
- **Troubleshooting:** [Troubleshooting Guide](docs/operations/TROUBLESHOOTING.md)
- **GitHub Issues:** [Report Issues](https://github.com/Nireus79/Socrates/issues)
- **Email:** contact@socrates.app

---

## 🎯 Version

**Current Version:** 0.2.0 (Production Ready)
**Status:** ✅ Phase 1 Complete - Foundation Ready
**Last Updated:** November 11, 2025

---

## 🙏 Acknowledgments

- **Claude API** by Anthropic - AI powering intelligent questions
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Reliable database
- **Open Source Community** - Standing on shoulders of giants

---

**[→ Start with Getting Started Guide](docs/user/GETTING_STARTED.md)**

**[→ View Full Documentation](docs/INDEX.md)**
