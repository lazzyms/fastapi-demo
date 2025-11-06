#!/usr/bin/env python3
"""
Database seeding script for FastAPI Demo.

This script seeds the database with sample data.
It is idempotent - safe to run multiple times.
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.crud import user as crud_user
from app.schemas.user import UserCreate


def seed_database():
    """Seed the database with sample data."""
    db: Session = SessionLocal()

    try:
        print("🌱 Seeding database with sample data...")
        print("")

        # Sample users to create
        sample_users = [
            {
                "email": "demo@fastapi-demo.com",
                "username": "demo",
                "full_name": "Demo User",
            },
            {
                "email": "alice@fastapi-demo.com",
                "username": "alice",
                "full_name": "Alice Johnson",
            },
            {
                "email": "bob@fastapi-demo.com",
                "username": "bob",
                "full_name": "Bob Smith",
            },
        ]

        created_count = 0
        skipped_count = 0

        for user_data in sample_users:
            # Check if user already exists (by email or username)
            existing_user = crud_user.get_user_by_email(db, user_data["email"])
            if existing_user:
                print(f"⏭️  User '{user_data['username']}' already exists, skipping...")
                skipped_count += 1
                continue

            existing_user = crud_user.get_user_by_username(db, user_data["username"])
            if existing_user:
                print(f"⏭️  User '{user_data['username']}' already exists, skipping...")
                skipped_count += 1
                continue

            # Create the user
            user_create = UserCreate(**user_data)
            new_user = crud_user.create_user(db, user_create)
            print(f"✓ Created user: {new_user.username} ({new_user.email})")
            created_count += 1

        print("")
        print("=" * 50)
        print(f"✅ Seeding complete!")
        print(f"   • Created: {created_count} user(s)")
        print(f"   • Skipped: {skipped_count} user(s) (already exist)")

        # Show total user count
        total_users = len(crud_user.get_users(db))
        print(f"   • Total users in database: {total_users}")
        print("=" * 50)

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        return False
    finally:
        db.close()

    return True


if __name__ == "__main__":
    import sys

    # Ensure database tables exist
    try:
        engine.connect()
    except Exception as e:
        print(f"❌ Error: Could not connect to database: {e}")
        print("Please run 'bash setup.sh' first to initialize the database.")
        sys.exit(1)

    # Run seeding
    success = seed_database()
    sys.exit(0 if success else 1)
