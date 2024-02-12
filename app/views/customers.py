import re
from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_user, login_required, current_user, logout_user
from flask_security import verify_password
from app.models import Users
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length


class LoginForm(FlaskForm):
    email = StringField("Username", [InputRequired(), Length(min=4, max=20)])
    password = PasswordField("Password", [InputRequired(), Length(min=8, max=20)])
    submit = SubmitField("Login", render_kw={"class": "btn btn-primary"})


customers = Blueprint("customers", __name__)


@customers.route("/home")
@customers.route("/")
def home():
    return render_template("home/home.html")


@customers.route("/customer_login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.email.data).first()
        if user and user.is_active:
            if verify_password(form.password.data, user.password):
                login_user(user)
                flash("Logged in successfully!")
                """
                IMPORTANT!!!
                The documentation advises to add this snippet:
                
                next = flask.request.args.get('next')
                # url_has_allowed_host_and_scheme should check if the url is safe
                # for redirects, meaning it matches the request host.
                # See Django's url_has_allowed_host_and_scheme for an example.
                if not url_has_allowed_host_and_scheme(next, request.host):
                    return flask.abort(400)
                return redirect(next or url_for("user", username=user.username))
                
                Otherwise the application will be vulnerable to open redirects
                INFO: flask-login.readthedocs.io/en/latest/#login-example
                """
                return redirect(url_for("customers.profile", username=user.username))
            else:
                flash("Wrong password - Try Again...")
        else:
            flash("Invalid username")
    return render_template("customers/login.html", form=form)


@customers.route("/customer/<username>/", methods=["GET", "POST"])
@login_required
def profile(username):
    if current_user.username != username:
        return render_template("errors/403.html"), 403

    # To be substituted with a database...
    devices = current_user.devices
    return render_template("customers/profile.html", username=username, devices=devices)


@customers.route("/logout/", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("customers.login"))
