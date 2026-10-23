from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User, Role


class UserCreateForm(FlaskForm):
    """Admin form to register new users."""
    name = StringField('Full Name', validators=[
        DataRequired(message="Name is required."),
        Length(max=100)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Valid email required.")
    ])
    role = SelectField('Role', choices=Role.CHOICES, default=Role.FACULTY)
    department = StringField('Department', validators=[Length(max=100)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    password = PasswordField('Initial Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must be at least 8 characters.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Create User')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("An account with this email address already exists.")


class UserEditForm(FlaskForm):
    """Admin form to edit existing user details."""
    name = StringField('Full Name', validators=[
        DataRequired(message="Name is required."),
        Length(max=100)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Valid email required.")
    ])
    role = SelectField('Role', choices=Role.CHOICES)
    department = StringField('Department', validators=[Length(max=100)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    is_active = BooleanField('Account Active')
    submit = SubmitField('Update User')

    def __init__(self, original_id, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.original_id = original_id

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if user and user.id != self.original_id:
            raise ValidationError("This email is already in use by another account.")


class ChangePasswordForm(FlaskForm):
    """User account password change form."""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message="Passwords must match.")
    ])
    submit = SubmitField('Update Password')