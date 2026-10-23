from getpass import getpass
from run import app
from app.extensions import db
from app.models.user import User, Role
import sys

with app.app_context():
    name = input("Enter your full name: ").strip()
    email = input("Choose your administrator email: ").strip().lower()

    if not name or "@" not in email:
        print("Invalid name or email. Please try again.")
        sys.exit(1)

    if User.query.filter_by(email=email).first():
        print("An account with this email already exists.")
        sys.exit(1)

    password = input("Create a strong password (at least 12 characters): ")
    confirm = input("Confirm password: ")

    if len(password) < 12 or password != confirm:
        print("Passwords must match and contain at least 12 characters.")
        sys.exit(1)

    user = User(
        name=name,
        email=email,
        role=Role.ADMIN,
        is_active=True
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
        print("\nAdministrator account created successfully!")
        print("Email:", user.email)
        print("Role:", user.role)
        print("Keep your password private.")
    except Exception:
        db.session.rollback()
        raise
