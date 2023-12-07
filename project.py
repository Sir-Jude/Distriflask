from flask import Flask, flash, redirect, render_template, url_for

# Imports for Flask security
from flask_security import (
    current_user,
    lookup_identity,
    LoginForm,
    RegisterForm,
    Security,
    SQLAlchemyUserDatastore,
    uia_username_mapper,
    unique_identity_attribute
)

# Imports for Flask login
from flask_login import LoginManager, logout_user, login_required


from flask_migrate import Migrate

# Imports for Admin page
from flask_admin import BaseView, expose, Admin, helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView

# Imports for .env file
import os
from dotenv import load_dotenv


from werkzeug.local import LocalProxy

# Imports for WTF
from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo

# Imports from otehr files
from models import db, Users, Roles
from errors import register_error_handlers
from views.customers import customers

# Imports for bcrypt
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


load_dotenv()


app = Flask(__name__)
app.register_blueprint(customers)
register_error_handlers(app)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SECURITY_PASSWORD_SALT"] = os.getenv("SECURITY_PASSWORD_SALT")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db_1.sqlite3"
app.config["FLASK_ADMIN_SWATCH"] = "cerulean"
app.config["SECURITY_POST_LOGIN_VIEW"] = "/admin/"
app.config['SECURITY_POST_LOGOUT_VIEW'] = '/admin/'
app.config["SECURITY_POST_REGISTER_VIEW"] = "/admin/users/"
app.config["SECURITY_REGISTERABLE"] = True


admin = Admin(
    app, name="Admin", base_template="master.html", template_mode="bootstrap3"
)
db.init_app(app)
migrate = Migrate(app, db)


def username_validator(form, field):
    # Side-effect - field.data is updated to normalized value.
    # Use proxy to we can declare this prior to initializing Security.
    _security = LocalProxy(lambda: app.extensions["security"])
    msg, field.data = _security._username_util.validate(field.data)
    if msg:
        raise ValidationError(msg)


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


app.config["SECURITY_USER_IDENTITY_ATTRIBUTES"] = (
    {"username": {"mapper": uia_username_mapper, "case_insensitive": True}},
)


class ExtendedRegisterForm(RegisterForm):
    email = StringField(
        "Username", [InputRequired(), username_validator, unique_identity_attribute]
    )
    password = PasswordField("Password", [InputRequired(), Length(min=8, max=20)])
    device = StringField("Device")
    active = BooleanField("Active")
    role = SelectField(
        "Role",
        choices=[
            ("customer", "Customer"),
            ("administration", "Administration"),
            ("sales", "Sales"),
            ("production", "Production"),
            ("application", "Application"),
            ("software", "Software"),  
        ],
        validators=[InputRequired()],
    )
    
    def validate(self, **kwargs):
        self.user = lookup_identity(self.email.data)
        # Setting 'ifield' informs the default login form validation
        # handler that the identity has already been confirmed.
        self.ifield = self.email
        if not super().validate(**kwargs):
            return False
        return True
    
    
    
@app.route("/admin/users/new/", methods=["GET", "POST"])
def register():
    form = ExtendedRegisterForm()

    if form.validate_on_submit():
        new_user = Users(
            username=form.username.data,
            password=form.password.data,
            device=form.device.data,
            active=form.active.data,
            role=form.role.data,
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(
            url_for("admin.index", _external=True, _scheme="http") + "users/"
        )

    return render_template("security/register_user.html", form=form)


user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
security = Security(
    app,
    user_datastore,
    register_form=ExtendedRegisterForm,
    login_form=ExtendedLoginForm,
)


@app.before_request
def create_user():
    existing_user = user_datastore.find_user(username="admin")
    if not existing_user:
        first_user = user_datastore.create_user(username="admin", password="12345678")
        user_datastore.activate_user(first_user)
        db.session.commit()


class UserAdminView(ModelView):
    column_exclude_list = ["fs_uniquifier", "password"]

    def is_accessible(self):
        return current_user.is_active and current_user.is_authenticated

    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for("security.login"))


admin.add_view(UserAdminView(Users, db.session))


@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for,
    )
    
@security.register_context_processor
def security_register_processor():
    return dict(register_user_form=ExtendedRegisterForm)


# Flask_login stuff
login_manager = LoginManager()
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)





