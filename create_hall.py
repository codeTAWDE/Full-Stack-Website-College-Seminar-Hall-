from run import app
from app.extensions import db
from app.models.hall import SeminarHall

with app.app_context():
    hall = SeminarHall.query.filter_by(code="SH-001").first()

    if hall:
        hall.name = "Main Seminar Hall"
        hall.location = "Main Building"
        hall.capacity = 250
        hall.description = "Main seminar hall for meetings, seminars, and presentations."
        hall.is_active = True
        print("Existing hall updated.")
    else:
        hall = SeminarHall(
            name="Main Seminar Hall",
            code="SH-001",
            location="Main Building",
            capacity=250,
            description="Main seminar hall for meetings, seminars, and presentations.",
            is_active=True
        )
        db.session.add(hall)
        print("New hall created.")

    db.session.commit()
    print("Hall:", hall.name)
    print("Code:", hall.code)
    print("Capacity:", hall.capacity)
    print("Active:", hall.is_active)
