"""
Agnel Polytechnic SHMS - Database Seeder
Initializes default seminar halls, equipment, and baseline accounts.
Run via: python seed.py
"""
import os
import sys
from app import create_app
from app.extensions import db
from app.models.user import User, Role
from app.models.hall import SeminarHall, Equipment

app = create_app(os.environ.get('FLASK_ENV', 'development'))


def seed_database():
    with app.app_context():
        print("Connecting to database and verifying schema...")
        db.create_all()

        # 1. Seed System Administrator
        admin_email = os.environ.get('ADMIN_INITIAL_EMAIL', 'admin@apv.ac.in')
        admin_pass = os.environ.get('ADMIN_INITIAL_PASSWORD', 'Admin@Agnel2026')
        
        existing_admin = User.query.filter_by(email=admin_email).first()
        if not existing_admin:
            admin = User(
                name="System Administrator",
                email=admin_email,
                role=Role.ADMIN,
                department="IT Administration",
                phone="+91 22 2777 1000",
                is_active=True
            )
            admin.set_password(admin_pass)
            db.session.add(admin)
            print(f" [+] Administrator account created: {admin_email} (Password: {admin_pass})")
        else:
            print(f" [i] Administrator account already exists: {admin_email}")

        # 2. Seed Principal Account
        principal_email = os.environ.get('PRINCIPAL_INITIAL_EMAIL', 'principal@apv.ac.in')
        principal_pass = os.environ.get('PRINCIPAL_INITIAL_PASSWORD', 'Principal@Agnel2026')

        existing_principal = User.query.filter_by(email=principal_email).first()
        if not existing_principal:
            principal = User(
                name="Principal Ma'am",
                email=principal_email,
                role=Role.PRINCIPAL,
                department="Executive Office",
                phone="+91 22 2777 1001",
                is_active=True
            )
            principal.set_password(principal_pass)
            db.session.add(principal)
            print(f" [+] Principal account created: {principal_email} (Password: {principal_pass})")
        else:
            print(f" [i] Principal account already exists: {principal_email}")

        # 3. Seed Sample Faculty Account
        faculty_email = 'faculty.comp@apv.ac.in'
        faculty_pass = 'Faculty@Agnel2026'

        existing_faculty = User.query.filter_by(email=faculty_email).first()
        if not existing_faculty:
            faculty = User(
                name="Prof. Rajesh Sharma",
                email=faculty_email,
                role=Role.FACULTY,
                department="Computer Engineering",
                phone="+91 98765 43210",
                is_active=True
            )
            faculty.set_password(faculty_pass)
            db.session.add(faculty)
            print(f" [+] Faculty account created: {faculty_email} (Password: {faculty_pass})")
        else:
            print(f" [i] Faculty account already exists: {faculty_email}")

        # 4. Seed Agnel Polytechnic Seminar Halls
        halls_data = [
            {
                "name": "Fr. Agnel Central Auditorium",
                "code": "AUD-01",
                "location": "Agnel Main Building, 2nd Floor",
                "capacity": 450,
                "description": "State-of-the-art auditorium with Dolby surround sound, dual projection screens, and stage lighting for annual symposiums and national seminars.",
                "equipment": [
                    ("JBL Surround Audio System", 1, "Operational"),
                    ("Epson 4K Laser Projector", 2, "Operational"),
                    ("Wireless Handheld & Collar Mics", 6, "Operational"),
                    ("Podium Laptop Interface", 1, "Operational")
                ]
            },
            {
                "name": "Polytechnic Seminar Hall 1",
                "code": "SH-101",
                "location": "Polytechnic Wing, Ground Floor",
                "capacity": 160,
                "description": "Acoustically treated conference hall tailored for department guest lectures, workshops, and project presentations.",
                "equipment": [
                    ("Full HD Projector & Motorized Screen", 1, "Operational"),
                    ("Bose Column Speakers", 2, "Operational"),
                    ("Cordless Microphones", 3, "Operational"),
                    ("Smart Whiteboard", 1, "Operational")
                ]
            },
            {
                "name": "IT & Engineering Conference Hall",
                "code": "IT-201",
                "location": "IT Block, 3rd Floor",
                "capacity": 85,
                "description": "Executive conference room equipped for hybrid video-conferencing, academic committee meetings, and faculty development programs.",
                "equipment": [
                    ("Logitech MeetUp HD Conference Cam", 1, "Operational"),
                    ("Dual 65-inch 4K Displays", 2, "Operational"),
                    ("Boundary Tabletop Microphones", 4, "Operational"),
                    ("High-Speed Dedicated LAN Switch", 1, "Operational")
                ]
            }
        ]

        for h_data in halls_data:
            existing_hall = SeminarHall.query.filter_by(code=h_data["code"]).first()
            if not existing_hall:
                hall = SeminarHall(
                    name=h_data["name"],
                    code=h_data["code"],
                    location=h_data["location"],
                    capacity=h_data["capacity"],
                    description=h_data["description"],
                    is_active=True
                )
                db.session.add(hall)
                db.session.flush()  # obtain hall.id

                for eq_name, qty, status in h_data["equipment"]:
                    eq = Equipment(
                        hall_id=hall.id,
                        name=eq_name,
                        quantity=qty,
                        status=status
                    )
                    db.session.add(eq)

                print(f" [+] Seminar Hall configured: {hall.name} ({hall.code})")
            else:
                print(f" [i] Seminar Hall already exists: {h_data['code']}")

        db.session.commit()
        print("\nDatabase seeding completed successfully! Ready for server startup.")


if __name__ == '__main__':
    seed_database()