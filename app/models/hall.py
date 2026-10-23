from datetime import datetime
from app.extensions import db


class SeminarHall(db.Model):
    """Seminar hall entity."""
    __tablename__ = 'seminar_halls'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    location = db.Column(db.String(150), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    equipment = db.relationship('Equipment', backref='hall', lazy='dynamic', cascade='all, delete-orphan')
    maintenance_records = db.relationship('MaintenanceRecord', backref='hall', lazy='dynamic', cascade='all, delete-orphan')
    bookings = db.relationship('BookingRequest', backref='hall', lazy='dynamic', cascade='all, delete-orphan')

    def is_under_maintenance(self, target_date):
        """Checks if the hall has active maintenance scheduled on a specific date."""
        record = MaintenanceRecord.query.filter(
            MaintenanceRecord.hall_id == self.id,
            MaintenanceRecord.start_date <= target_date,
            MaintenanceRecord.end_date >= target_date,
            MaintenanceRecord.status != 'COMPLETED'
        ).first()
        return record is not None

    def __repr__(self):
        return f"<SeminarHall {self.code}: {self.name} (Cap: {self.capacity})>"


class Equipment(db.Model):
    """Per-hall equipment and AV resources."""
    __tablename__ = 'hall_equipment'

    id = db.Column(db.Integer, primary_key=True)
    hall_id = db.Column(db.Integer, db.ForeignKey('seminar_halls.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.String(50), default='Operational', nullable=False)  # Operational, Under Repair, Faulty

    def __repr__(self):
        return f"<Equipment {self.name} x{self.quantity} for Hall {self.hall_id}>"


class MaintenanceRecord(db.Model):
    """Maintenance events and closures."""
    __tablename__ = 'maintenance_records'

    id = db.Column(db.Integer, primary_key=True)
    hall_id = db.Column(db.Integer, db.ForeignKey('seminar_halls.id', ondelete='CASCADE'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), default='SCHEDULED', nullable=False)  # SCHEDULED, IN_PROGRESS, COMPLETED
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Maintenance Hall {self.hall_id} from {self.start_date} to {self.end_date}>"