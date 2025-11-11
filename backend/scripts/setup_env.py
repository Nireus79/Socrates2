#!/usr/bin/env python3
"""
Automatic .env file generator for Socrates
Generates secure SECRET_KEY and creates .env file with user input
"""

import secrets
import os
import sys


def generate_secret_key():
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(32)


def get_user_input(prompt, default=None):
    """Get input from user with optional default"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        user_input = input(f"{prompt}: ").strip()
        while not user_input:
            print("This field is required!")
            user_input = input(f"{prompt}: ").strip()
        return user_input


def main():
    """Main setup function"""
    print("=" * 70)
    print("Socrates - Environment Setup")
    print("=" * 70)
    print()

    # Check if .env already exists
    if os.path.exists('.env'):
        overwrite = input(".env file already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            sys.exit(0)

    print("I'll help you create the .env file.")
    print("Press Enter to use default values shown in [brackets]")
    print()

    # Generate SECRET_KEY automatically
    secret_key = generate_secret_key()
    print(f"✅ Generated SECRET_KEY: {secret_key}")
    print()

    # Get database password
    print("PostgreSQL Setup:")
    print("-" * 70)
    db_user = get_user_input("PostgreSQL username", "postgres")
    db_password = get_user_input("PostgreSQL password (the one you set during installation)")
    db_host = get_user_input("PostgreSQL host", "localhost")
    db_port = get_user_input("PostgreSQL port", "5432")
    print()

    # Get Claude API key
    print("Claude API Setup:")
    print("-" * 70)

    # Check if ANTHROPIC_API_KEY is already in environment
    existing_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if existing_key:
        print(f"✅ Found existing ANTHROPIC_API_KEY in environment")
        use_existing = input("Use existing key? (Y/n): ").strip().lower()
        if use_existing != 'n':
            anthropic_key = existing_key
        else:
            anthropic_key = get_user_input("Enter your Anthropic API key")
    else:
        anthropic_key = get_user_input("Enter your Anthropic API key (starts with sk-ant-)")
    print()

    # Application settings
    print("Application Settings:")
    print("-" * 70)
    debug = get_user_input("Enable debug mode?", "True")
    environment = get_user_input("Environment", "development")
    log_level = get_user_input("Log level", "DEBUG")
    print()

    # Build database URLs
    db_url_auth = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/socrates_auth"
    db_url_specs = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/socrates_specs"

    # Create .env content
    env_content = f"""# Socrates - Environment Variables
# Generated automatically by setup_env.py

# ===== DATABASE =====
DATABASE_URL_AUTH={db_url_auth}
DATABASE_URL_SPECS={db_url_specs}

# ===== SECURITY =====
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== LLM API KEYS =====
ANTHROPIC_API_KEY={anthropic_key}

# ===== APPLICATION =====
DEBUG={debug}
ENVIRONMENT={environment}
LOG_LEVEL={log_level}

# ===== CORS (for future UI) =====
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
"""

    # Write .env file
    with open('.env', 'w') as f:
        f.write(env_content)

    print("=" * 70)
    print("✅ .env file created successfully!")
    print("=" * 70)
    print()
    print("Configuration summary:")
    print(f"  Database Host: {db_host}:{db_port}")
    print(f"  Database User: {db_user}")
    print(f"  Auth Database: socrates_auth")
    print(f"  Specs Database: socrates_specs")
    print(f"  Environment: {environment}")
    print(f"  Debug Mode: {debug}")
    print()
    print("⚠️  IMPORTANT: Never commit .env to git!")
    print("✅ .env is already in .gitignore")
    print()
    print("Next steps:")
    print("  1. Verify databases exist: psql -U postgres -l")
    print("  2. Create databases if needed:")
    print("     psql -U postgres -c 'CREATE DATABASE socrates_auth;'")
    print("     psql -U postgres -c 'CREATE DATABASE socrates_specs;'")
    print("  3. Test connection: python -c 'from dotenv import load_dotenv; load_dotenv(); print(\"✅ OK\")'")
    print()


if __name__ == "__main__":
    main()
