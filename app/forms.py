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
    device = QuerySelectField(
        "Course",
        query_factory=lambda: Course.query.order_by(func.lower(Course.name)).all(),
        get_label="name",
        allow_blank=True,
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
        self.user = lookup_identity(self.username.data.lower())
        # Setting 'ifield' informs the default login form validation
        # handler that the identity has already been confirmed.
        self.ifield = self.username
        if not super().validate(**kwargs):
            return False
        return True


class CourseSearchForm(FlaskForm):
    course_name = StringField("Course: ")
    selected_release_version = StringField("Exercise: ")
    submit = SubmitField("Search", render_kw={"class": "btn btn-primary"})


class CustomerDownloadForm(FlaskForm):
    release_version = SelectField("Version: ")
    submit = SubmitField("Download", render_kw={"class": "btn btn-primary"})


class AdminDownloadForm(FlaskForm):
    device = SelectField("Course: ")
    select = SubmitField("Select", render_kw={"class": "btn btn-primary"})
    version = SelectField("Version: ")
    submit = SubmitField("Download", render_kw={"class": "btn btn-primary"})


class UploadExerciseForm(FlaskForm):
    device = StringField("Course: ")
    version = FileField("Version: ")
    submit = SubmitField("Upload", render_kw={"class": "btn btn-primary"})

    def __init__(self, course_value=None, *args, **kwargs):
        super(UploadExerciseForm, self).__init__(*args, **kwargs)
        if course_value:
            self.device.data = course_value

    def allowed_file(self):
        version = self.version.data
        return (
            "." in version.filename
            and version.filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
        )

    def path_exists(self):
        upload_path = os.path.join(basedir, Config.UPLOAD_FOLDER, self.device.data)
        print(upload_path)
        return os.path.exists(upload_path)
