from app.forms import DownloadForm
from app.models import User, Course, Exercise
from config import basedir, Config
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
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

    # Sort courses' name in "uploads" folder and populate the drop down menu
    courses = current_user.courses
    download_form.course.choices = [(course, course) for course in courses]

    exercises = []
    selected_course = None

    # If the user selects a course...
    if download_form.select.data:
        selected_course = download_form.course.data
        # ...store the selected course in the session
        session["selected_course"] = selected_course
        flash(f"Course {selected_course} selected.")

    # If a selected course is stored in the session...
    if "selected_course" in session:
        # 1) Retrieve the selected course from the session
        selected_course = session["selected_course"]
        # 2) Retrieve all exercises associated with the selected course and sort them by number
        exercises = sorted(
            Exercise.query.join(Course)
            .filter(Course.name == selected_course)
            .all(),
            key=lambda exr: tuple(
                int(part) if part.isdigit() else part
                for part in re.findall(r"\d+|\D+", exr.number)
            ),
            reverse=False,
        )
    # Populate the number choices in the form with the sorted numbers
    # (empty list [] as default)
    download_form.exercise.choices = [
        (exercise.number, exercise.number) for exercise in exercises
    ]

    # If the form is submitted to initiate a download and the form data is valid...
    if download_form.submit.data and download_form.validate_on_submit():
        selected_exercise = download_form.exercise.data
        # Retrieve the exercise corresponding to the selected number
        exercise = Exercise.query.filter_by(number=selected_exercise).first()
        number_path = exercise.exercise_path
        path = os.path.join(basedir, Config.UPLOAD_FOLDER, number_path)
        # Send the exercise file to the user as an attachment for download
        return send_file(path_or_file=path, as_attachment=True)
    
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
