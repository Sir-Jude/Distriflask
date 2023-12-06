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
)


# Imports for Flask login
from flask_login import LoginManager, logout_user, login_required


from flask_migrate import Migrate

# Imports for Admin page
from flask_admin import Admin, helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView

# Imports for .env file
import os
from dotenv import load_dotenv


from werkzeug.local import LocalProxy

# Imports for WTF
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo

# Imports from otehr files
from models import db, Users, Roles
from errors import register_error_handlers
from routes_customers import routes_customers

# Imports for bcrypt
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


load_dotenv()


app = Flask(__name__)
app.register_blueprint(routes_customers)

app.config["SECURITY_USER_IDENTITY_ATTRIBUTES"] = {
    "username": {"mapper": uia_username_mapper, "case_insensitive": True}
}
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SECURITY_PASSWORD_SALT"] = os.getenv("SECURITY_PASSWORD_SALT")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db_1.sqlite3"
app.config["FLASK_ADMIN_SWATCH"] = "cerulean"
app.config["SECURITY_POST_LOGIN_VIEW"] = "/admin/"
# app.config['SECURITY_POST_LOGOUT_VIEW'] = '/admin/'
app.config["SECURITY_POST_REGISTER_VIEW"] = "/admin/"
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


register_error_handlers(app)


class ExtendedRegisterForm(RegisterForm):
    # # BUG: This code is completely useless and is not seen at all!!!
    # email = StringField(
    #     "Username", [InputRequired(), username_validator, unique_identity_attribute]
    # )
    # password = PasswordField("Password", [InputRequired(), Length(min=8, max=20)])
    # device = StringField("Device")
    # active = BooleanField("Active")
    # role = SelectField(
    #     "Role",
    #     choices=[("user", "User"), ("admin", "Admin")],
    #     validators=[InputRequired()],
    # )
    pass


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
    column_exclude_list = ["fs_uniquifier"]

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


# Flask_login stuff
login_manager = LoginManager()
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


@app.route("/user/<username>/", methods=["GET", "POST"])
@login_required
def user(username):
    if current_user.username != username:
        return render_template("errors/403.html"), 403

    # To be substituted with a database...
    devices = current_user.device
    return render_template(
        "customers/customer_view.html", username=username, devices=devices
    )


@app.route("/logout/", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("routes_customers.customer_login"))
