from app.extensions import db
from app.forms import (
    DownloadForm,
    CourseSearchForm,
    ExtendedRegisterForm,
    UploadExerciseForm,
)
from app.models import User, Course, Exercise
from config import basedir, Config
from flask import flash, redirect, request, send_file, session, url_for
from flask_login import login_required
from flask_security import current_user, hash_password, roles_required
from flask_admin.base import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from werkzeug.utils import secure_filename
import os
import re


class UserAdminView(ModelView):
    # Customized from BaseView
    def is_accessible(self):
        return (
            current_user.is_active
            and current_user.is_authenticated
            and any(role.name == "administrator" for role in current_user.roles)
        )

    # Customized from BaseView
    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for("security.login"))

    @staticmethod
    def _display_roles(view, context, model, name):
        return ", ".join([role.name.capitalize() for role in model.roles])

    @staticmethod
    def _display_courses(view, context, model, name):
        return ", ".join([course.name.capitalize() for course in model.courses])

    # Attribute of the ModelView class
    # Customize the display of the columns
    column_formatters = {"Courses": _display_courses, "roles": _display_roles}

    form = ExtendedRegisterForm

    # Customized from BaseModelView
    def on_model_change(self, form, model, is_created):
        # Check if the model being changed is a User model and the current user is an administrator
        if isinstance(model, User) and "administrator" in [role.name for role in current_user.roles]:
            # Check if password field is present in the form and has a value
            if "password" in form and form.password.data:
                # Hash the password before saving it to the database
                model.password = hash_password(form.password.data)

    # Actual columns' title as seen in the website
    column_list = ("username", "Courses", "active", "roles")

    # Link the columns' title and the model class attribute, so to make data sortable
    column_sortable_list = (
        "username",
        ("Courses", "courses.name"),
        "active",
        ("roles", "roles.name"),
    )


