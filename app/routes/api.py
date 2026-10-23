from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import current_user
from app.models.booking import BookingRequest, BookingStatus
from app.models.hall import SeminarHall

api_bp = Blueprint('api', __name__)


@api_bp.route('/calendar/events')
def calendar_events():
    """
    Returns JSON array of approved bookings for FullCalendar.
    Privacy protection:
    - If unauthenticated, only the hall and generic title ('Reserved') are returned.
    - If authenticated, official event title, department, and applicant are exposed.
    """
    start_param = request.args.get('start')
    end_param = request.args.get('end')
    hall_id_param = request.args.get('hall_id', type=int)

    query = BookingRequest.query.filter_by(status=BookingStatus.APPROVED)

    # Optional hall filter
    if hall_id_param:
        query = query.filter(BookingRequest.hall_id == hall_id_param)

    # Date range filters if supplied by FullCalendar
    if start_param:
        try:
            start_date = datetime.fromisoformat(start_param[:10]).date()
            query = query.filter(BookingRequest.booking_date >= start_date)
        except ValueError:
            pass

    if end_param:
        try:
            end_date = datetime.fromisoformat(end_param[:10]).date()
            query = query.filter(BookingRequest.booking_date <= end_date)
        except ValueError:
            pass

    bookings = query.all()
    events = []

    for b in bookings:
        # Construct ISO 8601 timestamps (YYYY-MM-DDTHH:MM:SS)
        start_iso = f"{b.booking_date.isoformat()}T{b.start_time.strftime('%H:%M:%S')}"
        end_iso = f"{b.booking_date.isoformat()}T{b.end_time.strftime('%H:%M:%S')}"

        if current_user.is_authenticated:
            title = f"{b.hall.code}: {b.event_title}"
            description = b.description or ""
            organizer = b.applicant.name
            department = b.applicant.department or "General"
        else:
            title = f"{b.hall.code}: Reserved"
            description = "Institutional Event"
            organizer = "Agnel Faculty"
            department = "Academic"

        events.append({
            'id': b.id,
            'title': title,
            'start': start_iso,
            'end': end_iso,
            'allDay': False,
            'extendedProps': {
                'reference': b.booking_reference,
                'hallName': b.hall.name,
                'hallLocation': b.hall.location,
                'organizer': organizer,
                'department': department,
                'description': description,
                'attendees': b.attendees_count
            }
        })

    return jsonify(events)


@api_bp.route('/halls/<int:hall_id>/availability')
def hall_availability(hall_id):
    """Checks availability for a specific hall on a chosen date."""
    target_date_str = request.args.get('date')
    if not target_date_str:
        return jsonify({'error': 'Missing date parameter (YYYY-MM-DD)'}), 400

    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    hall = SeminarHall.query.get_or_404(hall_id)
    if not hall.is_active:
        return jsonify({'available': False, 'reason': 'Hall is currently inactive'}), 200

    if hall.is_under_maintenance(target_date):
        return jsonify({'available': False, 'reason': 'Hall is closed for maintenance'}), 200

    approved_bookings = BookingRequest.query.filter_by(
        hall_id=hall.id,
        booking_date=target_date,
        status=BookingStatus.APPROVED
    ).order_by(BookingRequest.start_time.asc()).all()

    slots = [
        {
            'start': b.start_time.strftime('%H:%M'),
            'end': b.end_time.strftime('%H:%M'),
            'reference': b.booking_reference
        }
        for b in approved_bookings
    ]

    return jsonify({
        'hall_id': hall.id,
        'hall_name': hall.name,
        'date': target_date.isoformat(),
        'reserved_slots': slots
    })