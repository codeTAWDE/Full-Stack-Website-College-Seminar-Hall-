from datetime import datetime, date, timedelta
from io import BytesIO
from xml.sax.saxutils import escape

from flask import (
    Blueprint, render_template, redirect, url_for, request, jsonify, send_file
)
from flask_login import current_user, login_required
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, LongTable
)
from app.models.user import Role
from app.utils.decorators import role_required
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




@main_bp.route('/weekly-report.pdf')
@login_required
def weekly_report_pdf():
    """Generate a read-only weekly booking report for signed-in users."""
    if current_user.role not in (Role.FACULTY, Role.PRINCIPAL, Role.ADMIN):
        from flask import abort
        abort(403)

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    bookings = BookingRequest.query.filter(
        BookingRequest.booking_date >= week_start,
        BookingRequest.booking_date <= week_end
    ).order_by(
        BookingRequest.booking_date.asc(),
        BookingRequest.start_time.asc()
    ).all()

    status_order = [
        BookingStatus.PENDING,
        BookingStatus.APPROVED,
        BookingStatus.REJECTED,
        BookingStatus.CANCELLED,
    ]
    status_counts = {
        status: sum(1 for booking in bookings if booking.status == status)
        for status in status_order
    }

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="Weekly Seminar Hall Booking Report",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0b2545"),
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="SmallCell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        wordWrap="CJK",
    ))

    story = [
        Paragraph("Agnel Polytechnic", styles["ReportTitle"]),
        Paragraph("Weekly Seminar Hall Booking Report", styles["Heading2"]),
        Paragraph(
            f"Period: {week_start.strftime('%d %b %Y')} – "
            f"{week_end.strftime('%d %b %Y')}",
            styles["Normal"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Booking Summary", styles["Heading3"]),
    ]

    summary_data = [["Status", "Total"]]
    summary_data.extend([[status.title(), str(status_counts[status])]
                         for status in status_order])
    summary_data.append(["All bookings", str(len(bookings))])

    summary_table = Table(summary_data, colWidths=[55 * mm, 25 * mm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b2545")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([summary_table, Spacer(1, 6 * mm)])
    story.append(Paragraph("Booking Details", styles["Heading3"]))

    headers = [
        "Reference", "Date", "Time", "Hall", "Requester",
        "Event / Purpose", "Attendees", "Status",
    ]
    table_data = [headers]

    for booking in bookings:
        table_data.append([
            Paragraph(escape(booking.booking_reference or ""), styles["SmallCell"]),
            Paragraph(booking.booking_date.strftime("%d %b %Y"), styles["SmallCell"]),
            Paragraph(
                f"{booking.start_time.strftime('%H:%M')}–"
                f"{booking.end_time.strftime('%H:%M')}",
                styles["SmallCell"],
            ),
            Paragraph(escape(booking.hall.name or ""), styles["SmallCell"]),
            Paragraph(escape(booking.applicant.name or ""), styles["SmallCell"]),
            Paragraph(
                escape(booking.event_title or "")
                + (f"<br/>{escape(booking.description)}"
                   if booking.description else ""),
                styles["SmallCell"],
            ),
            str(booking.attendees_count),
            Paragraph(escape(booking.status.title()), styles["SmallCell"]),
        ])

    if not bookings:
        table_data.append([
            Paragraph("No bookings recorded for this week.", styles["SmallCell"]),
            "", "", "", "", "", "", "",
        ])

    details_table = LongTable(
        table_data,
        colWidths=[27 * mm, 23 * mm, 25 * mm, 30 * mm,
                   31 * mm, 65 * mm, 17 * mm, 22 * mm],
        repeatRows=1,
    )
    details_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b2545")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f1f5f9")]),
        ("SPAN", (0, 1), (-1, 1)) if not bookings else
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
    ]))
    story.append(details_table)

    document.build(story)
    buffer.seek(0)

    filename = f"SHMS_Weekly_Report_{week_start.isoformat()}.pdf"
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
