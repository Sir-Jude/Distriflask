from flask import Flask, flash, render_template, redirect, url_for
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from models import db, Users, Roles
from wtforms import BooleanField, StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo


bcrypt = Bcrypt()

# Flask_login stuff
login_manager = LoginManager()
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


class LoginForm(FlaskForm):
    email = StringField(
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[InputRequired(), Length(min=8, max=20)],
        render_kw={"placeholder": "Password"},
    )
    submit = SubmitField("Login", render_kw={"class": "btn btn-primary"})


@app.route("/admin/users/new", methods=["GET", "POST"])
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


@app.route("/login", methods=["GET", "POST"])
def login():
    form = ExtendedLoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data.lower()).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Logged in successfully!")
                return redirect(url_for("user", username=user.username))
            else:
                flash("Wrong password - Try Again...")
        else:
            flash("This username does not exist - Try again...")
    return render_template("security/login_user.html", form=form)


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
    return redirect(url_for("security/login_user.html"))


# <li><h6>Logged in as: {{ current_user.username.capitalize() }}</h6></li>