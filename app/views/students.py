import os
import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_security import verify_password
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import InputRequired, Length

from app.extensions import db
from app.forms import DownloadForm, UploadExerciseForm
from app.helpers import handle_download, process_download_form
from app.models import Course, Exercise, User
from config import Config, basedir


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

    if "student" in current_user.roles:
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

    elif "teacher" in current_user.roles:
        upload_form = UploadExerciseForm()

        # Get list of courses for the current user
        courses = current_user.courses

        upload_form.courses.choices = [(course, course) for course in courses]
        selected_course = None

        # If the user selects a course...
        if upload_form.select.data and upload_form.validate_on_submit():
            selected_course = upload_form.courses.data
            # ...store the selected course in the session
            session["selected_course"] = selected_course
            flash(f"Course {selected_course} selected.")
            return redirect(url_for("students.profile", username=current_user.username))

        # If a selected course is stored in the session...
        if "selected_course" in session:
            # 1) Retrieve the selected course from the session
            selected_course = session["selected_course"]

        if upload_form.submit.data and upload_form.validate_on_submit():
            upload_form.courses.data = str(selected_course)
            course_name = upload_form.courses.data
            number = upload_form.exercise.data

            if not (course_name and number):
                flash("Please fill out both the course and exercise fields.")

            elif not upload_form.path_exists():
                flash("Selected course does not exist.")

            elif not upload_form.allowed_file():
                flash(
                    "Selected file format is not allowed: please, use only .txt or .deb."
                )

            else:
                # Split the filename and its extension
                filename, extension = os.path.splitext(number.filename)

                # Save the file to the designated folder
                course = Course.query.filter_by(name=course_name).first()
                if not course:
                    flash(f"Course {course_name} does not exist.")
                    return redirect(
                        url_for("students.profile", username=current_user.username)
                    )

                course_folder = os.path.join(basedir, Config.UPLOAD_FOLDER, course_name)
                filepath = os.path.join(course_folder, secure_filename(number.filename))
                number.save(filepath)

                # Check if an exercise with the same number already exists for this course
                existing_exercise = Exercise.query.filter_by(
                    course=course, number=filename
                ).first()
                if existing_exercise:
                    # Update the existing exercise
                    existing_exercise.exercise_path = filepath
                    db.session.commit()
                    flash(
                        f'The exercise "{number.filename}" has been successfully uploaded for the course "{course_name}".'
                    )
                else:
                    # Store the exercise number info in the database
                    new_exercise = Exercise(
                        number=filename,
                        course=course,
                        exercise_path=filepath,
                    )
                    db.session.add(new_exercise)
                    db.session.commit()
                    flash(
                        f'The file "{number.filename}" has been uploaded into the folder'
                        f' "{basedir}/{Config.UPLOAD_FOLDER}/{course}/".'
                    )

                # Clear upload_form data after successful submission
                upload_form.courses.data = None
                upload_form.exercise.data = None

            return render_template(
                "students/profile.html",
                username=username,
                courses=courses,
                upload_form=upload_form,
            )
        else:
            return render_template(
                "students/profile.html",
                username=username,
                courses=courses,
                upload_form=upload_form,
            )


@students.route("/logout/", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("students.login"))
