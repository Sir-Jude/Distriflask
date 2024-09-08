from config import basedir, Config
from flask import current_app
from flask_security.forms import RegisterForm, LoginForm
from flask_security import lookup_identity
from flask_wtf import FlaskForm
from app.models import Role, Course
from sqlalchemy import func
from wtforms import (
    BooleanField,
    FileField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms_alchemy import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
from werkzeug.local import LocalProxy
import os


def username_validator(form, field):
    # Side-effect - field.data is updated to normalized value.
    # Use proxy to we can declare this prior to initializing Security.
    _security = LocalProxy(lambda: current_app.extensions["security"])
    msg, field.data = _security._username_util.validate(field.data)
    if msg:
        raise ValidationError(msg)


class ExtendedRegisterForm(RegisterForm):
    username = StringField("Username", [DataRequired()])
    password = PasswordField("Password", [DataRequired(), Length(min=8, max=20)])
    password_confirm = PasswordField(
        "Retype password",
        validators=[
            EqualTo("password", message="RETYPE_PASSWORD_MISMATCH"),
            DataRequired(),
        ],
    )
    courses = QuerySelectMultipleField(
        "Course",
        query_factory=lambda: Course.query.order_by(func.lower(Course.name)).all(),
        get_label="name",
        blank_text="None",
    )
    active = BooleanField("Active")
    roles = QuerySelectMultipleField(
        "Roles",
        query_factory=lambda: Role.query.all(),
        get_label="name",
        validators=[DataRequired()],
    )

    def __init__(self, *args, **kwargs):
        super(ExtendedRegisterForm, self).__init__(*args, **kwargs)
        # Remove email field
        delattr(self, "email")
        delattr(self, "submit")


class ExtendedLoginForm(LoginForm):
    username = StringField("Username", [DataRequired()])

    def validate(self, **kwargs):
        self.user = lookup_identity(self.username.data)
        # Setting 'ifield' informs the default login form validation
        # handler that the identity has already been confirmed.
        self.ifield = self.username
        if not super().validate(**kwargs):
            return False
        return True


class CourseSearchForm(FlaskForm):
    course_name = StringField("Course: ")
    selected_user = StringField("Exercise: ")
    submit = SubmitField("Search", render_kw={"class": "btn btn-primary"})


class DownloadForm(FlaskForm):
    course = SelectField("Course: ")
    select = SubmitField("Select", render_kw={"class": "btn btn-primary"})
    exercise = SelectField("Exercise: ")
    submit = SubmitField("Download", render_kw={"class": "btn btn-primary"})


class UploadExerciseForm(FlaskForm):
    course = StringField("Course: ")
    exercise = FileField("Exercise: ")
    submit = SubmitField("Upload", render_kw={"class": "btn btn-primary"})

    def __init__(self, course_value=None, *args, **kwargs):
        super(UploadExerciseForm, self).__init__(*args, **kwargs)
        if course_value:
            self.course.data = course_value

    def allowed_file(self):
        exercise = self.exercise.data
        return (
            "." in exercise.filename
            and exercise.filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
        )

    def path_exists(self):
        upload_path = os.path.join(basedir, Config.UPLOAD_FOLDER, self.course.data)
        print(upload_path)
        return os.path.exists(upload_path)
