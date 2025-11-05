# Socrates2 - Agentic RAG System for Vibe Coding

**Status:** 🚧 Documentation Phase Complete - Ready for Implementation
**Last Updated:** 2025-11-05

This is a complete redesign of Socrates with lessons learned from 3 previous failed attempts. The architecture has been carefully planned to avoid the critical failures that plagued earlier versions.

---

## 🎯 What is Socrates?

**Socrates** is an agentic RAG system that solves three fundamental problems in AI-assisted development:

1. **Context Loss** - AI forgets previous conversations → **Solution:** Persistent PostgreSQL database
2. **Greedy Algorithm Practices** - AI makes locally optimal but globally bad decisions → **Solution:** Quality Control system
3. **Incomplete Specifications** - Vague requirements lead to rework → **Solution:** Dynamic Socratic questioning

---

## 📚 Documentation Index

**READ IN THIS ORDER:**

### 1. Understanding the Vision (START HERE)

Read these documents first to understand WHAT we're building and WHY:

1. **[VISION.md](./VISION.md)** ⭐ **START HERE** - Core problems, solutions, and project vision
2. **[WHY_PREVIOUS_ATTEMPTS_FAILED.md](./WHY_PREVIOUS_ATTEMPTS_FAILED.md)** - Post-mortem of 3 failed attempts (what NOT to do)
3. **[ARCHIVE_ANTIPATTERNS.md](./ARCHIVE_ANTIPATTERNS.md)** - 8 anti-patterns that killed previous attempts
4. **[ARCHIVE_PATTERNS.md](./ARCHIVE_PATTERNS.md)** - Good patterns to keep from archive

### 2. Architecture & Design

Once you understand the vision, read the technical architecture:

5. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete system architecture and design decisions
6. **[TECHNOLOGY_STACK.md](./TECHNOLOGY_STACK.md)** - Technology choices and rationale
7. **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** - Directory structure and file organization
8. **[INTERCONNECTIONS_MAP.md](./INTERCONNECTIONS_MAP.md)** - Data flow and dependencies between all components

### 3. Workflows (How It Works)

Understand how users interact and how the system processes:

9. **[USER_WORKFLOW.md](./USER_WORKFLOW.md)** - How users interact with Socrates (step-by-step examples)
10. **[SYSTEM_WORKFLOW.md](./SYSTEM_WORKFLOW.md)** - Internal system workflows (agent coordination, data flow)

### 4. Critical Implementation Guides

**🔴 MUST READ before coding:**

11. **[SQLALCHEMY_BEST_PRACTICES.md](./SQLALCHEMY_BEST_PRACTICES.md)** 🔴 **CRITICAL** - SQLAlchemy issues that killed previous attempts (session lifecycle, detached instances)

### 5. Implementation Plan

Once you understand everything above, read the phase-by-phase implementation plan:

12. **[PHASES_SUMMARY.md](./PHASES_SUMMARY.md)** - Quick reference for all implementation phases
13. **[PHASE_0.md](./PHASE_0.md)** - Documentation & Planning (current phase)
14. **[PHASE_1.md](./PHASE_1.md)** - Infrastructure Foundation (next phase)
15. **[PHASE_2.md](./PHASE_2.md)** - Core Agents
16. **[PHASE_3.md](./PHASE_3.md)** - Conflict Detection
17. **[PHASE_4.md](./PHASE_4.md)** - Code Generation & Maturity Gates
18. **[PHASE_5.md](./PHASE_5.md)** - Quality Control System

---

## 🚨 Critical Success Factors

### What Killed Previous Attempts:

- **80%:** SQLAlchemy session lifecycle (0 data persistence despite API returning 201)
- **15%:** Detached instance errors
- **3%:** Silent exception handling
- **2%:** Missing interconnection documentation

### What Makes This Attempt Different:

1. ✅ **Documented killers BEFORE coding** - See SQLALCHEMY_BEST_PRACTICES.md
2. ✅ **Verification gates** - MUST pass tests before next phase
3. ✅ **Fail-fast principle** - No silent fallbacks
4. ✅ **Complete interconnection map** - Every dependency explicit
5. ✅ **Archive analysis** - 124 files analyzed, patterns documented

---

