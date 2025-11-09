#!/usr/bin/env python
"""Audit migrations for _should_run() pattern and identify which database each targets"""

from pathlib import Path
import re

VERSIONS_DIR = Path("../../backend/alembic/versions")

# Manually map migrations to their target database
MIGRATION_TARGETS = {
    "001_create_users_table.py": "auth",
    "002_create_refresh_tokens_table.py": "auth",
    "003_create_projects_table.py": "specs",
    "004_create_sessions_table.py": "specs",
    "005_create_questions_table.py": "specs",
    "006_create_specifications_table.py": "specs",
    "007_create_conversation_history_table.py": "specs",
    "008_create_conflicts_table.py": "specs",
    "009_create_generated_projects_table.py": "specs",
    "010_create_generated_files_table.py": "specs",
    "011_create_quality_metrics_table.py": "specs",
    "012_create_user_behavior_patterns_table.py": "specs",
    "013_create_question_effectiveness_table.py": "specs",
    "014_create_knowledge_base_documents_table.py": "specs",
    "015_create_teams_table.py": "specs",
    "016_create_team_members_table.py": "specs",
    "017_create_project_shares_table.py": "specs",
    "018_create_api_keys_table.py": "specs",
    "019_create_llm_usage_tracking_table.py": "specs",
    "020_add_user_identity_fields.py": "auth",
    "021_add_project_ownership.py": "specs",
}

def has_should_run(file_path):
    """Check if migration file has _should_run() function"""
    content = file_path.read_text()
    return "_should_run" in content and "def _should_run" in content

def get_target_db(file_path):
    """Extract target database from _should_run() if present"""
    content = file_path.read_text()

    # Check for _should_run() function
    if "_should_run" in content:
        # Look in the function specifically
        if "def _should_run" in content:
            # Extract the function and check which DB it checks
            if 'return "socrates_auth" in db_url' in content or "'socrates_auth' in db_url" in content:
                return "auth"
            elif 'return "socrates_specs" in db_url' in content or "'socrates_specs' in db_url" in content:
                return "specs"

    return None

def main():
    """Audit migrations"""
    print("Auditing migrations...\n")

    missing_check = []
    has_check = []

    for file_path in sorted(VERSIONS_DIR.glob("*.py")):
        if file_path.name == "__init__.py":
            continue

        has_check_result = has_should_run(file_path)
        expected_db = MIGRATION_TARGETS.get(file_path.name)
        actual_db = get_target_db(file_path)

        if has_check_result:
            has_check.append((file_path.name, actual_db))
            print(f"[OK] {file_path.name}: {actual_db}")
        else:
            missing_check.append((file_path.name, expected_db))
            print(f"[XX] {file_path.name}: MISSING _should_run() - should target {expected_db}")

    print(f"\n\nSummary:")
    print(f"  With _should_run():    {len(has_check)}")
    print(f"  Missing _should_run(): {len(missing_check)}")

    if missing_check:
        print(f"\nMigrations needing fixes:")
        for name, target_db in missing_check:
            print(f"  - {name} (should target: {target_db})")

if __name__ == "__main__":
    main()
