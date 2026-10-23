from datetime import datetime
from app.extensions import db


class Notification(db.Model):
    """In-app alert notification."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def send(cls, user_id, title, message, link=None):
        """Creates a new in-app notification."""
        notif = cls(
            user_id=user_id,
            title=title,
            message=message,
            link=link
        )
        db.session.add(notif)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    def __repr__(self):
        return f"<Notification {self.title} for User {self.user_id} (Read: {self.is_read})>"