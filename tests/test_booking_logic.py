from datetime import date, time, timedelta
from app.extensions import db
from app.models.booking import BookingRequest, BookingStatus
from app.utils.validators import validate_booking_times, has_booking_conflict


def test_booking_time_validation():
    """Verify boundary checks for reservation times."""
    tomorrow = date.today() + timedelta(days=1)
    yesterday = date.today() - timedelta(days=1)

    # 1. Past date must fail
    is_valid, err = validate_booking_times(yesterday, time(10, 0), time(12, 0))
    assert not is_valid
    assert "past dates" in err

    # 2. End time before start time must fail
    is_valid, err = validate_booking_times(tomorrow, time(14, 0), time(12, 0))
    assert not is_valid
    assert "after start time" in err

    # 3. Identical start and end time must fail
    is_valid, err = validate_booking_times(tomorrow, time(10, 0), time(10, 0))
    assert not is_valid

    # 4. Valid future window must succeed
    is_valid, err = validate_booking_times(tomorrow, time(10, 0), time(12, 0))
    assert is_valid
    assert err is None


def test_double_booking_conflict_detection(app, sample_hall, faculty_user):
    """Verify mathematical detection of overlapping approved bookings."""
    test_date = date.today() + timedelta(days=5)

    with app.app_context():
        # Create an APPROVED reservation from 10:00 to 12:00
        approved_booking = BookingRequest(
            hall_id=sample_hall.id,
            user_id=faculty_user.id,
            event_title="Existing Lecture",
            attendees_count=50,
            booking_date=test_date,
            start_time=time(10, 0),
            end_time=time(12, 0),
            status=BookingStatus.APPROVED
        )
        db.session.add(approved_booking)
        db.session.commit()

        # Case 1: Exact identical slot (10:00 - 12:00) -> MUST CONFLICT
        assert has_booking_conflict(sample_hall.id, test_date, time(10, 0), time(12, 0))

        # Case 2: Starts during existing (11:00 - 13:00) -> MUST CONFLICT
        assert has_booking_conflict(sample_hall.id, test_date, time(11, 0), time(13, 0))

        # Case 3: Ends during existing (09:00 - 11:00) -> MUST CONFLICT
        assert has_booking_conflict(sample_hall.id, test_date, time(9, 0), time(11, 0))

        # Case 4: Engulfs existing (09:00 - 13:00) -> MUST CONFLICT
        assert has_booking_conflict(sample_hall.id, test_date, time(9, 0), time(13, 0))

        # Case 5: Adjacent earlier slot (08:00 - 10:00) -> NO CONFLICT
        assert not has_booking_conflict(sample_hall.id, test_date, time(8, 0), time(10, 0))

        # Case 6: Adjacent later slot (12:00 - 14:00) -> NO CONFLICT
        assert not has_booking_conflict(sample_hall.id, test_date, time(12, 0), time(14, 0))

        # Case 7: Different date (same time) -> NO CONFLICT
        different_date = test_date + timedelta(days=1)
        assert not has_booking_conflict(sample_hall.id, different_date, time(10, 0), time(12, 0))


def test_cancelled_or_rejected_bookings_do_not_block_slots(app, sample_hall, faculty_user):
    """Ensure cancelled or rejected bookings do not block new reservations."""
    test_date = date.today() + timedelta(days=7)

    with app.app_context():
        # Rejected booking
        rejected = BookingRequest(
            hall_id=sample_hall.id,
            user_id=faculty_user.id,
            event_title="Rejected Event",
            attendees_count=40,
            booking_date=test_date,
            start_time=time(14, 0),
            end_time=time(16, 0),
            status=BookingStatus.REJECTED
        )
        db.session.add(rejected)
        db.session.commit()

        # Same slot should NOT conflict because the status is REJECTED
        assert not has_booking_conflict(sample_hall.id, test_date, time(14, 0), time(16, 0))