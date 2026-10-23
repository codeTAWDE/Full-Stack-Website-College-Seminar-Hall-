from datetime import date
from sqlalchemy import and_, or_
from app.extensions import db
from app.models.hall import SeminarHall, MaintenanceRecord
from app.models.booking import BookingRequest, BookingStatus


def validate_booking_times(booking_date, start_time, end_time):
    """
    Validates logical bounds for requested times:
    - Date cannot be in the past.
    - End time must be strictly greater than start time.
    """
    if booking_date < date.today():
        return False, "Reservations cannot be booked for past dates."

    if end_time <= start_time:
        return False, "End time must be after start time."

    return True, None


def has_booking_conflict(hall_id, booking_date, start_time, end_time, exclude_booking_id=None):
    """
    Standard query-level conflict checker.
    Detects if an existing APPROVED reservation overlaps with requested time slot.
    Interval overlap formula: existing.start < new.end AND existing.end > new.start
    """
    query = BookingRequest.query.filter(
        BookingRequest.hall_id == hall_id,
        BookingRequest.booking_date == booking_date,
        BookingRequest.status == BookingStatus.APPROVED,
        BookingRequest.start_time < end_time,
        BookingRequest.end_time > start_time
    )

    if exclude_booking_id:
        query = query.filter(BookingRequest.id != exclude_booking_id)

    conflicting_booking = query.first()
    return conflicting_booking is not None


def check_and_lock_hall_for_approval(booking_id):
    """
    MySQL InnoDB Concurrency-Safe Approval Validator:
    Executes a SELECT ... FOR UPDATE query on the target hall and its bookings.
    This establishes an exclusive row lock in MySQL, preventing race conditions
    where two managers approve conflicting slots concurrently.
    
    Returns:
        (is_safe, error_message, booking_object)
    """
    # Fetch booking instance
    booking = BookingRequest.query.filter_by(id=booking_id).first()
    if not booking:
        return False, "Booking request not found.", None

    # 1. Check if hall is active
    hall = SeminarHall.query.filter_by(id=booking.hall_id).with_for_update().first()
    if not hall or not hall.is_active:
        return False, "Seminar hall is currently inactive or decommissioned.", booking

    # 2. Check scheduled maintenance
    maintenance = MaintenanceRecord.query.filter(
        MaintenanceRecord.hall_id == hall.id,
        MaintenanceRecord.start_date <= booking.booking_date,
        MaintenanceRecord.end_date >= booking.booking_date,
        MaintenanceRecord.status != 'COMPLETED'
    ).first()
    if maintenance:
        return False, f"Hall is closed for maintenance ({maintenance.reason}).", booking

    # 3. Check overlapping approved bookings under row lock
    conflict = BookingRequest.query.filter(
        BookingRequest.hall_id == booking.hall_id,
        BookingRequest.booking_date == booking.booking_date,
        BookingRequest.status == BookingStatus.APPROVED,
        BookingRequest.id != booking.id,
        BookingRequest.start_time < booking.end_time,
        BookingRequest.end_time > booking.start_time
    ).with_for_update().first()

    if conflict:
        return False, f"Conflicting booking already approved ({conflict.booking_reference}: {conflict.event_title}).", booking

    return True, None, booking