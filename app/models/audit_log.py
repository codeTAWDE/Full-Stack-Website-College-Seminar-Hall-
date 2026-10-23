from datetime import datetime
from app.extensions import db


class AuditLog(db.Model):
    """System audit log for actions, approvals, and security events."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    @classmethod
    def log_action(cls, action, user_id=None, target_type=None, target_id=None, details=None, ip_address=None):
        """Helper to create and commit an audit log entry in one call."""
        entry = cls(
            action=action,
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address
        )
        db.session.add(entry)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    def __repr__(self):
        return f"<AuditLog {self.action} by User {self.user_id} at {self.timestamp}>"