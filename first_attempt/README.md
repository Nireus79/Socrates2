# Socrates2 - Agentic RAG System for Vibe Coding

**Status:** 🚧 Documentation Phase - Implementation Pending

This is a complete redesign of Socrates with lessons learned from 3 previous attempts. The architecture has been carefully planned to avoid the critical failures that plagued earlier versions.

---

## 📚 Documentation Index

Read these documents **in order** before starting implementation:

### 1. Understanding the System
- **[MY_UNDERSTANDING_OVERVIEW.md](https://github.com/Nireus79/Socrates/blob/main/MY_UNDERSTANDING_OVERVIEW.md)** - What Socrates is and how it works
- **[MY_UNDERSTANDING_ARCHITECTURE.md](https://github.com/Nireus79/Socrates/blob/main/MY_UNDERSTANDING_ARCHITECTURE.md)** - System architecture details
- **[MY_UNDERSTANDING_USER_WORKFLOW.md](https://github.com/Nireus79/Socrates/blob/main/MY_UNDERSTANDING_USER_WORKFLOW.md)** - User interaction workflows
- **[MY_UNDERSTANDING_SYSTEM_WORKFLOW.md](https://github.com/Nireus79/Socrates/blob/main/MY_UNDERSTANDING_SYSTEM_WORKFLOW.md)** - Internal system workflows
- **[MY_UNDERSTANDING_FEATURES.md](https://github.com/Nireus79/Socrates/blob/main/MY_UNDERSTANDING_FEATURES.md)** - Complete feature breakdown

### 2. Archive Analysis (Lessons Learned)
- **[ARCHIVE_PATTERNS.md](ARCHIVE_PATTERNS.md)** - Good patterns to follow from old repo
- **[ARCHIVE_ANTIPATTERNS.md](ARCHIVE_ANTIPATTERNS.md)** - Anti-patterns that caused failures
- **[WHY_PREVIOUS_ATTEMPTS_FAILED.md](WHY_PREVIOUS_ATTEMPTS_FAILED.md)** - Detailed post-mortem analysis
- **[SQLALCHEMY_BEST_PRACTICES.md](SQLALCHEMY_BEST_PRACTICES.md)** - 🔴 **CRITICAL** - SQLAlchemy issues that killed previous attempts (MUST READ before Phase 1)

### 3. Architecture & Design
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete system architecture with interconnections
- **[INTERCONNECTIONS_MAP.md](INTERCONNECTIONS_MAP.md)** - Data flow and dependencies between all components
- **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** - Directory layout and file organization

### 4. Implementation Plan
- **[PHASES.md](./PHASES.md)** - Detailed phase-by-phase implementation plan with verification gates
- **[TESTING_STRATEGY.md](./TESTING_STRATEGY.md)** - Testing requirements for each phase
- **[DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md)** - Complete database design

### 5. Development Guidelines
- **[DEVELOPMENT_GUIDELINES.md](./DEVELOPMENT_GUIDELINES.md)** - Coding standards and best practices
- **[VERIFICATION_CHECKLIST.md](./VERIFICATION_CHECKLIST.md)** - Checklist for each phase before proceeding

---

## 🎯 Core Concept

**Socrates** is an **agentic RAG system for "vibe coding"** that solves two fundamental AI problems:

1. **Context Loss** - AI forgets previous conversations → **Solution:** Persistent PostgreSQL database
2. **Greedy Algorithm Practices** - AI makes locally optimal but globally bad decisions → **Solution:** Quality Control system

---

## 🏗️ Architecture Overview

```
User → FastAPI → AgentOrchestrator → 10 Specialized Agents → PostgreSQL
                         ↓
                  Quality Control
```

### 10 Agents:
1. **ProjectManagerAgent** - Project lifecycle management
2. **SocraticCounselorAgent** - Question generation
3. **ContextAnalyzerAgent** - Spec extraction
4. **ConflictDetectorAgent** - Real-time conflict detection
5. **CodeGeneratorAgent** - Code generation
6. **ChatAgent** - Direct chat mode
7. **UserManagerAgent** - Authentication
8. **DocumentProcessorAgent** - Document processing
9. **SystemMonitorAgent** - System monitoring
10. **ArchitectureOptimizerAgent** - Meta-level optimization

---

## 🚨 Critical Success Factors

### ✅ DO:
- **Fail fast with clear errors** - No silent fallbacks
- **Make all dependencies REQUIRED** - Explicit dependency injection
- **Enforce verification gates** - Cannot proceed to next phase without passing tests
- **Maintain clear interconnections** - Every component knows what it depends on and provides
- **Write tests FIRST** - Before implementing feature

### ❌ DON'T:
- **No fallback_helpers.py** - This was the #1 killer of previous attempts
- **No optional dependencies** - Everything is required
- **No bypass mechanisms** - All requests go through orchestrator + quality control
- **No circular dependencies** - Strict layered architecture
- **No implementation without tests** - Tests are mandatory

---

## 📊 Project Status

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0: Documentation | ✅ IN PROGRESS | 10% |
| Phase 1: Infrastructure | ⏳ PENDING | 0% |
| Phase 2: Core Agents (3) | ⏳ PENDING | 0% |
| Phase 3: Conflict Detection | ⏳ PENDING | 0% |
| Phase 4: Code Generation | ⏳ PENDING | 0% |
| Phase 5: Quality Control | ⏳ PENDING | 0% |
| Phase 6: User Learning | ⏳ PENDING | 0% |
| Phase 7: Advanced Features | ⏳ PENDING | 0% |

---

## 🔗 Links to Old Repo (Reference Only)

- **Old Repo:** https://github.com/Nireus79/Socrates
- **Socratic7.py (Working PoC):** https://github.com/Nireus79/Socrates/blob/main/ARCHIVE/Socratic7.py
- **backend_for_audit (Failed Attempt):** https://github.com/Nireus79/Socrates/tree/main/ARCHIVE/backend_for_audit

**⚠️ WARNING:** Do NOT copy-paste code from old repo. Use as reference only. Previous attempts had fatal flaws (especially fallback_helpers.py).

---

## 🚀 Getting Started (Once Implementation Begins)

```bash
# Clone repository
git clone https://github.com/Nireus79/Socrates2.git
cd Socrates2

# Read all documentation FIRST
# Then proceed to Phase 1 implementation
```

---

## 📝 License

[Add license information]

---

## 🤝 Contributing

**Current Phase:** Documentation Review

Before contributing, please read:
1. All documentation listed above
2. DEVELOPMENT_GUIDELINES.md
3. WHY_PREVIOUS_ATTEMPTS_FAILED.md

---

**Last Updated:** 2025-11-05
