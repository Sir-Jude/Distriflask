from app.extensions import db
from app.forms import (
    AdminDownloadForm,
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
    def _display_versions(view, context, model, name):
        if model.device:
            # Extract versions and sort them
            versions = sorted(
                (release.version for release in model.device.releases),
                key=lambda r: tuple(
                    int(part) if part.isdigit() else part
                    for part in re.findall(r"\d+|\D+", r)
                ),
                reverse=False,
            )
            # Return a formatted string with sorted versions
            return ", ".join(versions)
        else:
            return ""

    # Attribute of the ModelView class
    # Customize the display of the columns
    column_formatters = {"versions": _display_versions, "roles": _display_roles}

    form = ExtendedRegisterForm

    # Customized from BaseModelView
    def on_model_change(self, form, model, is_created):
        # Check if the model being changed is a User model and the current user is an administrator
        if isinstance(model, User) and "administrator" in current_user.roles:
            # Check if password field is present in the form and has a value
            if "password" in form and form.password.data:
                # Hash the password before saving it to the database
                model.password = hash_password(form.password.data)

    # Actual columns' title as seen in the website
    column_list = ("username", "versions", "active", "roles")

    # Link the columns' title and the model class attribute, so to make data sortable
    column_sortable_list = (
        "username",
        ("versions", "course_name"),
        "active",
        ("roles", "roles.name"),
    )


class CourseAdminView(BaseView):
    # This decorator exposes the method to be reachable via a specific URL route.
    @expose("/")
    # The "index" func serves as entry point for this particular app's section
    def index(self):
        return redirect(url_for("course_admin.courses_default_table"))

    @expose("/admin/device/", methods=["GET", "POST"])
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
                    for part in re.findall(r"\d+|\D+", x.version)
                ),
            )
            # The three following variables will always return the most updated version
            # (no matter which numbers/letters are used)
            first_number = str(
                max(int(release.version.split(".")[0]) for release in all_exercises)
            )

            second_number = str(
                max(
                    int(release.version.split(".")[1])
                    for release in all_exercises
                    if release.version.startswith(first_number + ".")
                )
            )

            # Now, we'll use a custom sorting key for the third part
            # (since it might contain not just numbers, but also letters)
            third_number = [
                (
                    int(part) if part.isdigit() else part
                    for part in release.version.split(".")[2]
                )
                for release in all_exercises
                if release.version.startswith(first_number + "." + second_number + ".")
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

        # Filter releases based on first two numbers of selected_exercise in the URL
        if len(parts) < 2:
            flash("Invalid release version format.", "error")
            return redirect(url_for("course_admin.courses_default_table"))

        filtered_exercises = Exercise.query.filter(
            Exercise.version.like(f"{parts[0]}.{parts[1]}%")
        ).all()

        # Redirect to the default if there is any matching release
        if not filtered_exercises:
            flash("No releases found for the provided major version.", "error")
            return redirect(url_for("course_admin.courses_default_table"))

        # Get all unique releases matching the major version
        all_exercises = sorted(
            set([release.version for release in filtered_exercises]),
            key=lambda x: tuple(
                int(part) if part.isdigit() else part
                for part in re.findall(r"\d+|\D+", x)
            ),
            reverse=False,
        )

        # Check if the provided release version exists in the list of all releases
        if len(parts) == 2:
            selected_exercise = all_exercises[0]

        # Redirect to the default if there is any matching release
        if not all_exercises:
            flash("No releases found for the provided major version.", "error")
            return redirect(url_for("course_admin.courses_default_table"))

        # Check if the provided release version exists in the list of all releases
        elif selected_exercise not in all_exercises:
            flash("Selected release version not found.", "error")
            return redirect(url_for("course_admin.courses_default_table"))

        check_existence = Exercise.query.filter_by(version=selected_exercise).first()

        # Check if there are any filtered releases
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
                release.device for release in filtered_exercises
            ]

            # Query courses that have releases matching the major version
            courses_in_rows = Course.query.filter(
                Course.releases.any(Exercise.version.like(f"{exercise_number}%"))
            ).all()

            # Find the index of the selected release version in the list of all releases.
            index = all_exercises.index(selected_exercise)

            # Define a variable to store set number of newer/older releases
            halfwith = 10

            # Initialize lists to store newer and older releases.
            newer = []
            older = all_exercises[index + 1 : index + halfwith + 1]

            # Check if there are fewer than 10 releases before the selected one.
            if index - halfwith < 0:
                # If yes, include releases from beginning up to selected one.
                newer = all_exercises[:index]
            else:
                # Otherwise, include the 10 releases before the selected one.
                newer = all_exercises[index - halfwith : index]

            # Reorder all releases to have newer : selected :older
            releases = newer + [all_exercises[index]] + older

            # Check if there are more releases after the selected one.
            if (index + halfwith + 1) < len(all_exercises):
                # If yes, add ellipsis to indicate more releases.
                releases = releases + ["..."]

            # Check if there are more releases before the selected one.
            if (index - halfwith) > 0:
                releases = ["..."] + releases

            all_exercise_numbers = {
                device: [
                    release.version
                    for release in device.releases
                    if release.version in all_exercises
                ]
                for device in courses_with_matching_students
            }

            # Sort courses by name
            courses_in_rows = sorted(
                courses_in_rows, key=lambda x: x.name, reverse=False
            )

            return self.render(
                "admin/matrix_exercise.html",
                courses_in_rows=courses_in_rows,
                all_exercise_numbers=all_exercise_numbers,
                releases=releases,
                selected_exercise=selected_exercise,
                search_form=search_form,
            )
        else:
            flash("No release found.", "error")
            # Redirect to the default courses table
            return redirect(url_for("course_admin.courses_default_table"))

    @expose("/device/<course_name>", methods=["GET", "POST"])
    @login_required
    @roles_required("administrator")
    def selected_course_name(self, course_name):
        search_form = CourseSearchForm()
        all_courses = sorted(Course.query.all(), key=lambda d: d.name, reverse=False)
        all_exercises = {
            device: sorted(
                [r.version for r in device.releases],
                key=lambda x: tuple(
                    int(part) if part.isdigit() else part
                    for part in re.findall(r"\d+|\D+", x)
                ),
                reverse=False,
            )
            for device in all_courses
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
            version = upload_form.exercise.data

            if not (course_name and version):
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
                filename, extension = os.path.splitext(version.filename)

                # Save the file to the designated folder
                course = Course.query.filter_by(name=course_name).first()
                if not course:
                    flash(f"Course {course_name} does not exist.")
                    return redirect(url_for("upload_admin.upload"))

                course_folder = os.path.join(basedir, Config.UPLOAD_FOLDER, course_name)
                filepath = os.path.join(
                    course_folder, secure_filename(version.filename)
                )
                version.save(filepath)

                # Check if the release with the same version already exists for the course
                existing_exercise = Exercise.query.filter_by(
                    device=course, version=filename
                ).first()
                if existing_exercise:
                    # Update the existing release
                    existing_exercise.exercise_path = filepath
                    db.session.commit()
                    flash(
                        f'The file "{version.filename}" has been updated for course "{course_name}".'
                    )
                else:
                    # Store the version's info in the database
                    new_release = Exercise(
                        version=filename,
                        device=course,
                        exercise_path=filepath,
                    )
                    db.session.add(new_release)
                    db.session.commit()
                    flash(
                        f'The file "{version.filename}" has been uploaded into the folder'
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
        download_form = AdminDownloadForm(formdata=request.form)

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
            # 2) Retrieve all releases associated with the selected course and sort them by version
            exercises = sorted(
                Exercise.query.join(Course)
                .filter(Course.name == selected_course)
                .all(),
                key=lambda r: tuple(
                    int(part) if part.isdigit() else part
                    for part in re.findall(r"\d+|\D+", r.version)
                ),
                reverse=False,
            )
        # Populate the version choices in the form with the sorted versions
        # (empty list [] as default)
        download_form.exercise.choices = [
            (exercise.version, exercise.version) for exercise in exercises
        ]

        # If the form is submitted to initiate a download and the form data is valid...
        if download_form.submit.data and download_form.validate_on_submit():
            selected_exercise = download_form.exercise.data
            # Retrieve the release corresponding to the selected version
            exercise = Exercise.query.filter_by(version=selected_exercise).first()
            version_path = exercise.exercise_path
            path = os.path.join(basedir, Config.UPLOAD_FOLDER, version_path)
            # Send the release file to the user as an attachment for download
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
