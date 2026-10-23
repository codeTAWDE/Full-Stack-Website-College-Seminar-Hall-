from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from app.models.hall import SeminarHall


class BookingRequestForm(FlaskForm):
    """Form for faculty to request a seminar hall reservation."""
    hall_id = SelectField('Seminar Hall', coerce=int, validators=[
        DataRequired(message="Please select a seminar hall.")
    ])
    event_title = StringField('Event Title', validators=[
        DataRequired(message="Event title is required."),
        Length(max=150, message="Title must be under 150 characters.")
    ])
    description = TextAreaField('Event Description / Purpose', validators=[
        DataRequired(message="Please describe the purpose of the booking."),
        Length(max=1000, message="Description must be under 1000 characters.")
    ])
    attendees_count = IntegerField('Expected Number of Attendees', validators=[
        DataRequired(message="Attendee count is required."),
        NumberRange(min=1, message="Attendee count must be at least 1.")
    ])
    booking_date = DateField('Booking Date', validators=[
        DataRequired(message="Booking date is required.")
    ])
    start_time = TimeField('Start Time (24h format: HH:MM)', validators=[
        DataRequired(message="Start time is required.")
    ])
    end_time = TimeField('End Time (24h format: HH:MM)', validators=[
        DataRequired(message="End time is required.")
    ])
    submit = SubmitField('Submit Booking Request')

    def validate_booking_date(self, field):
        """Prevent reservations in the past."""
        if field.data < date.today():
            raise ValidationError("Booking date cannot be in the past.")

    def validate_end_time(self, field):
        """Ensure end time is strictly after start time."""
        if self.start_time.data and field.data:
            if field.data <= self.start_time.data:
                raise ValidationError("End time must be after start time.")

    def validate_attendees_count(self, field):
        """Ensure attendees do not exceed selected hall capacity."""
        if self.hall_id.data:
            hall = SeminarHall.query.get(self.hall_id.data)
            if hall and field.data > hall.capacity:
                raise ValidationError(
                    f"Selected hall ({hall.name}) has a maximum capacity of {hall.capacity} seats."
                )


class BookingDecisionForm(FlaskForm):
    """Form for Principal / Admin to review a booking."""
    action = SelectField('Decision', choices=[
        ('APPROVE', 'Approve Booking'),
        ('REJECT', 'Reject Booking')
    ], validators=[DataRequired()])
    rejection_reason = TextAreaField('Reason (Required if rejecting)', validators=[
        Length(max=500, message="Reason must be under 500 characters.")
    ])
    submit = SubmitField('Submit Decision')

    def validate_rejection_reason(self, field):
        if self.action.data == 'REJECT' and not (field.data and field.data.strip()):
            raise ValidationError("You must provide a reason when rejecting a booking.")