from flask import Flask, flash, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import (
    UserMixin,
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import os
from dotenv import load_dotenv
from sqlalchemy_utils import UUIDType
import uuid
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo, Email
from flask_bcrypt import Bcrypt

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["FLASK_ADMIN_SWATCH"] = "cerulean"
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


class User(db.Model, UserMixin):
    __tablename__ = "user"
    user_id = db.Column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4, unique=True
    )
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    device = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    # role = db.Column pass # multiple roles
    # region_id = db.Column pass # multiple regions
    # devices = db.Column # Only for customers, just one device (one to one)

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute!")

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True

    def get_id(self):
        return str(self.user_id)


class RegisterForm(FlaskForm):
    username = StringField(
        validators=[
            InputRequired(),
            Length(min=4, max=20),
        ],
        render_kw={"placeholder": "Username"},
    )
    email = StringField(
        validators=[
            InputRequired(),
            Email(),
        ],
        render_kw={"placeholder": "Email"},
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

        existing_user_username = User.query.filter_by(username=field.data).first()
        if existing_user_username:
            raise ValidationError(
                "This username already exists. Please choose a different one."
            )


@app.route("/admin/user/new/", methods=["GET", "POST"])
def custom_register():
    # Redirect to your custom registration page
    return redirect(url_for("register"))


@app.route("/admin/user/register/", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            device=form.device.data,
            role=form.role.data,
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(
            url_for("admin.index", _external=True, _scheme="http") + "user/"
        )

    return render_template("registration/register.html", form=form)


class UserAdminView(ModelView):
    column_exclude_list = ["password_hash"]
    form_excluded_columns = ["password_hash"]


admin.add_view(UserAdminView(User, db.session))


# Flask_login stuff
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


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
        user = User.query.filter_by(username=form.username.data.lower()).first()
        if user:
            if bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Logged in successfully!")
                return redirect(url_for("user", username=user.username))
            else:
                flash("Wrong password - Try Again...")
        else:
            flash("This username does not exist - Try again...")
    return render_template("registration/login.html", form=form)


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
def page_not_found(e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template("errors/500.html"), 500
