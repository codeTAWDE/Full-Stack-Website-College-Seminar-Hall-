from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app.extensions import db
from app.models.hall import SeminarHall
from app.models.booking import BookingRequest, BookingStatus
from app.models.user import User, Role
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.forms.booking import BookingRequestForm
from app.utils.decorators import faculty_required
from app.utils.validators import validate_booking_times, has_booking_conflict

faculty_bp = Blueprint('faculty', __name__)


@faculty_bp.route('/dashboard')
@login_required
@faculty_required
def dashboard():
    """Faculty overview with booking statistics and recent submissions."""
    total_bookings = BookingRequest.query.filter_by(user_id=current_user.id).count()
    pending_bookings = BookingRequest.query.filter_by(user_id=current_user.id, status=BookingStatus.PENDING).count()
    approved_bookings = BookingRequest.query.filter_by(user_id=current_user.id, status=BookingStatus.APPROVED).count()
    rejected_bookings = BookingRequest.query.filter_by(user_id=current_user.id, status=BookingStatus.REJECTED).count()

    recent_bookings = BookingRequest.query.filter_by(user_id=current_user.id)\
        .order_by(BookingRequest.created_at.desc()).limit(5).all()

    active_halls = SeminarHall.query.filter_by(is_active=True).all()

    return render_template(
        'faculty/dashboard.html',
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        approved_bookings=approved_bookings,
        rejected_bookings=rejected_bookings,
        recent_bookings=recent_bookings,
        active_halls=active_halls
    )


@faculty_bp.route('/bookings/new', methods=['GET', 'POST'])
@login_required
@faculty_required
def new_booking():
    """Submit a new seminar hall reservation request."""
    form = BookingRequestForm()
    # Populate dynamic active hall choices
    active_halls = SeminarHall.query.filter_by(is_active=True).order_by(SeminarHall.name.asc()).all()
    form.hall_id.choices = [(h.id, f"{h.name} ({h.code}) - Capacity: {h.capacity}") for h in active_halls]

    if not active_halls:
        flash("No seminar halls are currently active for reservations.", "warning")
        return redirect(url_for('faculty.dashboard'))

    if form.validate_on_submit():
        # Validate time logic
        is_valid_time, time_err = validate_booking_times(
            form.booking_date.data,
            form.start_time.data,
            form.end_time.data
        )
        if not is_valid_time:
            flash(time_err, "danger")
            return render_template('faculty/new_booking.html', form=form)

        # Check maintenance
        selected_hall = SeminarHall.query.get(form.hall_id.data)
        if selected_hall.is_under_maintenance(form.booking_date.data):
            flash(f"{selected_hall.name} is scheduled for maintenance on {form.booking_date.data}.", "danger")
            return render_template('faculty/new_booking.html', form=form)

        # Pre-check for overlapping approved bookings
        if has_booking_conflict(form.hall_id.data, form.booking_date.data, form.start_time.data, form.end_time.data):
            flash(
                "A conflicting approved reservation already exists for this hall and time window. "
                "Please choose an alternate slot or hall.",
                "danger"
            )
            return render_template('faculty/new_booking.html', form=form)

        # Create new booking request
        booking = BookingRequest(
            hall_id=form.hall_id.data,
            user_id=current_user.id,
            event_title=form.event_title.data.strip(),
            description=form.description.data.strip(),
            attendees_count=form.attendees_count.data,
            booking_date=form.booking_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            status=BookingStatus.PENDING
        )
        db.session.add(booking)
        db.session.commit()

        # Audit submission
        AuditLog.log_action(
            action="BOOKING_SUBMITTED",
            user_id=current_user.id,
            target_type="BookingRequest",
            target_id=booking.id,
            details=f"Requested {selected_hall.name} for {booking.booking_date} ({booking.booking_reference})",
            ip_address=request.remote_addr
        )

        # Notify Principals of pending request
        principals = User.query.filter_by(role=Role.PRINCIPAL, is_active=True).all()
        for p in principals:
            Notification.send(
                user_id=p.id,
                title="New Booking Awaiting Approval",
                message=f"Prof. {current_user.name} submitted a reservation for {selected_hall.name} on {booking.booking_date}.",
                link=url_for('principal.review_booking', booking_id=booking.id)
            )

        flash(f"Booking request {booking.booking_reference} submitted successfully for Principal review.", "success")
        return redirect(url_for('faculty.my_bookings'))

    return render_template('faculty/new_booking.html', form=form)


@faculty_bp.route('/bookings')
@login_required
@faculty_required
def my_bookings():
    """Paginated list of faculty bookings with status filtering."""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '').upper()

    query = BookingRequest.query.filter_by(user_id=current_user.id)
    if status_filter in [BookingStatus.PENDING, BookingStatus.APPROVED, BookingStatus.REJECTED, BookingStatus.CANCELLED]:
        query = query.filter_by(status=status_filter)

    bookings = query.order_by(BookingRequest.booking_date.desc(), BookingRequest.start_time.desc())\
        .paginate(page=page, per_page=10, error_out=False)

    return render_template('faculty/my_bookings.html', bookings=bookings, current_status=status_filter)


@faculty_bp.route('/bookings/<int:booking_id>')
@login_required
@faculty_required
def booking_detail(booking_id):
    """View details of a specific booking request."""
    booking = BookingRequest.query.get_or_404(booking_id)

    # Security check: only owner or administrator may view
    if booking.user_id != current_user.id and current_user.role != Role.ADMIN:
        abort(403)

    return render_template('faculty/booking_detail.html', booking=booking)


@faculty_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@faculty_required
def cancel_booking(booking_id):
    """Faculty cancellation of their own pending or future approved booking."""
    booking = BookingRequest.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        abort(403)

    if booking.status == BookingStatus.CANCELLED:
        flash("This booking is already cancelled.", "info")
        return redirect(url_for('faculty.booking_detail', booking_id=booking.id))

    
    # Allow cancellation only for pending or approved bookings
    if booking.status not in (BookingStatus.PENDING, BookingStatus.APPROVED):
        flash("Only pending or approved bookings can be cancelled.", "warning")
        return redirect(url_for('faculty.booking_detail', booking_id=booking.id))

    # Prevent cancellation of past events
    if booking.booking_date < date.today():
        flash("Past events cannot be cancelled.", "warning")
        return redirect(url_for('faculty.booking_detail', booking_id=booking.id))


    booking.status = BookingStatus.CANCELLED
    db.session.commit()

    AuditLog.log_action(
        action="BOOKING_CANCELLED",
        user_id=current_user.id,
        target_type="BookingRequest",
        target_id=booking.id,
        details=f"Booking {booking.booking_reference} cancelled by faculty",
        ip_address=request.remote_addr
    )

    flash(f"Booking {booking.booking_reference} has been cancelled.", "info")
    return redirect(url_for('faculty.my_bookings'))