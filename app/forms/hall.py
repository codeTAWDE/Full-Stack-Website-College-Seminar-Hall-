from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from app.models.hall import SeminarHall


class SeminarHallForm(FlaskForm):
    """Form to create or update a seminar hall."""
    name = StringField('Hall Name', validators=[
        DataRequired(message="Hall name is required."),
        Length(max=100)
    ])
    code = StringField('Hall Code (e.g. SH-101)', validators=[
        DataRequired(message="Hall code is required."),
        Length(max=20)
    ])
    location = StringField('Campus Location / Block', validators=[
        DataRequired(message="Location is required."),
        Length(max=150)
    ])
    capacity = IntegerField('Seating Capacity', validators=[
        DataRequired(message="Capacity is required."),
        NumberRange(min=10, max=5000, message="Capacity must be between 10 and 5000.")
    ])
    description = TextAreaField('Description & Facilities', validators=[
        Length(max=500)
    ])
    is_active = BooleanField('Active & Available for Bookings', default=True)
    submit = SubmitField('Save Seminar Hall')

    def __init__(self, original_id=None, *args, **kwargs):
        super(SeminarHallForm, self).__init__(*args, **kwargs)
        self.original_id = original_id

    def validate_name(self, field):
        hall = SeminarHall.query.filter_by(name=field.data).first()
        if hall and (self.original_id is None or hall.id != self.original_id):
            raise ValidationError("A seminar hall with this name already exists.")

    def validate_code(self, field):
        hall = SeminarHall.query.filter_by(code=field.data).first()
        if hall and (self.original_id is None or hall.id != self.original_id):
            raise ValidationError("A seminar hall with this code already exists.")


class EquipmentForm(FlaskForm):
    """Form to add or edit equipment in a hall."""
    name = StringField('Equipment Name', validators=[
        DataRequired(message="Equipment name is required."),
        Length(max=100)
    ])
    quantity = IntegerField('Quantity', validators=[
        DataRequired(),
        NumberRange(min=1, message="Quantity must be at least 1.")
    ], default=1)
    status = SelectField('Status', choices=[
        ('Operational', 'Operational'),
        ('Under Repair', 'Under Repair'),
        ('Faulty', 'Faulty')
    ], default='Operational')
    submit = SubmitField('Save Equipment')


class MaintenanceRecordForm(FlaskForm):
    """Form to schedule hall maintenance."""
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    reason = StringField('Maintenance Reason', validators=[
        DataRequired(),
        Length(max=255)
    ])
    status = SelectField('Status', choices=[
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed')
    ], default='SCHEDULED')
    submit = SubmitField('Schedule Maintenance')

    def validate_end_date(self, field):
        if self.start_date.data and field.data < self.start_date.data:
            raise ValidationError("End date cannot be earlier than start date.")