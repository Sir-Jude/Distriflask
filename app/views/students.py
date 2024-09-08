from app.forms import DownloadForm
from app.models import User
from app.helpers import process_download_form, handle_download
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_security import verify_password
from flask_wtf import FlaskForm
import re
import os
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import InputRequired, Length


class LoginForm(FlaskForm):
    username = StringField("Username", [InputRequired(), Length(min=4, max=20)])
    password = PasswordField("Password", [InputRequired(), Length(min=8, max=20)])
    submit = SubmitField("Login", render_kw={"class": "btn btn-primary"})


students = Blueprint("students", __name__)


@students.route("/home/")
@students.route("/")
def home():
    return render_template("students/home.html")


@students.route("/student_login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.is_active:
            if verify_password(form.password.data, user.password):
                login_user(user)
                flash("Logged in successfully.")
                next_page = request.args.get("next")
                if next_page == url_for("admin.index") and "administrator" in [
                    role.name for role in user.roles
                ]:
                    next_page = url_for("admin.index")
                elif next_page is None:
                    if "administrator" in [role.name for role in user.roles]:
                        next_page = url_for("admin.index")
                    else:
                        next_page = url_for("students.profile", username=user.username)
                return redirect(next_page)
            else:
                flash("Wrong password - Try Again...")
        else:
            flash("Specified user does not exist")
    return render_template("students/login.html", form=form)


@students.route("/student/<username>/", methods=["GET", "POST"])
@login_required
def profile(username):
    # Return 403 error if current user is not accessing their own profile
    if current_user.username != username:
        return render_template("errors/403.html"), 403

    download_form = DownloadForm()

    # Get list of courses for the current user
    courses = current_user.courses
    
    # Handle file download if the form is submitted and valid
    exercises = process_download_form(download_form, courses)
    
    # Handle file download if the form is submitted and valid
    file_response = handle_download(download_form)
    
    if file_response:
        return file_response

    
    return render_template(
        "students/profile.html",
        username=username,
        courses=courses,
        exercises=exercises,
        download_form=download_form,
    )


@students.route("/logout/", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("students.login"))
