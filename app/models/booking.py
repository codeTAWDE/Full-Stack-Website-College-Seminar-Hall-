import uuid
from datetime import datetime
from app.extensions import db


class BookingStatus:
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    CANCELLED = 'CANCELLED'

    CHOICES = [
        (PENDING, 'Pending Review'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (CANCELLED, 'Cancelled')
    ]


def generate_booking_reference():
    """Generates unique alphanumeric reference code: e.g. SHMS-A1B2C3D4"""
    return f"SHMS-{uuid.uuid4().hex[:8].upper()}"


class BookingRequest(db.Model):
    """Seminar hall booking requests and states."""
    __tablename__ = 'booking_requests'

    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(20), unique=True, default=generate_booking_reference, nullable=False, index=True)
    hall_id = db.Column(db.Integer, db.ForeignKey('seminar_halls.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    event_title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    attendees_count = db.Column(db.Integer, nullable=False)

    booking_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    status = db.Column(db.String(20), default=BookingStatus.PENDING, nullable=False, index=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def is_pending(self):
        return self.status == BookingStatus.PENDING

    def is_approved(self):
        return self.status == BookingStatus.APPROVED

    def is_rejected(self):
        return self.status == BookingStatus.REJECTED

    def is_cancelled(self):
        return self.status == BookingStatus.CANCELLED

    def __repr__(self):
        return f"<Booking {self.booking_reference}: Hall {self.hall_id} on {self.booking_date} ({self.status})>"