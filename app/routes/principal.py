from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import current_user, login_required
from app.extensions import db
from app.models.booking import BookingRequest, BookingStatus
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.forms.booking import BookingDecisionForm
from app.utils.decorators import principal_required
from app.utils.validators import check_and_lock_hall_for_approval
from app.utils.email import send_booking_notification

principal_bp = Blueprint('principal', __name__)


@principal_bp.route('/dashboard')
@login_required
@principal_required
def dashboard():
    """Principal executive dashboard with pending approvals and schedule overview."""
    pending_count = BookingRequest.query.filter_by(status=BookingStatus.PENDING).count()
    approved_today = BookingRequest.query.filter(
        BookingRequest.status == BookingStatus.APPROVED,
        BookingRequest.booking_date == date.today()
    ).count()

    pending_list = BookingRequest.query.filter_by(status=BookingStatus.PENDING)\
        .order_by(BookingRequest.booking_date.asc(), BookingRequest.start_time.asc()).limit(5).all()

    today_schedule = BookingRequest.query.filter(
        BookingRequest.status == BookingStatus.APPROVED,
        BookingRequest.booking_date == date.today()
    ).order_by(BookingRequest.start_time.asc()).all()

    return render_template(
        'principal/dashboard.html',
        pending_count=pending_count,
        approved_today=approved_today,
        pending_list=pending_list,
        today_schedule=today_schedule
    )


@principal_bp.route('/pending')
@login_required
@principal_required
def pending_approvals():
    """List of all pending booking requests awaiting Principal authorization."""
    page = request.args.get('page', 1, type=int)
    pending_requests = BookingRequest.query.filter_by(status=BookingStatus.PENDING)\
        .order_by(BookingRequest.booking_date.asc(), BookingRequest.start_time.asc())\
        .paginate(page=page, per_page=10, error_out=False)

    return render_template('principal/pending_approvals.html', bookings=pending_requests)


@principal_bp.route('/booking/<int:booking_id>/review', methods=['GET', 'POST'])
@login_required
@principal_required
def review_booking(booking_id):
    """Detailed booking inspection and transactional approval/rejection decision."""
    form = BookingDecisionForm()
    booking = BookingRequest.query.get_or_404(booking_id)

    if form.validate_on_submit():
        decision = form.action.data

        if decision == 'APPROVE':
            # Concurrency-safe lock and check
            is_safe, error_msg, locked_booking = check_and_lock_hall_for_approval(booking.id)
            if not is_safe:
                flash(f"Cannot approve: {error_msg}", "danger")
                return render_template('principal/review_booking.html', booking=booking, form=form)

            locked_booking.status = BookingStatus.APPROVED
            locked_booking.approved_by_id = current_user.id
            locked_booking.rejection_reason = None
            db.session.commit()

            # Record in Audit Trail
            AuditLog.log_action(
                action="BOOKING_APPROVED",
                user_id=current_user.id,
                target_type="BookingRequest",
                target_id=locked_booking.id,
                details=f"Approved booking {locked_booking.booking_reference} for {locked_booking.hall.name}",
                ip_address=request.remote_addr
            )

            # In-App Notification to faculty
            Notification.send(
                user_id=locked_booking.user_id,
                title="Booking Approved",
                message=f"Your request for {locked_booking.hall.name} on {locked_booking.booking_date} ({locked_booking.event_title}) was approved by the Principal.",
                link=url_for('faculty.booking_detail', booking_id=locked_booking.id)
            )

            # Email notification
            email_ok, email_message = send_booking_notification(
                user=locked_booking.applicant,
                subject=f"Approved: Booking {locked_booking.booking_reference} - {locked_booking.hall.name}",
                message_content=f"Your booking for {locked_booking.hall.name} on {locked_booking.booking_date} ({locked_booking.start_time.strftime('%H:%M')} - {locked_booking.end_time.strftime('%H:%M')}) has been APPROVED by the Principal."
            )
            if email_ok:
                current_app.logger.info(
                    "Booking approval notification sent for %s: %s",
                    locked_booking.booking_reference,
                    email_message
                )
            else:
                current_app.logger.warning(
                    "Booking approval notification failed for %s: %s",
                    locked_booking.booking_reference,
                    email_message
                )

            flash(f"Booking {locked_booking.booking_reference} has been successfully APPROVED.", "success")
            return redirect(url_for('principal.pending_approvals'))

        elif decision == 'REJECT':
            booking.status = BookingStatus.REJECTED
            booking.approved_by_id = current_user.id
            booking.rejection_reason = form.rejection_reason.data.strip()
            db.session.commit()

            # Audit record
            AuditLog.log_action(
                action="BOOKING_REJECTED",
                user_id=current_user.id,
                target_type="BookingRequest",
                target_id=booking.id,
                details=f"Rejected booking {booking.booking_reference}: {booking.rejection_reason}",
                ip_address=request.remote_addr
            )

            # Notification to faculty
            Notification.send(
                user_id=booking.user_id,
                title="Booking Request Rejected",
                message=f"Your request for {booking.hall.name} on {booking.booking_date} was rejected. Reason: {booking.rejection_reason}",
                link=url_for('faculty.booking_detail', booking_id=booking.id)
            )

            # Email notification
            email_ok, email_message = send_booking_notification(
                user=booking.applicant,
                subject=f"Rejected: Booking {booking.booking_reference} - {booking.hall.name}",
                message_content=f"Your booking request for {booking.hall.name} on {booking.booking_date} ({booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}) has been REJECTED by the Principal.\nReason: {booking.rejection_reason}"
            )
            if email_ok:
                current_app.logger.info(
                    "Booking rejection notification sent for %s: %s",
                    booking.booking_reference,
                    email_message
                )
            else:
                current_app.logger.warning(
                    "Booking rejection notification failed for %s: %s",
                    booking.booking_reference,
                    email_message
                )

            flash(f"Booking {booking.booking_reference} has been REJECTED.", "info")
            return redirect(url_for('principal.pending_approvals'))

    return render_template('principal/review_booking.html', booking=booking, form=form)


