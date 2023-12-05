from flask import Flask, flash, render_template, redirect, url_for
from flask_security import (
    current_user,
    lookup_identity,
    LoginForm,
    RegisterForm,
    RoleMixin,
    Security,
    SQLAlchemyUserDatastore,
    uia_username_mapper,
    unique_identity_attribute,
    UserMixin,
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin, helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
)
import os
from dotenv import load_dotenv
from routes import routes
import uuid
from sqlalchemy_utils import UUIDType
from werkzeug.local import LocalProxy
from wtforms import BooleanField, StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt


load_dotenv()


app = Flask(__name__)
app.register_blueprint(routes)
app.config["SECURITY_USER_IDENTITY_ATTRIBUTES"] = ({"username": {"mapper": uia_username_mapper, "case_insensitive": True}})
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SECURITY_PASSWORD_SALT"] = os.getenv("SECURITY_PASSWORD_SALT")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db_1.sqlite3"
app.config["FLASK_ADMIN_SWATCH"] = "cerulean"
app.config["SECURITY_POST_LOGIN_VIEW"] = "/admin/"
# app.config['SECURITY_POST_LOGOUT_VIEW'] = '/admin/'
app.config["SECURITY_POST_REGISTER_VIEW"] = "/admin/"
app.config["SECURITY_REGISTERABLE"] = True
admin = Admin(
    app, name="Admin", base_template="my_master.html", template_mode="bootstrap3"
)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)


def username_validator(form, field):
    # Side-effect - field.data is updated to normalized value.
    # Use proxy to we can declare this prior to initializing Security.
    _security = LocalProxy(lambda: app.extensions["security"])
    msg, field.data = _security._username_util.validate(field.data)
    if msg:
        raise ValidationError(msg)


@app.route("/")
def home_page():
    pass


roles_users_table = db.Table(
    "roles_users",
    db.Column("users_id", db.Integer(), db.ForeignKey("users.user_id")),
    db.Column("roles_id", db.Integer(), db.ForeignKey("roles.id")),
)


class Users(db.Model, UserMixin):
    user_id = db.Column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4, unique=True
    )
    username = db.Column(db.String(100), unique=True, index=True)
    password = db.Column(db.String(80))
    device = db.Column(db.String(200), nullable=True)
    active = db.Column(db.Boolean())
    roles = db.relationship(
        "Roles", secondary=roles_users_table, backref="users", lazy=True
    )
    fs_uniquifier = db.Column(
        db.String(64),
        unique=True,
        nullable=True,
        name="unique_fs_uniquifier_constraint",
    )


class Roles(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


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


@app.route("/admin/users/register", methods=["GET", "POST"])
def register():
    form = ExtendedRegisterForm(RegisterForm)

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


@app.before_request
def create_user():
    existing_user = user_datastore.find_user(username="admin")
    if not existing_user:
        first_user = user_datastore.create_user(username="admin", password="12345678")
        user_datastore.activate_user(first_user)
        db.session.commit()


class UserAdminView(ModelView):
    column_exclude_list = ["password", "fs_uniquifier"]

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


# # Flask_login stuff
# login_manager = LoginManager(app)
# login_manager.login_view = "login"


# @login_manager.user_loader
# def load_user(user_id):
#     return Users.query.get(user_id)


# class LoginForm(FlaskForm):
#     email = StringField(
#         validators=[InputRequired(), Length(min=4, max=20)],
#         render_kw={"placeholder": "Username"},
#     )
#     password = PasswordField(
#         validators=[InputRequired(), Length(min=8, max=20)],
#         render_kw={"placeholder": "Password"},
#     )
#     submit = SubmitField("Login", render_kw={"class": "btn btn-primary"})


# @app.route("/login", methods=["GET", "POST"])
# def login():
#     form = ExtendedLoginForm()
#     if form.validate_on_submit():
#         user = Users.query.filter_by(username=form.username.data.lower()).first()
#         if user:
#             if bcrypt.check_password(user.password, form.password.data):
#                 login_user(user)
#                 flash("Logged in successfully!")
#                 return redirect(url_for("user", username=user.username))
#             else:
#                 flash("Wrong password - Try Again...")
#         else:
#             flash("This username does not exist - Try again...")
#     return render_template("security/login_user.html", form=form)


# @app.route("/user/<username>/", methods=["GET", "POST"])
# @login_required
# def user(username):
#     if current_user.username != username:
#         return render_template("errors/403.html"), 403

#     # To be substituted with a database...
#     devices = current_user.device
#     return render_template("user.html", username=username, devices=devices)


# @app.route("/logout/", methods=["GET", "POST"])
# @login_required
# def logout():
#     logout_user()

#     flash("You have been logged out.")
#     return redirect(url_for("security/login_user.html"))


@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("errors/500.html"), 500
