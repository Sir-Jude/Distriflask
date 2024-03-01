from app.extensions import db
from app.models import User, Device, Release
from config import Config
from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_security import verify_password
from flask_wtf import FlaskForm
import os
import re
from wtforms import PasswordField, StringField, SubmitField
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
        user = User.query.filter_by(username=form.email.data).first()
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

    device = current_user.devices
    country = None  # Initialize country to None initially
    if device:  # Check if User has an associated device
        country = device.country_id
        releases = sorted(
            Release.query.join(Device).filter(Device.name == str(device)).all(),
            key=lambda r: tuple(
                int(part) if part.isdigit() else part
                for part in re.findall(r"\d+|\D+", r.version)
            ),
            reverse=True,
        )
    else:
        releases = []  # If device is not available, set releases to an empty list

    return render_template(
        "customers/profile.html",
        username=username,
        device=device,
        country=country,
        releases=releases,
    )


@customers.route("/devices/<path:rel_path>", methods=['GET', 'POST'])
def download_release(rel_path):
    # Get the selected release version from the form
    release_id = request.form['release']
    
    # Query the database to get the Release object
    release = Release.query.get(release_id)
    
    # Check if the release exists and is visible
    if release and release.flag_visible:
        # Construct the full path to the release file
        release_file_path = os.path.join(Config.UPLOAD_FOLDER, release.release_path)
        # Serve the file for download
        return send_from_directory(Config.UPLOAD_FOLDER, release.release_path, as_attachment=True)
    

@customers.route("/logout/", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("customers.login"))
