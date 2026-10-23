from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please provide a valid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RequestResetForm(FlaskForm):
    """Form to initiate password recovery."""
    email = StringField('Account Email', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please provide a valid email address.")
    ])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    """Form to define new password from reset token."""
    password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your new password."),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Reset Password')