class CourseAdminView(BaseView):
    # This decorator exposes the method to be reachable via a specific URL route.
    @expose("/")
    # The "index" func serves as entry point for this particular app's section
    def index(self):
        return redirect(url_for("course_admin.courses_default_table"))

    @expose("/admin/course/", methods=["GET", "POST"])
    @login_required
    @roles_required("administrator")
    def courses_default_table(self):
        search_form = CourseSearchForm()

        if search_form.validate_on_submit():
            course_name = search_form.course_name.data
            selected_exercise = search_form.selected_exercise.data

            if course_name and selected_exercise:
                flash("Please provide only one search criteria at a time.", "error")
                return redirect(url_for("course_admin.courses_default_table"))

            # Resulting table of the Exercise search
            if selected_exercise:
                # Redirect to the new route for selected_exercise filtering
                return redirect(
                    url_for(
                        "course_admin.selected_exercise",
                        selected_exercise=selected_exercise,
                    )
                )

            # Resulting table of the Course search
            elif course_name:
                # Redirect to the new route for course_name filtering
                return redirect(
                    url_for(
                        "course_admin.selected_course_name", course_name=course_name
                    )
                )

            else:
                flash("Please, provide at least one search criteria.", "error")
                return redirect(url_for("course_admin.courses_default_table"))

        # Default table
        else:
            all_exercises = sorted(
                Exercise.query.all(),
                key=lambda x: tuple(
                    int(part) if part.isdigit() else part
                    for part in re.findall(r"\d+|\D+", x.number)
                ),
            )
            # The three following variables will always return the most updated number
            # (no matter which numbers are used)
            first_number = str(
                max(int(exercise.number.split(".")[0]) for exercise in all_exercises)
            )

            second_number = str(
                max(
                    int(exercise.number.split(".")[1])
                    for exercise in all_exercises
                    if exercise.number.startswith(first_number + ".")
                )
            )

            # Now, we'll use a custom sorting key for the third part
            # (since it might contain not just numbers, but also letters)
            third_number = [
                (
                    int(part) if part.isdigit() else part
                    for part in exercise.number.split(".")[2]
                )
                for exercise in all_exercises
                if exercise.number.startswith(first_number + "." + second_number + ".")
            ]

            # Flatten the list of generator (iterables) and then find the maximum
            # (flatten = convert a list of list into a single list)
            # (generator = special type of iterator that generates values on-the-fly)
            # (contrary to list, which store their elements in memory at once)
            third_number = str(
                max(
                    [part for generator in third_number for part in generator],
                    key=lambda x: (int(x) if isinstance(x, int) else x),
                )
            )

            return redirect(
                url_for(
                    "course_admin.selected_exercise",
                    selected_exercise=f"{first_number}.{second_number}.{third_number}",
                )
            )

    @expose("/students-table/<selected_exercise>", methods=["GET", "POST"])
    @login_required
    @roles_required("administrator")
    def selected_exercise(self, selected_exercise):
        search_form = CourseSearchForm()

        parts = selected_exercise.split(".")

        # Filter exercises based on first two numbers of selected_exercise in the URL
        if len(parts) < 2:
            flash("Invalid exercise number.", "error")
            return redirect(url_for("course_admin.courses_default_table"))

        filtered_exercises = Exercise.query.filter(
            Exercise.number.like(f"{parts[0]}.{parts[1]}%")
        ).all()

        # Redirect to the default if there is any matching exercise
        if not filtered_exercises:
            flash("No exercises found for the provided number.", "error")
            return redirect(url_for("course_admin.courses_default_table"))

        # Get all unique exercises matching the provided number
        all_exercises = sorted(
            set([exercise.number for exercise in filtered_exercises]),
            key=lambda x: tuple(
                int(part) if part.isdigit() else part
                for part in re.findall(r"\d+|\D+", x)
            ),
            reverse=False,
        )

        # Check if the provided exercise number exists in the list of all exercises
        if len(parts) == 2:
            selected_exercise = all_exercises[0]

        # Redirect to the default if there is any matching exercise
        if not all_exercises:
            flash("No exercises found for the provided number.", "error")
            return redirect(url_for("course_admin.courses_default_table"))

        # Check if the provided exercise number exists in the list of all exercises
        elif selected_exercise not in all_exercises:
            flash("Selected exercise number not found.", "error")
            return redirect(url_for("course_admin.courses_default_table"))

        check_existence = Exercise.query.filter_by(number=selected_exercise).first()

        # Check if there are any filtered exercises
        if check_existence:
            exercise_number = "".join(
                [
                    str(part)
                    for part in list(
                        int(part) if part.isdigit() else part
                        for part in re.findall(r"\d+|\D+", selected_exercise)
                    )[:3]
                ]
            )

            # Extract courses associated with the filtered student
            courses_with_matching_students = [
                exercise.course for exercise in filtered_exercises
            ]

            # Query courses that have exercises matching the provided number
            courses_in_rows = Course.query.filter(
                Course.exercises.any(Exercise.number.like(f"{exercise_number}%"))
            ).all()

            # Find the index of the selected exercise number in the list of all exercises.
            index = all_exercises.index(selected_exercise)

            # Define a variable to store set number of newer/older exercises
            halfwith = 10

            # Initialize lists to store newer and older exercises.
            newer = []
            older = all_exercises[index + 1 : index + halfwith + 1]

            # Check if there are fewer than 10 exercises before the selected one.
            if index - halfwith < 0:
                # If yes, include exercises from beginning up to selected one.
                newer = all_exercises[:index]
            else:
                # Otherwise, include the 10 exercises before the selected one.
                newer = all_exercises[index - halfwith : index]

            # Reorder all exercises to have newer : selected :older
            exercises = newer + [all_exercises[index]] + older

            # Check if there are more exercises after the selected one.
            if (index + halfwith + 1) < len(all_exercises):
                # If yes, add ellipsis to indicate more exercises.
                exercises = exercises + ["..."]

            # Check if there are more exercises before the selected one.
            if (index - halfwith) > 0:
                exercises = ["..."] + exercises

            all_exercise_numbers = {
                course: [
                    exercise.number
                    for exercise in course.exercises
                    if exercise.number in all_exercises
                ]
                for course in courses_with_matching_students
            }

            # Sort courses by name
            courses_in_rows = sorted(
                courses_in_rows, key=lambda x: x.name, reverse=False
            )

            return self.render(
                "admin/matrix_exercise.html",
                courses_in_rows=courses_in_rows,
                all_exercise_numbers=all_exercise_numbers,
                exercises=exercises,
                selected_exercise=selected_exercise,
                search_form=search_form,
            )
        else:
            flash("No exercise found.", "error")
            # Redirect to the default courses table
            return redirect(url_for("course_admin.courses_default_table"))

    @expose("/course/<course_name>", methods=["GET", "POST"])
    @login_required
    @roles_required("administrator")
    def selected_course_name(self, course_name):
        search_form = CourseSearchForm()
        all_courses = sorted(Course.query.all(), key=lambda d: d.name, reverse=False)
        all_exercises = {
            course: sorted(
                [e.number for e in course.exercises],
                key=lambda x: tuple(
                    int(part) if part.isdigit() else part
                    for part in re.findall(r"\d+|\D+", x)
                ),
                reverse=False,
            )
            for course in all_courses
        }
        filtered_course = Course.query.filter_by(name=course_name).first()
        if filtered_course:
            return self.render(
                "admin/matrix_course.html",
                courses=[filtered_course],
                all_exercises=all_exercises,
                search_form=search_form,
            )
        else:
            flash("No courses found.", "error")
            return redirect(url_for("course_admin.courses_default_table"))

    def is_accessible(self):
        return (
            current_user.is_active
            and current_user.is_authenticated
            and any(role.name == "administrator" for role in current_user.roles)
        )

    def _handle_view(self, name, **kwargs):
        # Adjust _handle_view to accept additional arguments
        if name == "selected_exercise":
            # Extract 'selected_exercise' from kwargs
            selected_exercise = kwargs.pop("selected_exercise", None)
            if selected_exercise:
                # Call the relevant view method with the extracted argument
                return getattr(self, name)(selected_exercise)
        return super()._handle_view(name, **kwargs)


