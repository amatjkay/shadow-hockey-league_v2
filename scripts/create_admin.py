#!/usr/bin/env python
"""Script to create the first admin user.

Usage:
    python scripts/create_admin.py
    
The script will prompt for username and password.
"""

import sys
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, '.')

from app import create_app
from models import db, AdminUser


def create_admin_user() -> None:
    """Create admin user interactively."""
    print("=" * 50)
    print("Shadow Hockey League - Create Admin User")
    print("=" * 50)
    print()
    
    # Get username
    while True:
        username = input("Username (3-80 characters): ").strip()
        if len(username) < 3:
            print("❌ Username must be at least 3 characters.")
            continue
        if len(username) > 80:
            print("❌ Username must be at most 80 characters.")
            continue
        break
    
    # Get password
    while True:
        password = getpass("Password (at least 6 characters): ")
        if len(password) < 6:
            print("❌ Password must be at least 6 characters.")
            continue
        
        password_confirm = getpass("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords do not match.")
            continue
        break
    
    # Create app and database
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = db.session.query(AdminUser).filter_by(username=username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return
        
        # Create new user
        user = AdminUser(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        print()
        print("=" * 50)
        print(f"✅ Admin user '{username}' created successfully!")
        print(f"   Login at: /admin/")
        print("=" * 50)


if __name__ == "__main__":
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
