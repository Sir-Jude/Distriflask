# Imports for WTF
from flask import current_app
from wtforms import BooleanField, StringField, PasswordField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError

from flask_security import (
    RegisterForm,
    LoginForm,
    unique_identity_attribute,
    lookup_identity,
)

from werkzeug.local import LocalProxy


def username_validator(form, field):
    # Side-effect - field.data is updated to normalized value.
    # Use proxy to we can declare this prior to initializing Security.
    _security = LocalProxy(lambda: current_app.extensions["security"])
    msg, field.data = _security._username_util.validate(field.data)
    if msg:
        raise ValidationError(msg)


class ExtendedRegisterForm(RegisterForm):
    email = StringField(
        "Username", [InputRequired(), username_validator, unique_identity_attribute]
    )
    password = PasswordField("Password", [InputRequired(), Length(min=8, max=20)])
    devices = StringField("Devices")
    active = BooleanField("Active")
    role = SelectField(
        "Role",
        choices=[
            ("customer"),
            ("administrator"),
            ("sales"),
            ("production"),
            ("application"),
            ("software"),
        ],
        validators=[InputRequired()],
    )


class ExtendedLoginForm(LoginForm):
    email = StringField("Username", [InputRequired()])

    def validate(self, **kwargs):
        self.user = lookup_identity(self.email.data)
        # Setting 'ifield' informs the default login form validation
        # handler that the identity has already been confirmed.
        self.ifield = self.email
        if not super().validate(**kwargs):
            return False
        return True