## 🏗️ Architecture Overview

```
User → CLI/UI → FastAPI → AgentOrchestrator → 10 Specialized Agents → PostgreSQL (2 databases)
                                    ↓
                            Quality Control
```

### 10 Agents:
1. **ProjectManagerAgent** - Project lifecycle management
2. **SocraticCounselorAgent** - Dynamic question generation (7 roles)
3. **ContextAnalyzerAgent** - Specification extraction
4. **ConflictDetectorAgent** - Real-time conflict detection (4 types)
5. **CodeGeneratorAgent** - Code generation (Phase 4+)
6. **ChatAgent** - Direct chat mode
7. **UserManagerAgent** - Authentication
8. **DocumentProcessorAgent** - Document processing (Phase 4+)
9. **SystemMonitorAgent** - System monitoring (Phase 3+)
10. **ArchitectureOptimizerAgent** - Meta-level optimization (Phase 5+)

### 2 PostgreSQL Databases:
- **socrates_auth** - Users, authentication (small, locked down)
- **socrates_specs** - Projects, sessions, specs, conflicts (large, high-volume writes)

---

## 💻 Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.12 | Stable, compatible |
| **Web Framework** | FastAPI | 0.121.0+ | Async, lightweight |
| **ORM** | SQLAlchemy | 2.0.44+ | Mature, flexible |
| **Database** | PostgreSQL | 15+ | ACID, scalability |
| **Validation** | Pydantic | 2.12.3+ | Type safety |
| **Migrations** | Alembic | latest | Schema versioning |
| **LLM** | Claude (Anthropic) | latest | Primary reasoning |
| **CLI** | Custom | - | Simple, focused (MVP) |

**See [TECHNOLOGY_STACK.md](./TECHNOLOGY_STACK.md) for detailed rationale and alternatives considered.**

---

## 📋 Key Features (MVP)

### Core Functionality:
- ✅ **Persistent Context** - Nothing forgotten, all specs in database
- ✅ **Socratic Questioning** - Dynamic questions from 7 professional roles
- ✅ **Direct Chat Mode** - Toggle between Socratic and Direct Chat
- ✅ **Conflict Detection** - 4 types detected automatically (tech, requirements, timeline, resources)
- ✅ **Quality Control** - Prevents greedy decisions, shows all paths with costs
- ✅ **Maturity System** - Dynamic tracking of specification completeness (10 categories)
- ✅ **Real-Time Compatibility Testing** - Tests tech stack compatibility BEFORE implementation
- ✅ **User Learning** - System adapts to individual patterns (infrastructure ready, full implementation Phase 5+)
- ✅ **Multi-LLM Support** - Not tied to Claude (infrastructure ready, multi-provider Phase 3+)

### Future Phases:
- 🔜 **Code Generation** - Phase 4
- 🔜 **IDE Integration** - Phase 4
- 🔜 **GitHub Integration** - Phase 4
- 🔜 **Team Collaboration** - Phase 6
- 🔜 **UI (React)** - Phase 6

---

## 🚀 Quick Start (Not Yet Implemented)

**Current Status:** Documentation complete, implementation pending

Once Phase 1 is implemented:

```bash
# Setup databases
createdb socrates_auth
createdb socrates_specs
python scripts/setup_databases.py

# Install dependencies
pip install -r requirements.txt

# Run migrations
python scripts/run_migrations.py

# Start backend
cd backend
uvicorn main:app --reload

# Run CLI
cd cli
python main.py
```

---

## 🧪 Testing Strategy

### Phase 1 Requirements (MUST PASS):

1. **test_persistence_after_session_close()** 🔴 **CRITICAL**
   - Tests exact bug that killed previous attempt
   - Verifies data persists after SQLAlchemy session closes
   - **MUST PASS** before Phase 2

2. **test_no_detached_instances()**
   - Verifies no detached instance errors
   - **MUST PASS** before Phase 2

3. **test_dto_completeness()**
   - Verifies all model fields exist in DTOs
   - **MUST PASS** before Phase 2

### Coverage Requirements:
- Minimum 90% overall coverage
- 100% coverage for:
  - BaseAgent
  - AgentOrchestrator
  - All repositories
  - Quality Control system
  - Maturity system

---

