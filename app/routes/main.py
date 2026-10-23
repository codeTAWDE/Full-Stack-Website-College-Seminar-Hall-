from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import current_user, login_required
from app.models.hall import SeminarHall
from app.models.booking import BookingRequest, BookingStatus
from app.models.notification import Notification
from app.extensions import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Main landing page with institutional overview and hall highlights."""
    halls = SeminarHall.query.filter_by(is_active=True).all()
    # Fetch recent approved events for public display
    upcoming_events = BookingRequest.query.filter(
        BookingRequest.status == BookingStatus.APPROVED,
        BookingRequest.booking_date >= datetime.utcnow().date()
    ).order_by(BookingRequest.booking_date.asc(), BookingRequest.start_time.asc()).limit(5).all()

    return render_template('index.html', halls=halls, upcoming_events=upcoming_events)


@main_bp.route('/calendar')
def calendar_view():
    """Public calendar view displaying scheduled seminar hall sessions."""
    halls = SeminarHall.query.filter_by(is_active=True).all()
    return render_template('calendar.html', halls=halls)


@main_bp.route('/halls')
def halls_view():
    """Public directory of seminar halls, AV amenities, and seating capacity."""
    halls = SeminarHall.query.filter_by(is_active=True).all()
    return render_template('halls_catalog.html', halls=halls)


@main_bp.route('/notifications')
@login_required
def notifications():
    """View and clear in-app notifications for the logged-in user."""
    user_notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()

    # Mark unread notifications as read
    unread = [n for n in user_notifications if not n.is_read]
    if unread:
        for n in unread:
            n.is_read = True
        db.session.commit()

    return render_template('notifications.html', notifications=user_notifications)


@main_bp.route('/notifications/unread-count')
@login_required
def unread_notifications_count():
    """API endpoint for navigation badge counter."""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    return jsonify({'unread_count': count})