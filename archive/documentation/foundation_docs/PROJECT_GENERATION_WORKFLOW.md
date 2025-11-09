# PROJECT GENERATION WORKFLOW

**Version:** 1.0.0
**Status:** Foundation Document
**Last Updated:** November 5, 2025
**Priority:** 🔴 HIGH - Feature #9 from VISION.md

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [What is Project Generation?](#what-is-project-generation)
3. [When Does Generation Happen?](#when-does-generation-happen)
4. [Generation Pipeline](#generation-pipeline)
5. [Architecture Generation](#architecture-generation)
6. [File Structure Generation](#file-structure-generation)
7. [Code Generation](#code-generation)
8. [Configuration Generation](#configuration-generation)
9. [Documentation Generation](#documentation-generation)
10. [Quality Validation](#quality-validation)
11. [User Customization](#user-customization)
12. [Complete Workflow Example](#complete-workflow-example)

---

## OVERVIEW

**Project Generation** is Feature #9 from VISION.md: "All specifications and context feed into project generation. Backend generates architecture, file structure, code."

**Key Principle from VISION.md:**
> Better specs = better generated code. Quality of generated project depends on quality of specifications.

### What Makes Socrates2 Different

❌ **NOT a code generator that ignores context**
❌ **NOT a template system**
❌ **NOT a boilerplate generator**

✅ **Specification-driven generation** - Every generated line traces to a spec
✅ **Quality-aware generation** - Maturity ≥ 100% required for Design → Implementation
✅ **Context-aware generation** - Uses ALL conversations, decisions, conflicts resolved
✅ **Validation-first generation** - Quality Control validates before generation

---

## WHAT IS PROJECT GENERATION?

### Inputs (What Socrates2 Uses)

```
┌─────────────────────────────────────────────┐
│ INPUTS TO GENERATION                        │
├─────────────────────────────────────────────┤
│ 1. Specifications (from Discovery Phase)    │
│    - User requirements                       │
│    - Business goals                          │
│    - Constraints                             │
│    - Success criteria                        │
│                                              │
│ 2. Resolved Conflicts (from Analysis Phase) │
│    - Technology conflicts resolved           │
│    - Requirement conflicts resolved          │
│    - Timeline conflicts resolved             │
│                                              │
│ 3. Architecture (from Design Phase)         │
│    - System architecture                     │
│    - Database schema                         │
│    - API contracts                           │
│    - Technology stack                        │
│    - Compatibility test results              │
│                                              │
│ 4. Conversation History                     │
│    - All questions asked                     │
│    - All answers provided                    │
│    - All decisions made                      │
│    - Rationale for decisions                 │
│                                              │
│ 5. Maturity Metrics                         │
│    - Coverage per category                   │
│    - Overall maturity score                  │
│    - Gap analysis                            │
└─────────────────────────────────────────────┘
```

### Outputs (What Socrates2 Generates)

```
┌─────────────────────────────────────────────┐
│ OUTPUTS FROM GENERATION                     │
├─────────────────────────────────────────────┤
│ 1. Complete Project Structure               │
│    - Directory tree                          │
│    - All files and folders                   │
│                                              │
│ 2. Source Code                              │
│    - Backend implementation                  │
│    - Frontend implementation                 │
│    - Database migrations                     │
│    - API endpoints                           │
│                                              │
│ 3. Configuration Files                      │
│    - requirements.txt / package.json         │
│    - .env.example                            │
│    - Database config                         │
│    - Docker config (if requested)            │
│                                              │
│ 4. Tests                                    │
│    - Unit tests                              │
│    - Integration tests                       │
│    - Test fixtures                           │
│                                              │
│ 5. Documentation                            │
│    - README.md                               │
│    - API documentation                       │
│    - Setup instructions                      │
│    - Architecture docs                       │
│                                              │
│ 6. Traceability Report                      │
│    - Spec → Code mapping                     │
│    - Decision rationale                      │
│    - Test coverage                           │
└─────────────────────────────────────────────┘
```

---

## WHEN DOES GENERATION HAPPEN?

### Phase Gate Requirements

**From VISION.md:**

```
Phase 1: Discovery
  ↓ (Maturity ≥ 60%, all conflicts resolved)
Phase 2: Analysis
  ↓ (Maturity = 100%, all conflicts resolved)
Phase 3: Design
  ↓ (Maturity = 100%, architecture validated, compatibility confirmed)
Phase 4: Implementation ← PROJECT GENERATION HAPPENS HERE
```

### Pre-Generation Checklist

Before generation can start:

- [ ] **Maturity = 100%** across all 12 categories
- [ ] **All conflicts resolved** (no open conflicts)
- [ ] **Architecture validated** by Quality Control
- [ ] **Compatibility testing passed** (tech stack validated)
- [ ] **User approval obtained** ("Yes, generate the project")

**If any item is ❌, Quality Control BLOCKS generation.**

---

## GENERATION PIPELINE

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ GENERATION PIPELINE                                         │
└─────────────────────────────────────────────────────────────┘

Step 1: Pre-Generation Validation
┌─────────────────────────────────────────┐
│ QualityControlAgent                     │
│ - Check maturity ≥ 100%                 │
│ - Check no open conflicts               │
│ - Check architecture validated          │
│ - Check user approval                   │
└────────────┬────────────────────────────┘
             │ ✅ Pass
             ▼
Step 2: Architecture Generation
┌─────────────────────────────────────────┐
│ ArchitectureOptimizerAgent              │
│ - Generate system architecture          │
│ - Generate component relationships      │
│ - Generate data flow diagrams           │
│ - Generate deployment architecture      │
└────────────┬────────────────────────────┘
             │
             ▼
Step 3: File Structure Generation
┌─────────────────────────────────────────┐
│ ProjectGeneratorAgent                   │
│ - Generate directory structure          │
│ - Generate file manifest                │
│ - Generate import dependencies          │
└────────────┬────────────────────────────┘
             │
             ▼
Step 4: Code Generation
┌─────────────────────────────────────────┐
│ CodeGeneratorAgent                      │
│ - Generate models (database)            │
│ - Generate services (business logic)    │
│ - Generate controllers (API endpoints)  │
│ - Generate utilities                    │
│ - Generate frontend components          │
└────────────┬────────────────────────────┘
             │
             ▼
Step 5: Configuration Generation
┌─────────────────────────────────────────┐
│ ConfigGeneratorAgent                    │
│ - Generate requirements.txt             │
│ - Generate .env.example                 │
│ - Generate database config              │
│ - Generate Docker config                │
└────────────┬────────────────────────────┘
             │
             ▼
Step 6: Test Generation
┌─────────────────────────────────────────┐
│ TestGeneratorAgent                      │
│ - Generate unit tests                   │
│ - Generate integration tests            │
│ - Generate test fixtures                │
│ - Generate test config                  │
└────────────┬────────────────────────────┘
             │
             ▼
Step 7: Documentation Generation
┌─────────────────────────────────────────┐
│ DocumentationGeneratorAgent             │
│ - Generate README.md                    │
│ - Generate API docs                     │
│ - Generate setup guide                  │
│ - Generate architecture docs            │
└────────────┬────────────────────────────┘
             │
             ▼
Step 8: Post-Generation Validation
┌─────────────────────────────────────────┐
│ QualityControlAgent                     │
│ - Validate all files generated          │
│ - Validate code quality                 │
│ - Validate test coverage                │
│ - Validate traceability (spec → code)   │
└────────────┬────────────────────────────┘
             │ ✅ Pass
             ▼
Step 9: Package & Deliver
┌─────────────────────────────────────────┐
│ DeliveryAgent                           │
│ - Create project ZIP                    │
│ - Generate traceability report          │
│ - Generate setup instructions           │
│ - Provide download link                 │
└─────────────────────────────────────────┘
```

---

## ARCHITECTURE GENERATION

### What Gets Generated

```python
# System Architecture Document (Generated)
{
  "project_name": "E-commerce for Artisans",
  "architecture_pattern": "Modular Monolith",
  "components": [
    {
      "name": "AuthService",
      "type": "service",
      "responsibilities": ["User authentication", "JWT token management"],
      "dependencies": ["UserRepository", "JWTService"],
      "database_tables": ["users", "sessions"],
      "api_endpoints": ["/auth/register", "/auth/login", "/auth/refresh"]
    },
    {
      "name": "ProductService",
      "type": "service",
      "responsibilities": ["Product CRUD", "Product search", "Inventory management"],
      "dependencies": ["ProductRepository", "ImageService"],
      "database_tables": ["products", "categories", "inventory"],
      "api_endpoints": ["/products", "/products/:id", "/products/search"]
    }
    // ... more components
  ],
  "data_flow": [
    {
      "from": "Frontend",
      "to": "APIGateway",
      "protocol": "HTTPS",
      "data": "User requests"
    },
    {
      "from": "APIGateway",
      "to": "AuthService",
      "protocol": "Internal",
      "data": "Authentication requests"
    }
    // ... more flows
  ],
  "external_integrations": [
    {
      "name": "Stripe",
      "purpose": "Payment processing",
      "endpoints": ["Payment Intent API", "Webhooks"]
    },
    {
      "name": "SendGrid",
      "purpose": "Email notifications",
      "endpoints": ["Send Email API"]
    }
  ]
}
```

---

## FILE STRUCTURE GENERATION

### Generated Directory Structure

```
generated-project/
├── backend/
│   ├── src/
│   │   ├── models/                 # Database models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── order.py
│   │   │   └── payment.py
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── product_service.py
│   │   │   ├── order_service.py
│   │   │   └── payment_service.py
│   │   ├── repositories/           # Data access
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py
│   │   │   ├── product_repository.py
│   │   │   └── order_repository.py
│   │   ├── controllers/            # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── auth_controller.py
│   │   │   ├── product_controller.py
│   │   │   └── order_controller.py
│   │   ├── middleware/             # Request processing
│   │   │   ├── __init__.py
│   │   │   ├── auth_middleware.py
│   │   │   └── error_middleware.py
│   │   ├── utils/                  # Utilities
│   │   │   ├── __init__.py
│   │   │   ├── jwt_utils.py
│   │   │   └── validation.py
│   │   └── config/                 # Configuration
│   │       ├── __init__.py
│   │       ├── settings.py
│   │       └── database.py
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_product_service.py
│   │   │   └── test_order_service.py
│   │   ├── integration/
│   │   │   ├── test_auth_flow.py
│   │   │   └── test_order_flow.py
│   │   └── fixtures/
│   │       ├── test_data.json
│   │       └── conftest.py
│   ├── alembic/                    # Database migrations
│   │   ├── versions/
│   │   │   └── 001_initial_schema.py
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── RegisterForm.tsx
│   │   │   ├── products/
│   │   │   │   ├── ProductList.tsx
│   │   │   │   ├── ProductCard.tsx
│   │   │   │   └── ProductDetail.tsx
│   │   │   └── orders/
│   │   │       ├── OrderList.tsx
│   │   │       └── OrderDetail.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   └── products.ts
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useProducts.ts
│   │   ├── types/
│   │   │   ├── user.ts
│   │   │   ├── product.ts
│   │   │   └── order.ts
│   │   └── App.tsx
│   ├── tests/
│   │   └── components/
│   │       └── ProductList.test.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   └── DEPLOYMENT.md
├── .gitignore
├── README.md
└── TRACEABILITY.md               # Spec → Code mapping
```

---

## CODE GENERATION

### Model Generation Example

**Input Specification:**
```
User table needs:
- id (UUID, primary key)
- email (unique, required)
- password (hashed, required)
- name (optional)
- created_at (timestamp)
```

**Generated Code:**

```python
# backend/src/models/user.py
"""
User model.

Generated from specification: "User authentication with email/password"
Traceability: SPEC-001, SPEC-012, SPEC-034
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database.base import Base

class User(Base):
    """
    User model for authentication.

    Attributes:
        id: Unique user identifier (UUID)
        email: User email address (unique)
        password_hash: Hashed password (bcrypt)
        name: User display name (optional)
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "users"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique user identifier"
    )

    # Authentication fields
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (unique)"
    )

    password_hash = Column(
        String(255),
        nullable=False,
        comment="Hashed password (bcrypt)"
    )

    # Profile fields
    name = Column(
        String(255),
        nullable=True,
        comment="User display name"
    )

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Account creation timestamp"
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp"
    )

    def __repr__(self):
        return f"<User {self.email}>"

    def to_dict(self):
        """Convert user to dictionary (exclude password)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
```

### Service Generation Example

**Input Specification:**
```
User registration flow:
1. Validate email format
2. Check email uniqueness
3. Validate password strength (12+ chars, uppercase, lowercase, digit, special)
4. Hash password with bcrypt
5. Create user record
6. Return user object
```

**Generated Code:**

```python
# backend/src/services/auth_service.py
"""
Authentication service.

Generated from specifications:
- SPEC-001: User registration with email/password
- SPEC-012: Password strength requirements
- SPEC-034: Email validation

Traceability:
- User registration: SPEC-001 → auth_service.register_user()
- Password validation: SPEC-012 → auth_service._is_strong_password()
- Email validation: SPEC-001 → auth_service._is_valid_email()
"""

from sqlalchemy.orm import Session
from models.user import User
from passlib.context import CryptContext
import re
import logging

logger = logging.getLogger(__name__)

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Authentication service.

    Handles user registration, login, password management.
    """

    def __init__(self, db: Session):
        """
        Initialize auth service.

        Args:
            db: Database session
        """
        self.db = db

    def register_user(self, email: str, password: str, name: str = None) -> User:
        """
        Register a new user.

        Implements specification SPEC-001: User registration with email/password

        Workflow:
        1. Validate email format (SPEC-001)
        2. Check email uniqueness (SPEC-001)
        3. Validate password strength (SPEC-012)
        4. Hash password with bcrypt (SPEC-034)
        5. Create user record (SPEC-001)

        Args:
            email: User email address
            password: Plain-text password
            name: User display name (optional)

        Returns:
            User: Created user object

        Raises:
            ValueError: If validation fails
        """
        logger.info(f"Registering user: {email}")

        # Step 1: Validate email format
        if not self._is_valid_email(email):
            logger.warning(f"Invalid email format: {email}")
            raise ValueError("Invalid email format")

        # Step 2: Check email uniqueness
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            logger.warning(f"Email already registered: {email}")
            raise ValueError("Email already registered")

        # Step 3: Validate password strength
        if not self._is_strong_password(password):
            logger.warning("Password does not meet strength requirements")
            raise ValueError(
                "Password must be at least 12 characters with uppercase, "
                "lowercase, digit, and special character"
            )

        # Step 4: Hash password
        password_hash = pwd_context.hash(password)

        # Step 5: Create user
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"User registered successfully: {email}")
        return user

    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format.

        Implements specification SPEC-001: Email validation

        Args:
            email: Email address to validate

        Returns:
            bool: True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _is_strong_password(self, password: str) -> bool:
        """
        Validate password strength.

        Implements specification SPEC-012: Password strength requirements
        - Minimum 12 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character

        Args:
            password: Password to validate

        Returns:
            bool: True if strong, False otherwise
        """
        if len(password) < 12:
            return False

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        return has_upper and has_lower and has_digit and has_special
```

---

## CONFIGURATION GENERATION

### requirements.txt Generation

**Input:** Technology stack from Design phase

**Generated Output:**

```txt
# requirements.txt
# Generated by Socrates2 based on project specifications

# Web Framework (SPEC-045: FastAPI for REST API)
fastapi==0.121.0
uvicorn[standard]==0.27.0

# Database (SPEC-023: PostgreSQL 15 for data persistence)
sqlalchemy==2.0.44
alembic==1.12.0
psycopg2-binary==2.9.9

# Data Validation (SPEC-056: Pydantic for input validation)
pydantic==2.12.3

# Authentication (SPEC-001, SPEC-034: JWT authentication)
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Environment Variables (SPEC-067: .env configuration)
python-dotenv==1.0.0

# LLM Integration (SPEC-089: Claude API integration)
anthropic==0.25.0

# Testing (SPEC-078: pytest for automated testing)
pytest==7.4.0
pytest-cov==4.1.0
pytest-asyncio==0.21.1

# Code Quality (SPEC-078: Code quality tools)
black==23.12.0
flake8==7.0.0
mypy==1.8.0

# Email (SPEC-091: SendGrid for email notifications)
sendgrid==6.10.0

# Payment Processing (SPEC-092: Stripe integration)
stripe==7.8.0
```

### .env.example Generation

```bash
# .env.example
# Generated by Socrates2 based on project specifications
# Copy this file to .env and fill in your values

# ============================================
# Database Configuration (SPEC-023)
# ============================================
DATABASE_URL=postgresql://user:password@localhost:5432/ecommerce_db

# ============================================
# Authentication (SPEC-001, SPEC-034)
# ============================================
SECRET_KEY=generate-a-secret-key-here
JWT_SECRET_KEY=generate-a-jwt-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================
# External Integrations
# ============================================

# Claude API (SPEC-089)
ANTHROPIC_API_KEY=your-anthropic-api-key

# SendGrid Email (SPEC-091)
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@yourapp.com

# Stripe Payment (SPEC-092)
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# ============================================
# Application Settings
# ============================================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# ============================================
# CORS (SPEC-045)
# ============================================
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## DOCUMENTATION GENERATION

### README.md Generation

```markdown
# E-commerce Platform for Artisans

**Generated by Socrates2** on November 5, 2025

## Overview

This is an e-commerce platform designed for artisans to sell handmade products online.

**Project Specifications:**
- Total specifications: 127
- Maturity score: 100%
- Conflicts resolved: 8
- Generation date: November 5, 2025

## Features

Based on specifications collected during Discovery phase:

- **User Authentication** (SPEC-001, SPEC-012, SPEC-034)
  - Email/password registration
  - JWT token authentication
  - Password strength validation
  - Account management

- **Product Management** (SPEC-045, SPEC-056, SPEC-067)
  - Product CRUD operations
  - Product search and filtering
  - Category management
  - Image uploads

- **Order Processing** (SPEC-078, SPEC-089, SPEC-091)
  - Shopping cart
  - Checkout flow
  - Payment processing (Stripe)
  - Order tracking

- **Notifications** (SPEC-091, SPEC-092)
  - Email notifications (SendGrid)
  - Order confirmations
  - Shipping updates

## Technology Stack

Based on Design phase architecture:

**Backend:**
- Python 3.12
- FastAPI 0.121.0
- SQLAlchemy 2.0.44
- PostgreSQL 15
- Alembic (migrations)

**Frontend:**
- React 18
- TypeScript
- Vite
- TailwindCSS

**External Services:**
- Stripe (payments)
- SendGrid (emails)
- DigitalOcean Spaces (file storage)

## Setup

See [SETUP.md](docs/SETUP.md) for detailed setup instructions.

Quick start:

```bash
# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
alembic upgrade head
uvicorn src.main:app --reload

# Frontend setup
cd frontend
npm install
cp .env.example .env
# Edit .env with your API URL
npm run dev
```

## API Documentation

See [docs/API.md](docs/API.md) for complete API documentation.

Interactive API docs available at: http://localhost:8000/docs

## Testing

```bash
# Backend tests
cd backend
pytest --cov=src --cov-report=html

# Frontend tests
cd frontend
npm test
```

**Test Coverage:**
- Backend: 87% (SPEC-078 target: 80%+)
- Frontend: 78% (SPEC-078 target: 75%+)

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for architecture details.

**Architecture Pattern:** Modular Monolith (SPEC-145)
**Design Decisions:** See TRACEABILITY.md

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment guide.

**Recommended Platform:** DigitalOcean App Platform (SPEC-167)

## Traceability

Every line of code in this project traces back to a specification.

See [TRACEABILITY.md](TRACEABILITY.md) for complete spec → code mapping.

## License

MIT License

## Generated by Socrates2

This project was generated by Socrates2 based on 127 specifications
collected over 3 weeks of discovery, analysis, and design.

**Generation Statistics:**
- Files generated: 156
- Lines of code: 23,451
- Test coverage: 84%
- Generation time: 3 minutes 42 seconds
- Specification maturity: 100%

**Quality Metrics:**
- No critical issues
- No security vulnerabilities
- All tests passing
- All specifications implemented

For questions or issues, contact: [your-email]
```

---

## QUALITY VALIDATION

### Post-Generation Validation

```python
# services/generation_validator.py
"""
Post-generation validation service.

Validates generated project meets quality standards.
"""

class GenerationValidator:
    """Validates generated project quality."""

    def validate_generation(self, project_path: str, specs: list) -> dict:
        """
        Validate generated project.

        Checks:
        1. All files generated correctly
        2. Code quality standards met
        3. Test coverage ≥ target
        4. Traceability complete (every spec → code)
        5. No security vulnerabilities
        6. Dependencies installable
        7. Tests pass

        Args:
            project_path: Path to generated project
            specs: List of specifications

        Returns:
            dict with validation results
        """
        results = {
            "is_valid": False,
            "issues": [],
            "warnings": [],
            "metrics": {},
        }

        # Check 1: All files exist
        file_check = self._validate_files_exist(project_path)
        if not file_check["passed"]:
            results["issues"].extend(file_check["issues"])

        # Check 2: Code quality
        quality_check = self._validate_code_quality(project_path)
        if not quality_check["passed"]:
            results["warnings"].extend(quality_check["warnings"])

        # Check 3: Test coverage
        coverage_check = self._validate_test_coverage(project_path)
        results["metrics"]["test_coverage"] = coverage_check["coverage"]
        if coverage_check["coverage"] < 75:
            results["warnings"].append(
                f"Test coverage {coverage_check['coverage']}% below target 75%"
            )

        # Check 4: Traceability
        traceability_check = self._validate_traceability(project_path, specs)
        results["metrics"]["specs_implemented"] = traceability_check["percentage"]
        if traceability_check["percentage"] < 100:
            results["issues"].append(
                f"Only {traceability_check['percentage']}% of specs implemented"
            )

        # Check 5: Security
        security_check = self._validate_security(project_path)
        if len(security_check["vulnerabilities"]) > 0:
            results["issues"].extend(security_check["vulnerabilities"])

        # Overall validation
        results["is_valid"] = len(results["issues"]) == 0

        return results
```

---

## USER CUSTOMIZATION

### Customization Points

Users can customize generated projects:

1. **Before Generation**
   - Choose technology stack variants (e.g., PostgreSQL vs MySQL)
   - Choose architecture pattern (modular monolith vs microservices)
   - Choose deployment target (DigitalOcean, AWS, Docker)
   - Choose test framework (pytest vs unittest)

2. **During Generation**
   - Template selection (minimal, standard, full-featured)
   - Code style preferences (black, prettier)
   - Documentation level (minimal, standard, comprehensive)

3. **After Generation**
   - Manual code editing (user maintains project)
   - Re-generation (if specs change significantly)
   - Incremental generation (add new features)

---

## COMPLETE WORKFLOW EXAMPLE

### Example: E-commerce Platform Generation

**Timeline: 3 weeks total, 4 minutes generation**

#### Week 1-2: Discovery Phase
- 87 specifications collected via Socratic questioning
- 8 conflicts detected and resolved
- Maturity: 68%

#### Week 3: Analysis + Design Phase
- Gap analysis completed (maturity → 100%)
- Architecture designed (modular monolith)
- Database schema finalized (12 tables)
- API contracts defined (24 endpoints)
- Compatibility testing passed (Python 3.12, PostgreSQL 15, React 18)

#### Day 1 of Week 4: Generation

**10:00 AM: User requests generation**

```
User: "I'm ready to generate the project. Please proceed."

Socrates2: "Checking pre-generation requirements..."

✅ Maturity: 100% (12/12 categories)
✅ Conflicts: 0 open conflicts
✅ Architecture: Validated by Quality Control
✅ Compatibility: All tests passed
✅ User approval: Confirmed

Starting project generation...
```

**10:01 AM: Architecture generation (30 seconds)**
```
[1/9] Generating system architecture...
  ✅ Generated 5 core services
  ✅ Generated 12 database models
  ✅ Generated 24 API endpoints
  ✅ Generated data flow diagrams
```

**10:02 AM: File structure generation (15 seconds)**
```
[2/9] Generating project structure...
  ✅ Created 156 files
  ✅ Created 42 directories
  ✅ Generated file manifest
```

**10:02 AM: Code generation (90 seconds)**
```
[3/9] Generating source code...
  ✅ Generated 12 models (1,234 lines)
  ✅ Generated 5 services (3,456 lines)
  ✅ Generated 8 repositories (987 lines)
  ✅ Generated 12 controllers (2,345 lines)
  ✅ Generated 15 React components (4,567 lines)
  ✅ Generated utilities (678 lines)
```

**10:03 AM: Configuration generation (10 seconds)**
```
[4/9] Generating configuration files...
  ✅ Generated requirements.txt (87 specs mapped)
  ✅ Generated .env.example
  ✅ Generated docker-compose.yml
  ✅ Generated database config
```

**10:03 AM: Test generation (45 seconds)**
```
[5/9] Generating tests...
  ✅ Generated 45 unit tests (2,345 lines)
  ✅ Generated 12 integration tests (1,234 lines)
  ✅ Generated test fixtures
  ✅ Generated conftest.py
```

**10:04 AM: Documentation generation (20 seconds)**
```
[6/9] Generating documentation...
  ✅ Generated README.md
  ✅ Generated API.md (24 endpoints documented)
  ✅ Generated SETUP.md
  ✅ Generated ARCHITECTURE.md
  ✅ Generated TRACEABILITY.md (127 specs → code mapped)
```

**10:04 AM: Post-generation validation (30 seconds)**
```
[7/9] Validating generated project...
  ✅ All files exist (156/156)
  ✅ Code quality: 98/100
  ✅ Test coverage: 87%
  ✅ Traceability: 100% (127/127 specs implemented)
  ✅ Security: No vulnerabilities
  ✅ Dependencies: All installable
  ✅ Tests: All passing (57/57)
```

**10:05 AM: Packaging (10 seconds)**
```
[8/9] Packaging project...
  ✅ Created ecommerce-artisans.zip (23,451 lines)
  ✅ Generated traceability report
  ✅ Generated setup instructions
```

**10:05 AM: Delivery (5 seconds)**
```
[9/9] Delivering project...
  ✅ Project ready for download

──────────────────────────────────────────────
PROJECT GENERATION COMPLETE
──────────────────────────────────────────────

Project: E-commerce Platform for Artisans
Files: 156 files, 42 directories
Code: 23,451 lines
Tests: 57 tests, 87% coverage
Specs: 127 specifications implemented
Quality: 98/100
Time: 3 minutes 42 seconds

Download: https://socrates2.app/projects/abc123/download
Traceability: https://socrates2.app/projects/abc123/traceability
```

**User downloads project and runs setup:**

```bash
# Unzip project
unzip ecommerce-artisans.zip
cd ecommerce-artisans

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with credentials
alembic upgrade head
pytest  # All tests pass ✅
uvicorn src.main:app --reload

# Frontend setup
cd ../frontend
npm install
npm run dev

# Project running successfully! 🎉
```

---

## VERIFICATION CHECKLIST

Before implementing Project Generation:

- [ ] Generation pipeline architecture defined
- [ ] ArchitectureOptimizerAgent implemented
- [ ] ProjectGeneratorAgent implemented
- [ ] CodeGeneratorAgent implemented (LLM-based)
- [ ] ConfigGeneratorAgent implemented
- [ ] TestGeneratorAgent implemented
- [ ] DocumentationGeneratorAgent implemented
- [ ] GenerationValidator implemented
- [ ] Traceability system implemented (spec → code mapping)
- [ ] Pre-generation validation (QC gates) working
- [ ] Post-generation validation working
- [ ] User approval flow implemented
- [ ] Download/delivery mechanism implemented

---

**Document Status:** ✅ Complete
**Reviewed By:** Pending
**Approved By:** Pending
**Date:** November 5, 2025

---

*This workflow ensures Project Generation (Feature #9) produces high-quality, traceable, tested code from specifications.*
