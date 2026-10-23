from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from sqlalchemy import func
from app.extensions import db
from app.models.user import User, Role
from app.models.hall import SeminarHall, Equipment, MaintenanceRecord
from app.models.booking import BookingRequest, BookingStatus
from app.models.audit_log import AuditLog
from app.forms.hall import SeminarHallForm, EquipmentForm, MaintenanceRecordForm
from app.forms.user import UserCreateForm, UserEditForm
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """System Administration overview metrics."""
    total_users = User.query.count()
    total_halls = SeminarHall.query.count()
    total_bookings = BookingRequest.query.count()
    pending_bookings = BookingRequest.query.filter_by(status=BookingStatus.PENDING).count()

    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_halls=total_halls,
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        recent_logs=recent_logs
    )


# ================= SEMINAR HALL MANAGEMENT =================

@admin_bp.route('/halls')
@login_required
@admin_required
def halls():
    """List all seminar halls."""
    all_halls = SeminarHall.query.order_by(SeminarHall.id.asc()).all()
    return render_template('admin/halls.html', halls=all_halls)


@admin_bp.route('/halls/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_hall():
    """Create a new seminar hall."""
    form = SeminarHallForm()
    if form.validate_on_submit():
        hall = SeminarHall(
            name=form.name.data.strip(),
            code=form.code.data.strip().upper(),
            location=form.location.data.strip(),
            capacity=form.capacity.data,
            description=form.description.data.strip() if form.description.data else None,
            is_active=form.is_active.data
        )
        db.session.add(hall)
        db.session.commit()

        AuditLog.log_action(
            action="CREATE_HALL",
            user_id=current_user.id,
            target_type="SeminarHall",
            target_id=hall.id,
            details=f"Created hall {hall.name} ({hall.code})",
            ip_address=request.remote_addr
        )

        flash(f"Seminar hall {hall.name} created successfully.", "success")
        return redirect(url_for('admin.halls'))

    return render_template('admin/hall_form.html', form=form, title="Create Seminar Hall")


@admin_bp.route('/halls/<int:hall_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_hall(hall_id):
    """Edit existing seminar hall details."""
    hall = SeminarHall.query.get_or_404(hall_id)
    form = SeminarHallForm(original_id=hall.id, obj=hall)

    if form.validate_on_submit():
        hall.name = form.name.data.strip()
        hall.code = form.code.data.strip().upper()
        hall.location = form.location.data.strip()
        hall.capacity = form.capacity.data
        hall.description = form.description.data.strip() if form.description.data else None
        hall.is_active = form.is_active.data
        db.session.commit()

        AuditLog.log_action(
            action="EDIT_HALL",
            user_id=current_user.id,
            target_type="SeminarHall",
            target_id=hall.id,
            details=f"Updated hall {hall.code}",
            ip_address=request.remote_addr
        )

        flash(f"Hall {hall.name} updated successfully.", "success")
        return redirect(url_for('admin.halls'))

    return render_template('admin/hall_form.html', form=form, title=f"Edit {hall.name}", hall=hall)


@admin_bp.route('/halls/<int:hall_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_hall(hall_id):
    """Enable or disable a seminar hall for reservations."""
    hall = SeminarHall.query.get_or_404(hall_id)
    hall.is_active = not hall.is_active
    db.session.commit()

    state = "activated" if hall.is_active else "deactivated"
    AuditLog.log_action(
        action="TOGGLE_HALL_STATE",
        user_id=current_user.id,
        target_type="SeminarHall",
        target_id=hall.id,
        details=f"Hall {hall.code} {state}",
        ip_address=request.remote_addr
    )

    flash(f"Seminar hall {hall.name} is now {state}.", "info")
    return redirect(url_for('admin.halls'))


# ================= USER MANAGEMENT =================

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List system users with pagination."""
    page = request.args.get('page', 1, type=int)
    users_list = User.query.order_by(User.role.asc(), User.name.asc())\
        .paginate(page=page, per_page=15, error_out=False)

    return render_template('admin/users.html', users=users_list)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Provision a new user account."""
    form = UserCreateForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            role=form.role.data,
            department=form.department.data.strip() if form.department.data else None,
            phone=form.phone.data.strip() if form.phone.data else None,
            is_active=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        AuditLog.log_action(
            action="CREATE_USER",
            user_id=current_user.id,
            target_type="User",
            target_id=user.id,
            details=f"Created user {user.email} with role {user.role}",
            ip_address=request.remote_addr
        )

        flash(f"User account for {user.name} ({user.email}) created successfully.", "success")
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', form=form, title="Create New User")


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Modify user credentials, role, or profile."""
    user = User.query.get_or_404(user_id)
    form = UserEditForm(original_id=user.id, obj=user)

    if form.validate_on_submit():
        # Prevent administrator from accidentally removing their own admin rights
        if user.id == current_user.id and form.role.data != Role.ADMIN:
            flash("You cannot demote your own administrator account.", "danger")
            return render_template('admin/user_form.html', form=form, title="Edit User", user=user)

        user.name = form.name.data.strip()
        user.email = form.email.data.strip().lower()
        user.role = form.role.data
        user.department = form.department.data.strip() if form.department.data else None
        user.phone = form.phone.data.strip() if form.phone.data else None
        user.is_active = form.is_active.data
        db.session.commit()

        AuditLog.log_action(
            action="EDIT_USER",
            user_id=current_user.id,
            target_type="User",
            target_id=user.id,
            details=f"Updated user {user.email} ({user.role})",
            ip_address=request.remote_addr
        )

        flash(f"User {user.name} updated successfully.", "success")
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', form=form, title=f"Edit {user.name}", user=user)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    """Activate or deactivate a user account."""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()

    status_str = "activated" if user.is_active else "deactivated"
    AuditLog.log_action(
        action="TOGGLE_USER_ACTIVE",
        user_id=current_user.id,
        target_type="User",
        target_id=user.id,
        details=f"User {user.email} {status_str}",
        ip_address=request.remote_addr
    )

    flash(f"Account for {user.name} has been {status_str}.", "info")
    return redirect(url_for('admin.users'))


# ================= AUDIT LOGS & REPORTS =================

@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """Paginated security audit trail."""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()

    query = AuditLog.query
    if action_filter:
        query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))

    logs = query.order_by(AuditLog.timestamp.desc())\
        .paginate(page=page, per_page=20, error_out=False)

    return render_template('admin/audit_logs.html', logs=logs, action_filter=action_filter)


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Analytical breakdown of seminar hall utilization."""
    # Bookings grouped by hall
    bookings_by_hall = db.session.query(
        SeminarHall.name,
        func.count(BookingRequest.id).label('total_bookings')
    ).join(BookingRequest, SeminarHall.id == BookingRequest.hall_id)\
     .group_by(SeminarHall.name).all()

    # Bookings grouped by status
    bookings_by_status = db.session.query(
        BookingRequest.status,
        func.count(BookingRequest.id)
    ).group_by(BookingRequest.status).all()

    # Total approved hours
    total_approved = BookingRequest.query.filter_by(status=BookingStatus.APPROVED).count()

    return render_template(
        'admin/reports.html',
        bookings_by_hall=bookings_by_hall,
        bookings_by_status=bookings_by_status,
        total_approved=total_approved
    )