from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db
from app.models.user import User, Role
from app.models.audit_log import AuditLog
from app.forms.auth import LoginForm, RequestResetForm, ResetPasswordForm
from app.forms.user import ChangePasswordForm
from app.utils.email import send_reset_email

auth_bp = Blueprint('auth', __name__)


def is_safe_redirect(target):
    """Ensures redirect targets are internal to prevent open-redirect vulnerabilities."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User authentication with role-based dashboard redirection."""
    if current_user.is_authenticated:
        if current_user.role == Role.ADMIN:
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == Role.PRINCIPAL:
            return redirect(url_for('principal.dashboard'))
        return redirect(url_for('faculty.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Your account is deactivated. Please contact the administrator.", "danger")
                AuditLog.log_action(
                    action="LOGIN_FAILED_DEACTIVATED",
                    user_id=user.id,
                    target_type="User",
                    target_id=user.id,
                    details="Attempted login on deactivated account",
                    ip_address=request.remote_addr
                )
                return render_template('auth/login.html', form=form)

            # Log user into session
            login_user(user, remember=form.remember_me.data)

            # Audit successful login
            AuditLog.log_action(
                action="LOGIN_SUCCESS",
                user_id=user.id,
                target_type="User",
                target_id=user.id,
                details=f"Successful login as {user.role}",
                ip_address=request.remote_addr
            )

            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get('next')
            if next_page and is_safe_redirect(next_page):
                return redirect(next_page)

            if user.role == Role.ADMIN:
                return redirect(url_for('admin.dashboard'))
            elif user.role == Role.PRINCIPAL:
                return redirect(url_for('principal.dashboard'))
            else:
                return redirect(url_for('faculty.dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            AuditLog.log_action(
                action="LOGIN_FAILED",
                user_id=None,
                target_type="Auth",
                target_id=None,
                details=f"Failed login attempt for {form.email.data}",
                ip_address=request.remote_addr
            )

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Terminate authenticated session and record in audit log."""
    user_id = current_user.id
    user_role = current_user.role
    logout_user()

    AuditLog.log_action(
        action="LOGOUT",
        user_id=user_id,
        target_type="User",
        target_id=user_id,
        details=f"User ({user_role}) logged out",
        ip_address=request.remote_addr
    )

    flash("You have been signed out successfully.", "info")
    return redirect(url_for('main.index'))


@auth_bp.route('/reset-request', methods=['GET', 'POST'])
def reset_request():
    """Request a password reset email."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.is_active:
            token = user.get_reset_token()
            send_reset_email(user, token)
            AuditLog.log_action(
                action="PASSWORD_RESET_REQUEST",
                user_id=user.id,
                target_type="User",
                target_id=user.id,
                details="Password reset token generated",
                ip_address=request.remote_addr
            )

        # Generic response to prevent user enumeration
        flash("If an active account exists with that email, password reset instructions have been sent.", "info")
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_request.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Verify reset token and update password."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    user = User.verify_reset_token(token)
    if not user:
        flash("The password reset token is invalid or has expired.", "warning")
        return redirect(url_for('auth.reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()

        AuditLog.log_action(
            action="PASSWORD_RESET_SUCCESS",
            user_id=user.id,
            target_type="User",
            target_id=user.id,
            details="Password successfully updated using reset token",
            ip_address=request.remote_addr
        )

        flash("Your password has been reset. You may now sign in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Authenticated user password modification."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password entered is incorrect.", "danger")
            return render_template('auth/change_password.html', form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()

        AuditLog.log_action(
            action="PASSWORD_CHANGE",
            user_id=current_user.id,
            target_type="User",
            target_id=current_user.id,
            details="User updated own password",
            ip_address=request.remote_addr
        )

        flash("Your password has been changed successfully.", "success")
        return redirect(url_for('main.index'))

    return render_template('auth/change_password.html', form=form)