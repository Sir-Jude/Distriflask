from app.forms import StudentdownloadForm
from app.models import User, Course, Exercise
from config import basedir, Config
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
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

    course = current_user.courses

    # set exercises to an empty list
    exercises = []
    if course:  # If user has an associated course, fetch exercises
        exercises = sorted(
            Exercise.query.join(Course).filter(Course.name == str(course)).all(),
            key=lambda exr: tuple(
                int(part) if part.isdigit() else part
                for part in re.findall(r"\d+|\D+", exr.number)
            ),
            reverse=False,
        )

    form = StudentdownloadForm(formdata=request.form)
    # Populate the choices for exercise numbers in the form
    form.exercise_number.choices = [
        # (value submitted to the form, text displayed to the user)
        (exercise.number, exercise.number)
        for exercise in exercises
    ]

    if form.validate_on_submit():
        exercise_number = form.exercise_number.data
        exercise = Exercise.query.filter_by(number=exercise_number).first()

        if exercise:
            number = exercise.exercise_path
            return redirect(url_for("students.download_number", number=number))
        else:
            flash("Exercise not found.", "error")

    return render_template(
        "students/profile.html",
        username=username,
        course=course,
        exercises=exercises,
        form=form,
    )


@students.route("/course/<path:number>", methods=["GET", "POST"])
@login_required
def download_number(number):
    exercise = Exercise.query.filter_by(exercise_path=number).first()

    number = exercise.exercise_path
    path = os.path.join(basedir, Config.UPLOAD_FOLDER, number)
    return send_file(path_or_file=path, as_attachment=True)


@students.route("/logout/", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("students.login"))
