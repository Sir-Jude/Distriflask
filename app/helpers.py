from app.models import Course, Exercise
from flask import flash, session, send_file
from config import basedir, Config
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