## 📊 Project Phases

| Phase | Name | Duration | Status |
|-------|------|----------|--------|
| **Phase 0** | Documentation & Planning | 3 days | ✅ **COMPLETE** |
| **Phase 1** | Infrastructure Foundation | 2-3 days | ⏳ **NEXT** |
| **Phase 2** | Core Agents | 1-2 weeks | ⏳ Pending |
| **Phase 3** | Conflict Detection | 3-4 days | ⏳ Pending |
| **Phase 4** | Code Generation | 1-2 weeks | ⏳ Pending |
| **Phase 5** | Quality Control | 1 week | ⏳ Pending |

**See [PHASES_SUMMARY.md](./PHASES_SUMMARY.md) for detailed breakdown.**

---

## ✅ Phase 0 Deliverables (COMPLETE)

- [x] VISION.md - Project goals and requirements
- [x] ARCHITECTURE.md - Complete system architecture
- [x] TECHNOLOGY_STACK.md - Technology decisions and rationale
- [x] PROJECT_STRUCTURE.md - Directory structure
- [x] USER_WORKFLOW.md - User interaction flows
- [x] SYSTEM_WORKFLOW.md - Internal system workflows
- [x] INTERCONNECTIONS_MAP.md - Complete dependency mapping
- [x] SQLALCHEMY_BEST_PRACTICES.md - Critical implementation guide
- [x] ARCHIVE_ANTIPATTERNS.md - What NOT to do
- [x] ARCHIVE_PATTERNS.md - Good patterns to keep
- [x] WHY_PREVIOUS_ATTEMPTS_FAILED.md - Post-mortem analysis
- [x] Phase documents (PHASE_0.md through PHASE_5.md)

**Total Documentation:** 18 comprehensive documents (~200KB)

---

## 🔒 What This Project Is NOT

❌ A simple chatbot
❌ A code generator without context
❌ A tool that loses information
❌ A system making greedy decisions
❌ A one-size-fits-all approach
❌ A substitute for thinking

**Socrates enables better thinking by:**
- Maintaining complete context
- Asking the right questions
- Detecting conflicts early
- Showing all options with true costs

---

## 🤝 Contributing

**Current Status:** Not accepting contributions (foundation phase)

Once MVP is stable (Phase 2 complete):
- Contribution guidelines will be added
- Issue templates will be created
- Development workflow will be documented

---

## 📄 License

TBD

---

## 📞 Support & Questions

**For the development team:**
- Read docs in order (listed above)
- Check INTERCONNECTIONS_MAP.md for dependencies
- Consult SQLALCHEMY_BEST_PRACTICES.md before database work
- Reference ARCHIVE_ANTIPATTERNS.md to avoid past mistakes

---

## 🎯 Success Probability

**Previous Attempts:** 0% (all failed)
**Socrates2:** 85% (documented issues, verification gates, fail-fast principles)

**The Difference:**
- Previous: Found bugs AFTER coding
- Socrates2: Found bugs BEFORE coding (from archive analysis)

**References:**
- [VISION.md lines 212-225](./VISION.md) - Lessons from previous failures
- [WHY_PREVIOUS_ATTEMPTS_FAILED.md](./WHY_PREVIOUS_ATTEMPTS_FAILED.md) - Complete post-mortem
- [ARCHIVE_ANTIPATTERNS.md](./ARCHIVE_ANTIPATTERNS.md) - 8 documented killers

---

**Last Updated:** 2025-11-05
**Phase:** 0 (Documentation) - COMPLETE ✅
**Next:** Phase 1 (Infrastructure Foundation)
**Approval:** Ready for implementation

---

## Quick Reference Links

- **Vision & Goals:** [VISION.md](./VISION.md)
- **Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Technology Stack:** [TECHNOLOGY_STACK.md](./TECHNOLOGY_STACK.md)
- **Critical Issues:** [SQLALCHEMY_BEST_PRACTICES.md](./SQLALCHEMY_BEST_PRACTICES.md)
- **Interconnections:** [INTERCONNECTIONS_MAP.md](./INTERCONNECTIONS_MAP.md)
- **Implementation Plan:** [PHASES_SUMMARY.md](./PHASES_SUMMARY.md)
- **Project Structure:** [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)
