from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from app.extensions import db


class Role:
    """System-wide role constants."""
    FACULTY = 'FACULTY'
    PRINCIPAL = 'PRINCIPAL'
    ADMIN = 'ADMIN'

    CHOICES = [
        (FACULTY, 'Faculty'),
        (PRINCIPAL, 'Principal'),
        (ADMIN, 'System Administrator')
    ]


class User(UserMixin, db.Model):
    """User account model for Faculty, Principal, and Administrators."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.FACULTY, index=True)
    department = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    bookings = db.relationship(
        'BookingRequest',
        backref='applicant',
        lazy='dynamic',
        foreign_keys='BookingRequest.user_id',
        cascade='all, delete-orphan'
    )
    approved_bookings = db.relationship(
        'BookingRequest',
        backref='approver',
        lazy='dynamic',
        foreign_keys='BookingRequest.approved_by_id'
    )
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hashes the password securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies candidate password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == Role.ADMIN

    def is_principal(self):
        return self.role == Role.PRINCIPAL

    def is_faculty(self):
        return self.role == Role.FACULTY

    def get_reset_token(self):
        """Generates an expiring URL-safe password reset token."""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='shms-password-reset-salt')

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        """Verifies password reset token within expiration period (default 30 mins)."""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='shms-password-reset-salt', max_age=expires_sec)
            user_id = data.get('user_id')
        except Exception:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"<User {self.id}: {self.email} ({self.role})>"