@principal_bp.route('/approved-bookings')
@login_required
@principal_required
def approved_bookings():
    """List approved bookings that the Principal can manage."""
    page = request.args.get('page', 1, type=int)

    bookings = BookingRequest.query.filter_by(
        status=BookingStatus.APPROVED
    ).order_by(
        BookingRequest.booking_date.asc(),
        BookingRequest.start_time.asc()
    ).paginate(page=page, per_page=10, error_out=False)

    return render_template(
        'principal/approved_bookings.html',
        bookings=bookings
    )


@principal_bp.route(
    '/booking/<int:booking_id>/revoke-approval',
    methods=['GET', 'POST']
)
@login_required
@principal_required
def revoke_approval(booking_id):
    """Reject a booking that was previously approved by the Principal."""
    booking = BookingRequest.query.get_or_404(booking_id)
    form = BookingDecisionForm()

    if booking.status != BookingStatus.APPROVED:
        flash(
            "Only currently approved bookings can have their approval revoked.",
            "warning"
        )
        return redirect(url_for('principal.approved_bookings'))

    if form.validate_on_submit():
        reason = (form.rejection_reason.data or "").strip()

        if not reason:
            form.rejection_reason.errors.append(
                "Please provide a reason for revoking this approval."
            )
            return render_template(
                'principal/revoke_approval.html',
                booking=booking,
                form=form
            )

        # Recheck status immediately before changing it.
        db.session.refresh(booking)

        if booking.status != BookingStatus.APPROVED:
            flash("This booking is no longer approved.", "warning")
            return redirect(url_for('principal.approved_bookings'))

        booking.status = BookingStatus.REJECTED
        booking.approved_by_id = current_user.id
        booking.rejection_reason = reason

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Unable to update the booking. Please try again.", "danger")
            return redirect(url_for('principal.approved_bookings'))

        AuditLog.log_action(
            action="BOOKING_APPROVAL_REVOKED",
            user_id=current_user.id,
            target_type="BookingRequest",
            target_id=booking.id,
            details=(
                f"Revoked previous approval for booking "
                f"{booking.booking_reference}. Reason: {reason}"
            ),
            ip_address=request.remote_addr
        )

        Notification.send(
            user_id=booking.user_id,
            title="Previously Approved Booking Now Rejected",
            message=(
                f"Your previously approved booking {booking.booking_reference} "
                f"for {booking.hall.name} on {booking.booking_date} "
                f"({booking.event_title}) has now been rejected by the Principal. "
                f"Reason: {reason}"
            ),
            link=url_for(
                'faculty.booking_detail',
                booking_id=booking.id
            )
        )

        send_booking_notification(
            user=booking.applicant,
            subject=(
                f"Important Status Update: Booking "
                f"{booking.booking_reference} Rejected"
            ),
            message_content=(
                f"Your previously approved booking for {booking.hall.name} "
                f"on {booking.booking_date} "
                f"({booking.start_time.strftime('%H:%M')} - "
                f"{booking.end_time.strftime('%H:%M')}) "
                f"has now been REJECTED by the Principal.\n\n"
                f"Reason: {reason}"
            )
        )

        flash(
            f"Approval revoked. Booking {booking.booking_reference} "
            "is now rejected.",
            "success"
        )
        return redirect(url_for('principal.approved_bookings'))

    return render_template(
        'principal/revoke_approval.html',
        booking=booking,
        form=form
    )
