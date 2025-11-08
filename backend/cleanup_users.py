#!/usr/bin/env python
"""Clean up test users from the database."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Create engine directly with raw SQL
db_url = os.getenv('DATABASE_URL_AUTH')
engine = create_engine(db_url)

# Get the most recent users (test users)
with engine.connect() as conn:
    # Get all users
    result = conn.execute(text("SELECT id, email FROM users ORDER BY created_at DESC;"))
    users = result.fetchall()

    print(f"\nUsers in database: {len(users)}")
    print("="*60)
    for i, (user_id, email) in enumerate(users, 1):
        print(f"{i}. ID: {user_id}, Email: {email}")

    if users:
        # Delete the most recent user (last one created)
        last_user_id = users[0][0]
        last_user_email = users[0][1]

        print("\n" + "="*60)
        print(f"\nDeleting most recent user:")
        print(f"  ID: {last_user_id}")
        print(f"  Email: {last_user_email}")

        # Delete from refresh_tokens first (foreign key)
        conn.execute(text("DELETE FROM refresh_tokens WHERE user_id = :user_id"), {"user_id": str(last_user_id)})

        # Then delete the user
        conn.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": str(last_user_id)})

        conn.commit()
        print("\n[OK] User deleted successfully!")
    else:
        print("\nNo users to delete.")

engine.dispose()
