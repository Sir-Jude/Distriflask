from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_login import LoginManager, current_user, login_user
import os
from dotenv import load_dotenv

# Import the libraries to use UUID (Universal Unique Identifier)
from sqlalchemy_utils import UUIDType
import uuid
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError


load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
db = SQLAlchemy(app)
admin = Admin(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4, unique=True
    )
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    # role = db.Column pass # multiple roles
    # region_id = db.Column pass # multiple regions
    # devices = db.Column # Only for customers, just one device (one to one)

@app.route("/")
@app.route("/home/", methods=["GET"])
def home_page():
    username = None
    if current_user.is_authenticated:
        username = current_user.username
    return render_template("welcome.html", username=username)

admin.add_view(ModelView(User, db.session))


class RegisterForm(FlaskForm):
    username = StringField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[InputRequired(), Length(min=8, max=20)],
        render_kw={"placeholder": "Password"},
    )
    submit = SubmitField("Register", render_kw={"class": "btn btn-primary"})
    
    def validate_username(self, field):
        existing_user_username = User.query.filter_by(username=field.data).first()
        if existing_user_username:
            raise ValidationError(
                "This username already exists. Please choose a different one."
            )


@app.route("/register/", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        new_user = User(username=form.username.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for ("login"))
    
    return render_template("registration/register.html", form=form)


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
    
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                "This username already exists. Please choose a different one."
            )

@app.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Assuming User.authenticate is a method that checks the username and password
        user = User.authenticate(username=form.username.data, password=form.password.data)

        if user:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to the dashboard or another page
        else:
            flash('Invalid username or password', 'danger')

    return render_template("registration/login.html", form=form)
    return render_template("registration/login.html", form=form)


@app.route("/user/<name>/")
def user(name):
    # To be substituted with a database...
    devices = ["device_1", "device_2", "device_3", "device_4", "..."]
    return render_template("user.html", username=name, devices=devices)
