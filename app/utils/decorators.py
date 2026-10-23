from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user
from app.models.user import Role


def role_required(*allowed_roles):
    """
    Decorator to restrict route access strictly to specified roles.
    Re-checks authentication, active status, and role privileges on the server.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for('auth.login', next=request.url))

            if not current_user.is_active:
                flash("Your account has been deactivated. Please contact the administrator.", "danger")
                return redirect(url_for('auth.logout'))

            if current_user.role not in allowed_roles:
                # Deny access with a 403 HTTP status
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Restricts access to System Administrators only."""
    return role_required(Role.ADMIN)(f)


def principal_required(f):
    """Restricts booking approval access to Principals only."""
    return role_required(Role.PRINCIPAL)(f)

def faculty_required(f):
    """Restricts faculty booking actions to Faculty members only."""
    return role_required(Role.FACULTY)(f)