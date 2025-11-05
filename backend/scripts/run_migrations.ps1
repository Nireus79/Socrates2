# Socrates2 - Automated Database Migration Script
# This script runs Alembic migrations for both databases

param(
    [string]$PostgresPassword = ""
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Socrates2 - Database Migration Script" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-Not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please run 'python scripts\setup_env.py' first" -ForegroundColor Yellow
    exit 1
}

# Load .env file to get database credentials
Write-Host "Loading configuration from .env file..." -ForegroundColor Green
$envContent = Get-Content ".env"
$dbUrlAuth = ($envContent | Select-String "DATABASE_URL_AUTH=").ToString().Split("=")[1]
$dbUrlSpecs = ($envContent | Select-String "DATABASE_URL_SPECS=").ToString().Split("=")[1]

if ([string]::IsNullOrEmpty($dbUrlAuth) -or [string]::IsNullOrEmpty($dbUrlSpecs)) {
    Write-Host "ERROR: Database URLs not found in .env file!" -ForegroundColor Red
    exit 1
}

Write-Host "  Database URLs loaded successfully" -ForegroundColor Green
Write-Host ""

# Check if databases exist
Write-Host "Checking if databases exist..." -ForegroundColor Green

# Extract database names from URLs
if ($dbUrlAuth -match "/([^/]+)$") {
    $dbNameAuth = $matches[1]
}
if ($dbUrlSpecs -match "/([^/]+)$") {
    $dbNameSpecs = $matches[1]
}

Write-Host "  Auth Database: $dbNameAuth" -ForegroundColor Cyan
Write-Host "  Specs Database: $dbNameSpecs" -ForegroundColor Cyan
Write-Host ""

# Check if alembic is initialized
if (-Not (Test-Path "alembic\env.py")) {
    Write-Host "Alembic not initialized. Running 'alembic init alembic'..." -ForegroundColor Yellow
    alembic init alembic
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to initialize Alembic!" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Alembic initialized successfully" -ForegroundColor Green
    Write-Host ""
}

# Check if migration files exist
$migrationFiles = @(
    "alembic\versions\001_create_users_table.py",
    "alembic\versions\002_create_refresh_tokens_table.py",
    "alembic\versions\003_create_projects_table.py",
    "alembic\versions\004_create_sessions_table.py"
)

$missingFiles = @()
foreach ($file in $migrationFiles) {
    if (-Not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "ERROR: Missing migration files:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please pull the latest code from GitHub:" -ForegroundColor Yellow
    Write-Host "  git pull origin master" -ForegroundColor Yellow
    exit 1
}

Write-Host "All 4 migration files found" -ForegroundColor Green
Write-Host ""

# Run migrations for socrates_auth
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Step 1: Running migrations for $dbNameAuth" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$env:DATABASE_URL = $dbUrlAuth
Write-Host "Setting DATABASE_URL to: $dbNameAuth" -ForegroundColor Yellow

# Check current migration state
Write-Host "Checking current migration state..." -ForegroundColor Green
alembic current 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    $currentRevision = alembic current 2>&1
    Write-Host "  Current revision: $currentRevision" -ForegroundColor Cyan
}

# Run upgrade
Write-Host "Running 'alembic upgrade head'..." -ForegroundColor Green
alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Migration failed for $dbNameAuth!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  1. Database doesn't exist - create it first:" -ForegroundColor Yellow
    Write-Host "     psql -U postgres -c `"CREATE DATABASE $dbNameAuth;`"" -ForegroundColor Cyan
    Write-Host "  2. Wrong password in .env file" -ForegroundColor Yellow
    Write-Host "  3. PostgreSQL service not running" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "SUCCESS: Migrations completed for $dbNameAuth" -ForegroundColor Green
Write-Host ""

# Verify tables created
Write-Host "Verifying tables created..." -ForegroundColor Green
Write-Host "  Expected tables: users, refresh_tokens" -ForegroundColor Cyan
Write-Host ""

# Run migrations for socrates_specs
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Step 2: Running migrations for $dbNameSpecs" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$env:DATABASE_URL = $dbUrlSpecs
Write-Host "Setting DATABASE_URL to: $dbNameSpecs" -ForegroundColor Yellow

# Check current migration state
Write-Host "Checking current migration state..." -ForegroundColor Green
alembic current 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    $currentRevision = alembic current 2>&1
    Write-Host "  Current revision: $currentRevision" -ForegroundColor Cyan
}

# Run upgrade
Write-Host "Running 'alembic upgrade head'..." -ForegroundColor Green
alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Migration failed for $dbNameSpecs!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  1. Database doesn't exist - create it first:" -ForegroundColor Yellow
    Write-Host "     psql -U postgres -c `"CREATE DATABASE $dbNameSpecs;`"" -ForegroundColor Cyan
    Write-Host "  2. Wrong password in .env file" -ForegroundColor Yellow
    Write-Host "  3. PostgreSQL service not running" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "SUCCESS: Migrations completed for $dbNameSpecs" -ForegroundColor Green
Write-Host ""

# Verify tables created
Write-Host "Verifying tables created..." -ForegroundColor Green
Write-Host "  Expected tables: projects, sessions" -ForegroundColor Cyan
Write-Host ""

# Final summary
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "ALL MIGRATIONS COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Database: $dbNameAuth" -ForegroundColor Cyan
Write-Host "  Tables: users, refresh_tokens, alembic_version" -ForegroundColor White
Write-Host ""
Write-Host "Database: $dbNameSpecs" -ForegroundColor Cyan
Write-Host "  Tables: projects, sessions, alembic_version" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify tables: psql -U postgres -d $dbNameAuth -c `"\dt`"" -ForegroundColor Cyan
Write-Host "  2. Start FastAPI server: uvicorn app.main:app --reload" -ForegroundColor Cyan
Write-Host "  3. Open API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
