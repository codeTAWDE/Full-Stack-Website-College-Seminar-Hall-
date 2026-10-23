from getpass import getpass
from run import app
from app.extensions import db
from app.models.user import User, Role

with app.app_context():
    name = input("Faculty name: ").strip()
    email = input("Faculty email: ").strip().lower()
    password = input("Faculty password: ")

    if not name or not email or not password:
        print("Name, email, and password are required.")
    elif User.query.filter_by(email=email).first():
        print("An account with this email already exists.")
    else:
        user = User(
            name=name,
            email=email,
            role=Role.FACULTY,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("Faculty account created successfully.")
        print("Name:", user.name)
        print("Email:", user.email)
        print("Role:", user.role.value if hasattr(user.role, "value") else user.role)
