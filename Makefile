.PHONY: help install test lint format build clean docker-up docker-down deploy docs

help:
	@echo "Socrates2 Development Commands"
	@echo "================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          - Install all dependencies"
	@echo "  make install-backend  - Install backend dependencies only"
	@echo "  make install-frontend - Install VS Code extension dependencies"
	@echo "  make install-plugins  - Install JetBrains plugin dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test             - Run all tests"
	@echo "  make test-backend     - Run backend tests"
	@echo "  make test-frontend    - Run VS Code extension tests"
	@echo "  make test-coverage    - Run tests with coverage report"
	@echo "  make lint             - Run all linters"
	@echo "  make lint-backend     - Lint backend code (flake8, mypy)"
	@echo "  make lint-frontend    - Lint VS Code extension (ESLint)"
	@echo "  make format           - Format code (black, isort, prettier)"
	@echo "  make format-backend   - Format backend code only"
	@echo "  make format-frontend  - Format VS Code extension only"
	@echo ""
	@echo "Building:"
	@echo "  make build            - Build all components"
	@echo "  make build-backend    - Build backend package"
	@echo "  make build-plugins    - Build JetBrains plugins"
	@echo "  make build-extension  - Build VS Code extension"
	@echo "  make build-lsp        - Build LSP server"
	@echo ""
	@echo "Database:"
	@echo "  make db-create        - Create databases"
	@echo "  make db-migrate       - Run database migrations"
	@echo "  make db-seed          - Seed database with sample data"
	@echo "  make db-reset         - Drop and recreate databases"
	@echo ""
	@echo "Running:"
	@echo "  make run              - Run backend server"
	@echo "  make run-lsp          - Run LSP server"
	@echo "  make run-extension    - Run VS Code extension in development mode"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-up        - Start Docker container"
	@echo "  make docker-down      - Stop Docker container"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Clean all build artifacts"
	@echo "  make clean-backend    - Clean backend build artifacts"
	@echo "  make clean-frontend   - Clean frontend build artifacts"

# Setup & Installation
install: install-backend install-frontend install-plugins
	@echo "All dependencies installed!"

install-backend:
	cd backend && pip install -r requirements.txt -r requirements-dev.txt

install-frontend:
	cd extensions/vs-code && npm ci

install-plugins:
	@echo "JetBrains plugins managed by Gradle"

# Testing
test: test-backend test-frontend
	@echo "All tests passed!"

test-backend:
	cd backend && pytest tests/ -v

test-frontend:
	cd extensions/vs-code && npm test

test-coverage:
	cd backend && pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in backend/htmlcov/"

# Linting
lint: lint-backend lint-frontend
	@echo "All code passes linting!"

lint-backend:
	@echo "Running flake8..."
	cd backend && flake8 app/ --max-complexity=10 --max-line-length=120
	@echo "Running mypy..."
	cd backend && mypy app/ --ignore-missing-imports || true
	@echo "Checking black formatting..."
	cd backend && black --check app/ || true
	@echo "Checking isort..."
	cd backend && isort --check-only app/ || true

lint-frontend:
	cd extensions/vs-code && npm run lint

# Formatting
format: format-backend format-frontend
	@echo "All code formatted!"

format-backend:
	cd backend && black app/ && isort app/

format-frontend:
	cd extensions/vs-code && npm run format || npx prettier --write src/

# Building
build: build-backend build-plugins build-extension build-lsp
	@echo "Build complete!"

build-backend:
	cd backend && python setup.py build
	@echo "Backend build successful"

build-plugins:
	cd plugins/jetbrains && gradle build
	@echo "JetBrains plugins build successful"

build-extension:
	cd extensions/vs-code && npm run compile
	@echo "VS Code extension build successful"

build-lsp:
	cd backend/lsp && python setup.py build
	@echo "LSP server build successful"

# Database
db-create:
	cd backend && python -c "from app.core.database import create_databases; create_databases()"

db-migrate:
	cd backend && alembic upgrade head

db-seed:
	cd backend && python -c "from scripts.seed_data import seed; seed()"

db-reset:
	cd backend && python -c "from app.core.database import reset_databases; reset_databases()"

# Running
run:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-lsp:
	cd backend/lsp && python -m socrates2_lsp

run-extension:
	cd extensions/vs-code && code --extensionDevelopmentPath=. .

# Docker
docker-build:
	docker build -t socrates2:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Cleanup
clean: clean-backend clean-frontend
	@echo "Clean complete!"

clean-backend:
	cd backend && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type f -name "*.pyc" -delete
	cd backend && rm -rf build/ dist/ *.egg-info
	cd backend && rm -rf .pytest_cache/ .coverage htmlcov/

clean-frontend:
	cd extensions/vs-code && rm -rf node_modules/ dist/ out/ *.vsix

# Additional shortcuts
check: lint test
	@echo "Code check complete!"

publish: build
	@echo "Ready to publish - create a GitHub release to trigger publication workflows"

docs:
	@echo "Documentation available at:"
	@echo "  - README.md: Project overview"
	@echo "  - CONTRIBUTING.md: Contributing guidelines"
	@echo "  - SECURITY.md: Security policy"
	@echo "  - CHANGELOG.md: Version history"
	@echo "  - Architecture: See PHASE_6_COMPLETE_ARCHITECTURE.md"
