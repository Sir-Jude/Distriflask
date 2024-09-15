from app.extensions import db
from app.forms import UploadExerciseForm
from app.models import Course, Exercise
from flask import flash, session, send_file
from config import basedir, Config
from werkzeug.utils import secure_filename
import os
import re


def process_download_form(download_form, courses):
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
            Exercise.query.join(Course).filter(Course.name == selected_course).all(),
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

    return exercises


def handle_download(download_form):

    # If the form is submitted to initiate a download and the form data is valid...
    if download_form.submit.data and download_form.validate_on_submit():
        selected_exercise = download_form.exercise.data
        # Retrieve the exercise corresponding to the selected number
        exercise = Exercise.query.filter_by(number=selected_exercise).first()
        number_path = exercise.exercise_path
        path = os.path.join(basedir, Config.UPLOAD_FOLDER, number_path)
        # Send the exercise file to the user as an attachment for download
        return send_file(path_or_file=path, as_attachment=True)

    return None


def handle_course_selection(upload_form):
    selected_course = upload_form.courses.data
    # Store the selected course in the session
    session["selected_course"] = selected_course
    flash(f"Course {selected_course} selected.")


def validate_upload_form(upload_form):
    """Validate the upload form and handle errors."""
    course_name = upload_form.courses.data
    number = upload_form.exercise.data

    if not (course_name and number):
        flash("Please fill out both the course and exercise fields.")
        return False

    elif not upload_form.path_exists():
        flash("Selected course does not exist.")
        return False

    elif not upload_form.allowed_file():
        flash("Selected file format is not allowed: please, use only .txt or .deb.")
        return False

    return True


def save_exercise_file(upload_form, course_name, number):
    """Save the uploaded file to the course folder and update the database."""
    filename, extension = os.path.splitext(number.filename)
    course = Course.query.filter_by(name=course_name).first()

    if not course:
        flash(f"Course {course_name} does not exist.")
        return False

    course_folder = os.path.join(basedir, Config.UPLOAD_FOLDER, course_name)
    filepath = os.path.join(course_folder, secure_filename(number.filename))
    number.save(filepath)

    # Check if an exercise with the same number already exists
    existing_exercise = Exercise.query.filter_by(course=course, number=filename).first()

    if existing_exercise:
        existing_exercise.exercise_path = filepath
        db.session.commit()
        flash(
            f'The exercise "{number.filename}" has been successfully uploaded for the course "{course_name}".'
        )
    else:
        new_exercise = Exercise(number=filename, course=course, exercise_path=filepath)
        db.session.add(new_exercise)
        db.session.commit()
        flash(
            f'The file "{number.filename}" has been uploaded into the folder "{basedir}/{Config.UPLOAD_FOLDER}/{course_name}/".'
        )
    
    # Clear upload_form data after successful submission
    upload_form.courses.data = None
    upload_form.exercise.data = None

    return True
