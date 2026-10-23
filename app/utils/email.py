import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, url_for

logger = logging.getLogger(__name__)


def _log_info(msg):
    """Log an info message through current_app.logger when available, else module logger."""
    try:
        if current_app:
            current_app.logger.info(msg)
            return
    except RuntimeError:
        pass
    logger.info(msg)


def _log_warning(msg):
    """Log a warning message through current_app.logger when available, else module logger."""
    try:
        if current_app:
            current_app.logger.warning(msg)
            return
    except RuntimeError:
        pass
    logger.warning(msg)


def _log_error(msg):
    """Log an error message through current_app.logger when available, else module logger."""
    try:
        if current_app:
            current_app.logger.error(msg)
            return
    except RuntimeError:
        pass
    logger.error(msg)


def _send_smtp_email(to_email, subject, body_text, body_html=None):
    """Internal SMTP dispatcher with error handling."""
    mail_server = current_app.config.get('MAIL_SERVER')
    mail_port = current_app.config.get('MAIL_PORT', 587)
    mail_username = current_app.config.get('MAIL_USERNAME')
    mail_password = current_app.config.get('MAIL_PASSWORD')
    default_sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'shms-noreply@college.edu')
    use_tls = current_app.config.get('MAIL_USE_TLS', True)

    # If no SMTP credentials are configured, log for development safety without exposing sensitive content
    if not mail_username or not mail_password:
        _log_warning(f"[EMAIL] SMTP credentials not configured in environment. Subject: {subject}")
        return False, "SMTP credentials not configured in environment. Logged to console."

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = default_sender
        msg['To'] = to_email

        msg.attach(MIMEText(body_text, 'plain'))
        if body_html:
            msg.attach(MIMEText(body_html, 'html'))

        if mail_port == 465:
            with smtplib.SMTP_SSL(mail_server, mail_port, timeout=20) as server:
                server.login(mail_username, mail_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(mail_server, mail_port, timeout=20) as server:
                if use_tls:
                    server.starttls()
                server.login(mail_username, mail_password)
                server.send_message(msg)

        _log_info(f"Email notification successfully delivered: {subject}")
        return True, "Email sent successfully."
    except Exception as e:
        _log_error(f"Failed to deliver email ({subject}): {str(e)}")
        return False, f"Failed to send email: {str(e)}"


def send_reset_email(user, token):
    """Sends secure password reset instructions with token link."""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    subject = "Agnel Polytechnic SHMS - Password Reset Request"
    body_text = f"""Dear {user.name},

To reset your password for the Seminar Hall Management System, click the following link:
{reset_url}

This link is valid for 30 minutes. If you did not make this request, simply ignore this email.

Regards,
SHMS Administration
Agnel Polytechnic, Vashi
"""
    body_html = f"""
    <p>Dear {user.name},</p>
    <p>To reset your password for the Seminar Hall Management System, click the link below:</p>
    <p><a href="{reset_url}" style="display:inline-block;padding:10px 18px;background-color:#0b2545;color:#ffffff;text-decoration:none;border-radius:4px;">Reset Password</a></p>
    <p><small>Or copy this URL into your browser:<br>{reset_url}</small></p>
    <p>This link is valid for 30 minutes. If you did not request this, please ignore this email.</p>
    <hr>
    <p><small>Seminar Hall Management System &bull; Agnel Polytechnic, Vashi</small></p>
    """
    return _send_smtp_email(user.email, subject, body_text, body_html)


def send_booking_notification(user, subject, message_content, action_url=None):
    """Sends booking status updates (Approved, Rejected, Submitted)."""
    full_url = url_for('main.index', _external=True) if not action_url else action_url
    body_text = f"""Dear {user.name},

{message_content}

View details: {full_url}

Regards,
SHMS Administration
Agnel Polytechnic, Vashi
"""
    body_html = f"""
    <p>Dear {user.name},</p>
    <p>{message_content}</p>
    <p><a href="{full_url}">Click here to view your booking details</a></p>
    <hr>
    <p><small>Seminar Hall Management System &bull; Agnel Polytechnic, Vashi</small></p>
    """
    return _send_smtp_email(user.email, subject, body_text, body_html)
