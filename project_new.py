from flask import Flask, flash, render_template, redirect, url_for
from flask_security import (
    RoleMixin,
    UserMixin,
    Security,
    SQLAlchemyUserDatastore,
    current_user
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
from sqlalchemy_utils import UUIDType
import uuid
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo
from flask_bcrypt import Bcrypt

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["FLASK_ADMIN_SWATCH"] = "cerulean"
app.config['SECURITY_POST_LOGIN_VIEW'] = '/admin/'
app.config['SECURITY_POST_LOGOUT_VIEW'] = '/admin/'
app.config['SECURITY_POST_REGISTER_VIEW'] = '/admin/'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
admin = Admin(app, name="Admin", template_mode="bootstrap3")
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)


@app.route("/")
@app.route("/home/", methods=["GET"])
def home_page():
    """
    By initializing username as None, it ensures that the "username"
    variable exists even if the user isn't authenticated. This approach
    avoids potential errors that might arise if current_user.is_authenticated
    evaluates to False, and username hasn't been assigned a value yet.
    """
    username = None
    if current_user.is_authenticated:
        username = current_user.username
    return render_template("welcome.html", username=username)


roles_users_table = db.Table(
    'roles_users',
    db.Column('users_id', db.Integer(), 
    db.ForeignKey('users.user_id')),
    db.Column('roles_id', db.Integer(), 
    db.ForeignKey('roles.id'))
)


class Users(db.Model, UserMixin):
    __tablename__ = "users"
    user_id = db.Column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4, unique=True
    )
    username = db.Column(db.String(20), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    device = db.Column(db.String(200), nullable=True)
    active = db.Column(db.Boolean())
    role = db.relationship('Roles', secondary=roles_users_table, backref='user', lazy=True)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=True, name='unique_fs_uniquifier_constraint')


class Roles(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class RegisterForm(FlaskForm):
    username = StringField(
        validators=[
            InputRequired(),
            Length(min=4, max=20),
        ],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[
            InputRequired(),
            Length(min=8, max=20),
            EqualTo("password_2", message="Passwords must match!"),
        ],
        render_kw={"placeholder": "Password"},
    )
    password_2 = PasswordField(
        validators=[InputRequired()],
        render_kw={"placeholder": "Confirm Password"},
    )

    device = StringField(
        render_kw={"placeholder": "Device"},
    )

    active = BooleanField(
        render_kw={"placeholder": "Device"},
    )
    
    role = SelectField(
        choices=[("user", "User"), ("admin", "Admin")],
        validators=[
            InputRequired(),
        ],
        render_kw={"placeholder": "Role"},
    )
    submit = SubmitField("Register", render_kw={"class": "btn btn-primary"})

    def validate_username(self, field):
        field.data = field.data.lower()

        existing_user_username = Users.query.filter_by(username=field.data).first()
        if existing_user_username:
            raise ValidationError(
                "This username already exists. Please choose a different one."
            )


@app.route("/admin/users/new/", methods=["GET", "POST"])
def custom_register():
    # Redirect to your custom registration page
    return redirect(url_for("register"))


@app.route("/admin/users/register/", methods=["GET", "POST"])
def register():
    form = RegisterForm()

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
security = Security(app, user_datastore)


class UserAdminView(ModelView):
    column_exclude_list = ["password_hash", "fs_uniquifier"]
    def is_accessible(self):
        return (
            current_user.is_active and
            current_user.is_authenticated
        )

admin.add_view(UserAdminView(Users, db.session))

@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template = admin.base_template,
        admin_view = admin.index_view,
        h = admin_helpers,
        get_url = url_for
    )

# Flask_login stuff
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


class LoginForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[InputRequired(), Length(min=8, max=20)],
        render_kw={"placeholder": "Password"},
    )
    submit = SubmitField("Login", render_kw={"class": "btn btn-primary"})


@app.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data.lower()).first()
        if user:
            if bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Logged in successfully!")
                return redirect(url_for("user", username=user.username))
            else:
                flash("Wrong password - Try Again...")
        else:
            flash("This username does not exist - Try again...")
    return render_template("customers/login.html", form=form)


@app.route("/user/<username>/", methods=["GET", "POST"])
@login_required
def user(username):
    if current_user.username != username:
        return render_template("errors/403.html"), 403

    # To be substituted with a database...
    devices = current_user.device
    return render_template("user.html", username=username, devices=devices)


@app.route("/logout/", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()

    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("errors/500.html"), 500
