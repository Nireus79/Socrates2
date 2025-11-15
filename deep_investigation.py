#!/usr/bin/env python3
"""
DEEP SYSTEM INVESTIGATION
Maps: schemas, tables, migrations, endpoints, models, interconnections
Identifies inconsistencies and creates repair plan
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

print("\n" + "="*100)
print("DEEP SYSTEM INVESTIGATION - SCHEMAS, MIGRATIONS, ENDPOINTS, MODELS")
print("="*100)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============================================================================
# SECTION 1: MIGRATION ANALYSIS
# ============================================================================
print("\n" + "="*100)
print("SECTION 1: DATABASE MIGRATIONS ANALYSIS")
print("="*100)

migration_dirs = {
    'specs': r'C:\Users\themi\PycharmProjects\Socrates\backend\alembic\versions',
}

all_migrations = {}

for db_type, migration_path in migration_dirs.items():
    print(f"\nChecking {db_type} migrations in: {migration_path}")

    if os.path.exists(migration_path):
        migrations = sorted([f for f in os.listdir(migration_path) if f.endswith('.py')])
        all_migrations[db_type] = migrations

        print(f"  Found {len(migrations)} migration files:")
        for mig in migrations:
            print(f"    - {mig}")
    else:
        print(f"  PATH DOES NOT EXIST: {migration_path}")

# ============================================================================
# SECTION 2: DATABASE SCHEMA ANALYSIS (from code)
# ============================================================================
print("\n" + "="*100)
print("SECTION 2: DATABASE MODELS AND SCHEMAS")
print("="*100)

models_path = r'C:\Users\themi\PycharmProjects\Socrates\backend\app\models'
print(f"\nScanning models directory: {models_path}\n")

if os.path.exists(models_path):
    model_files = [f for f in os.listdir(models_path) if f.endswith('.py')]

    print(f"Found {len(model_files)} model files:")

    models_by_category = {
        'Core': [],
        'Auth': [],
        'Content': [],
        'Analytics': [],
        'Collaboration': [],
        'Billing': [],
        'Other': []
    }

    for model_file in model_files:
        if 'auth' in model_file or 'user' in model_file:
            models_by_category['Auth'].append(model_file)
        elif 'project' in model_file or 'session' in model_file or 'specification' in model_file:
            models_by_category['Core'].append(model_file)
        elif 'conversation' in model_file or 'conflict' in model_file:
            models_by_category['Content'].append(model_file)
        elif 'analytics' in model_file or 'metric' in model_file:
            models_by_category['Analytics'].append(model_file)
        elif 'team' in model_file or 'collaboration' in model_file:
            models_by_category['Collaboration'].append(model_file)
        elif 'billing' in model_file or 'subscription' in model_file:
            models_by_category['Billing'].append(model_file)
        else:
            models_by_category['Other'].append(model_file)

    for category, files in models_by_category.items():
        if files:
            print(f"\n  {category}:")
            for f in files:
                print(f"    - {f}")

# ============================================================================
# SECTION 3: ENDPOINT ANALYSIS
# ============================================================================
print("\n" + "="*100)
print("SECTION 3: API ENDPOINTS ANALYSIS")
print("="*100)

api_path = r'C:\Users\themi\PycharmProjects\Socrates\backend\app\api'
print(f"\nScanning API directory: {api_path}\n")

endpoint_pattern = re.compile(r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']')
endpoints_by_file = {}

if os.path.exists(api_path):
    api_files = [f for f in os.listdir(api_path) if f.endswith('.py')]

    print(f"Found {len(api_files)} API endpoint files\n")
    print("Extracting registered endpoints:\n")

    for api_file in sorted(api_files):
        file_path = os.path.join(api_path, api_file)
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            matches = endpoint_pattern.findall(content)

            if matches:
                endpoints_by_file[api_file] = matches
                print(f"  {api_file}:")
                for method, path in matches:
                    print(f"    {method.upper():6} {path}")
                print()
        except Exception as e:
            print(f"  ERROR reading {api_file}: {e}")

# ============================================================================
# SECTION 4: MAIN APPLICATION SETUP
# ============================================================================
print("\n" + "="*100)
print("SECTION 4: MAIN APPLICATION SETUP (main.py)")
print("="*100)

main_path = r'C:\Users\themi\PycharmProjects\Socrates\backend\app\main.py'

if os.path.exists(main_path):
    with open(main_path, 'r') as f:
        main_content = f.read()

    # Find router includes
    router_pattern = re.compile(r'app\.include_router\(([^,]+),\s*prefix=["\']([^"\']+)["\']')
    routers = router_pattern.findall(main_content)

    print(f"\nRegistered routers in main.py:")
    for router, prefix in routers:
        print(f"  {router:40} -> prefix: {prefix}")
else:
    print(f"  main.py not found at {main_path}")

# ============================================================================
# SECTION 5: SESSIONS ENDPOINT - DETAILED ANALYSIS
# ============================================================================
print("\n" + "="*100)
print("SECTION 5: SESSIONS API - DETAILED ANALYSIS")
print("="*100)

sessions_path = r'C:\Users\themi\PycharmProjects\Socrates\backend\app\api\sessions.py'

if os.path.exists(sessions_path):
    with open(sessions_path, 'r') as f:
        sessions_content = f.read()

    # Extract all endpoint definitions
    print("\nAll endpoints in sessions.py:")

    session_endpoints = endpoint_pattern.findall(sessions_content)

    if session_endpoints:
        for method, path in session_endpoints:
            print(f"  {method.upper():6} {path}")
    else:
        print("  No endpoints found!")

    # Check for specific functions that should exist
    print("\nFunction definitions in sessions.py:")

    func_pattern = re.compile(r'def\s+(\w+)\s*\(')
    functions = func_pattern.findall(sessions_content)

    # Filter to relevant functions
    relevant_funcs = [f for f in functions if any(x in f.lower() for x in
        ['question', 'answer', 'mode', 'chat', 'session', 'history', 'switch', 'next'])]

    for func in relevant_funcs[:20]:
        print(f"  - {func}()")
else:
    print(f"  sessions.py not found at {sessions_path}")

# ============================================================================
# SECTION 6: MODELS STRUCTURE
# ============================================================================
print("\n" + "="*100)
print("SECTION 6: CORE MODELS STRUCTURE")
print("="*100)

model_files_to_check = [
    ('Session', r'C:\Users\themi\PycharmProjects\Socrates\backend\app\models\session.py'),
    ('Project', r'C:\Users\themi\PycharmProjects\Socrates\backend\app\models\project.py'),
    ('Specification', r'C:\Users\themi\PycharmProjects\Socrates\backend\app\models\specification.py'),
    ('ConversationHistory', r'C:\Users\themi\PycharmProjects\Socrates\backend\app\models\conversation_history.py'),
]

for model_name, model_path in model_files_to_check:
    print(f"\n{model_name} Model:")

    if os.path.exists(model_path):
        with open(model_path, 'r') as f:
            content = f.read()

        # Find class definition
        class_pattern = re.compile(r'class\s+(\w+)\(.*?\):')
        classes = class_pattern.findall(content)

        if classes:
            print(f"  Classes: {', '.join(classes)}")

        # Find Column definitions
        column_pattern = re.compile(r'(\w+)\s*=\s*Column\(')
        columns = column_pattern.findall(content)

        if columns:
            print(f"  Columns: {', '.join(columns[:10])}")
            if len(columns) > 10:
                print(f"    ... and {len(columns) - 10} more")
    else:
        print(f"  NOT FOUND: {model_path}")

# ============================================================================
# SECTION 7: MISSING ENDPOINTS ANALYSIS
# ============================================================================
print("\n" + "="*100)
print("SECTION 7: EXPECTED VS ACTUAL ENDPOINTS")
print("="*100)

# Expected endpoints from failing tests
expected_endpoints = {
    'Socratic Questions': [
        ('GET', '/api/v1/sessions/{id}/next-question'),
        ('GET', '/api/v1/sessions/{id}/question'),
    ],
    'Mode Switching': [
        ('PUT', '/api/v1/sessions/{id}/mode'),
        ('PUT', '/api/v1/sessions/{id}/switch-mode'),
        ('GET', '/api/v1/sessions/{id}/mode'),
    ],
    'Answer Submission': [
        ('POST', '/api/v1/sessions/{id}/answer'),
        ('POST', '/api/v1/sessions/{id}/submit-answer'),
    ],
    'Chat': [
        ('POST', '/api/v1/sessions/{id}/chat'),
        ('POST', '/api/v1/sessions/{id}/message'),
    ],
    'History': [
        ('GET', '/api/v1/sessions/{id}/history'),
        ('GET', '/api/v1/sessions/{id}/context'),
        ('GET', '/api/v1/sessions/{id}/messages'),
    ],
    'LLM Management': [
        ('GET', '/api/v1/llm/providers'),
        ('POST', '/api/v1/projects/{id}/llm'),
        ('GET', '/api/v1/projects/{id}/llm'),
    ],
    'Export': [
        ('POST', '/api/v1/projects/{id}/export'),
    ],
    'Conflicts': [
        ('GET', '/api/v1/projects/{id}/conflicts'),
        ('POST', '/api/v1/projects/{id}/conflicts/detect'),
    ],
    'Quality': [
        ('POST', '/api/v1/quality/analyze-question'),
        ('GET', '/api/v1/projects/{id}/quality'),
    ],
    'Project Management': [
        ('PUT', '/api/v1/projects/{id}/archive'),
        ('GET', '/api/v1/projects/{id}/stats'),
    ],
    'Session Management': [
        ('DELETE', '/api/v1/sessions/{id}'),
    ],
}

# Flatten all registered endpoints
all_registered = []
for file, endpoints in endpoints_by_file.items():
    for method, path in endpoints:
        # Normalize paths
        normalized_path = path.replace('{session_id}', '{id}').replace('{project_id}', '{id}')
        all_registered.append((method.upper(), normalized_path))

print("\nEndpoint Coverage Analysis:\n")

total_expected = 0
total_found = 0

for category, endpoints in expected_endpoints.items():
    found = 0
    missing = []

    for method, path in endpoints:
        total_expected += 1
        # Check if this endpoint is registered
        if any(method == reg_method and path in reg_path for reg_method, reg_path in all_registered):
            found += 1
            total_found += 1
        else:
            missing.append(f"{method} {path}")

    print(f"{category}:")
    print(f"  Expected: {len(endpoints)}, Found: {found}")
    if missing:
        for m in missing:
            print(f"    MISSING: {m}")
    print()

print(f"\nOVERALL: {total_found}/{total_expected} expected endpoints are registered ({100*total_found//total_expected}%)")

# ============================================================================
# SECTION 8: CONFIGURATION ANALYSIS
# ============================================================================
print("\n" + "="*100)
print("SECTION 8: DATABASE CONFIGURATION")
print("="*100)

config_path = r'C:\Users\themi\PycharmProjects\Socrates\backend\app\core\config.py'

if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config_content = f.read()

    # Find database URLs
    db_pattern = re.compile(r'(DATABASE_URL[A-Z_]*)\s*=\s*(.+?)(?:\n|$)')
    db_configs = db_pattern.findall(config_content)

    print("\nDatabase Configuration:")
    for var, value in db_configs[:10]:
        # Mask sensitive info
        masked = re.sub(r'password[^@]*@', 'password:***@', str(value))
        print(f"  {var}: {masked}")
else:
    print(f"  config.py not found at {config_path}")

# ============================================================================
# SECTION 9: CONSISTENCY REPORT
# ============================================================================
print("\n" + "="*100)
print("SECTION 9: CONSISTENCY REPORT")
print("="*100)

issues = []

# Check 1: Models vs Migrations
print("\n1. MODELS vs MIGRATIONS Consistency:")
print("   - Need to verify model definitions match migration tables")

# Check 2: Endpoints vs Requirements
print("\n2. ENDPOINTS vs REQUIREMENTS:")
missing_critical = sum(1 for endpoints in expected_endpoints.values()
                      for _ in endpoints
                      if not any('next-question' in str(_) and 'GET' in str(_)))
print(f"   - {total_expected - total_found} endpoints missing from {total_expected} expected")
print(f"   - {100 - (100*total_found//total_expected)}% missing")

# Check 3: Schema vs Code
print("\n3. SCHEMA CONSISTENCY:")
print("   - Need to check if database tables match ORM models")

print("\n" + "="*100)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100 + "\n")