class UploadAdminView(BaseView):
    @expose("/")
    def index(self):
        return redirect(url_for("upload_admin.upload"))

    @expose("/admin/upload/", methods=["GET", "POST"])
    @login_required
    @roles_required("administrator")
    def upload(self):
        upload_form = UploadExerciseForm()

        if upload_form.validate_on_submit():
            course_name = upload_form.course.data
            number = upload_form.exercise.data

            if not (course_name and number):
                flash("Please fill out both the course and exercise fields.")

            elif not upload_form.path_exists():
                flash(
                    "Selected file path does not exist: please, input the correct one."
                )

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
                    return redirect(url_for("upload_admin.upload"))

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
                        f'The file "{number.filename}" has been updated for course "{course_name}".'
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
                upload_form.course.data = None
                upload_form.exercise.data = None

                return redirect(url_for("upload_admin.upload"))

            # Retain course name on upload_form submission failure due to invalid file
            # format
            if upload_form.course.data:
                course_value = upload_form.course.data
            else:
                course_value = None

            return self.render(
                "admin/upload.html", upload_form=upload_form, course_value=course_value
            )

        return self.render("admin/upload.html", upload_form=upload_form)

    def is_accessible(self):
        return (
            current_user.is_active
            and current_user.is_authenticated
            and any(role.name == "administrator" for role in current_user.roles)
        )

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for("security.login"))


class DownloadAdminView(BaseView):
    @expose("/")
    def index(self):
        return redirect(url_for("download_admin.download"))

    @expose("/admin/download/", methods=["GET", "POST"])
    @login_required
    @roles_required("administrator")
    def download(self):
        download_form = DownloadForm()

        # Sort courses' name in "uploads" folder and populate the drop down menu
        courses = sorted(os.listdir(os.path.join(basedir, Config.UPLOAD_FOLDER)))
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

        # Render the download page template with the download form
        return self.render("admin/download.html", download_form=download_form)

    def is_accessible(self):
        return (
            current_user.is_active
            and current_user.is_authenticated
            and any(role.name == "administrator" for role in current_user.roles)
        )

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for("security.login"))
