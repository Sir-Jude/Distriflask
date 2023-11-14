# Issues:
# - Move the button "Register" from the normal homepage to the admin homepage
# - After i have register a new user, I want to be redirect to the list of users in admin, not the admin dashboard.


from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
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
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from sqlalchemy_utils import UUIDType
import uuid
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, DataRequired, EqualTo
from flask_migrate import Migrate


load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
db = SQLAlchemy(app)
migrate = Migrate(app, db)
admin = Admin(app)
login_manager = LoginManager(app)


@app.route("/")
@app.route("/home/", methods=["GET"])
def home_page():
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
    password_hash = db.Column(db.String(200), nullable=False)
    # role = db.Column pass # multiple roles
    # region_id = db.Column pass # multiple regions
    # devices = db.Column # Only for customers, just one device (one to one)

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute!")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def authenticate(username, password):
        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            return user
        return None

    def get_id(self):
        return str(self.user_id)


class UserAdminView(ModelView):
    column_list = ("username", "password_hash")  # Exclude 'user_id' from the list view
    form_excluded_columns = ("user_id",)  # Exclude 'user_id' from the detail view
    column_formatters = {
        "password_hash": lambda v, c, m, p: "●●●●●●●●" if m.password_hash else ""
    }

    def scaffold_form(self):
        form_class = super(UserAdminView, self).scaffold_form()
        form_class.password = PasswordField(
            "Password",
            [
                DataRequired(),
                EqualTo("password_confirm", message="Passwords must match"),
            ],
        )
        form_class.password_confirm = PasswordField("Confirm Password")
        return form_class

    def on_model_change(self, form, model, is_created):
        if "password" in form.data and "password_confirm" in form.data:
            if form.data["password"] == form.data["password_confirm"]:
                if form.data["password"]:
                    model.password = form.data["password"]

        super(UserAdminView, self).on_model_change(form, model, is_created)


admin.add_view(UserAdminView(User, db.session))


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
        user = User.authenticate(
            username=form.username.data, password=form.password.data
        )

        if user:
            login_user(user)
            return redirect(url_for("user", username=form.username.data))

    return render_template("registration/login.html", form=form)


@app.route("/user/<username>/")
def user(username):
    # To be substituted with a database...
    devices = ["device_1", "device_2", "device_3", "device_4", "..."]
    return render_template("user.html", username=username, devices=devices)


@app.route("/logout/", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template("errors/500.html"), 500
