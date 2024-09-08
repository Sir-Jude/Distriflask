import os
import re

from flask import flash, redirect, url_for
from flask_admin.base import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import login_required
from flask_security import current_user, hash_password, roles_required
from app.helpers import process_download_form, handle_download
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms import (CourseSearchForm, DownloadForm, ExtendedRegisterForm,
                       UploadExerciseForm)
from app.models import Course, Exercise, User, Role
from config import Config, basedir


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
        if isinstance(model, User) and "administrator" in [
            role.name for role in current_user.roles
        ]:
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
            selected_user = search_form.selected_user.data

            if course_name and selected_user:
                flash("Please provide only one search criteria at a time.", "error")
                return redirect(url_for("course_admin.courses_default_table"))

            # Resulting table of the Exercise search
            if selected_user:
                # Redirect to the new route for selected_user filtering
                return redirect(
                    url_for(
                        "course_admin.selected_user",
                        selected_user=selected_user,
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
            all_users = sorted(
                User.query.all(),
                key=lambda x: x.username)
            # The three following variables will always return the most updated number
            # (no matter which numbers are used)
            first_user = str(
                User.query
                .join(User.roles)
                .filter(User.roles.any(Role.name == "student"))  # Filter by the "student" role
                .filter(User.username == all_users[0].username)  # Get the first user from all_users
                .first()  # Return the first matching result
            )
            
            return redirect(
                url_for(
                    "course_admin.selected_user",
                    selected_user=f"{first_user}",
                )
            )

    @expose("/users-table/<selected_user>", methods=["GET", "POST"])
    @login_required
    @roles_required("administrator")
    def selected_user(self, selected_user):
        search_form = CourseSearchForm()

        # Retrieve all users (sorted alphabetically)
        all_users = sorted([user.username for user in User.query.all()])

        # Check if the provided selected_user exists in the list of all users
        if selected_user not in all_users:
            flash("Selected user not found.", "error")
            return redirect(url_for("course_admin.courses_default_table"))

        # Find the index of the selected user in the list
        index = all_users.index(selected_user)

        # Define a variable to store set number of newer/older users
        halfwidth = 10

        # Initialize lists to store newer and older users.
        newer = []
        older = all_users[index + 1 : index + halfwidth + 1]

        # Check if there are fewer than 10 users before the selected one.
        if index - halfwidth < 0:
            # If yes, include users from the beginning up to the selected one.
            newer = all_users[:index]
        else:
            # Otherwise, include the 10 users before the selected one.
            newer = all_users[index - halfwidth : index]

        # Reorder the users to have newer : selected : older
        users = newer + [all_users[index]] + older

        # Check if there are more users after the selected one.
        if (index + halfwidth + 1) < len(all_users):
            # If yes, add ellipsis to indicate more users.
            users = users + ["..."]

        # Check if there are more users before the selected one.
        if (index - halfwidth) > 0:
            users = ["..."] + users

        # Retrieve courses associated with the filtered users
        filtered_users = User.query.filter(User.username.in_(users)).all()
        courses_with_matching_users = [
            course for user in filtered_users for course in user.courses
        ]

        # Query courses that have users matching the provided usernames
        courses_in_rows = Course.query.filter(
            Course.users.any(User.username.in_(users))
        ).all()

        # Create a mapping of courses and the users enrolled in them
        all_user_usernames = {
            course: [
                user.username
                for user in course.users
                if user.username in all_users
            ]
            for course in courses_with_matching_users
        }

        # Sort courses by name
        courses_in_rows = sorted(courses_in_rows, key=lambda x: x.name, reverse=False)

        return self.render(
            "admin/matrix_exercise.html",
            courses_in_rows=courses_in_rows,
            all_user_usernames=all_user_usernames,
            users=users,
            selected_user=selected_user,
            search_form=search_form,
        )

    @expose("/course/<course_name>", methods=["GET", "POST"])
    @login_required
    @roles_required("administrator")
    def selected_course_name(self, course_name):
        search_form = CourseSearchForm()
        all_courses = sorted(Course.query.all(), key=lambda d: d.name, reverse=False)
        all_users = {
            course: sorted(
                [user.username for user in course.users],
                key=lambda x: tuple(
                    int(part) if part.isdigit() else part
                    for part in re.findall(r"\d+|\D+", x)
                ),
            )
            for course in all_courses
        }
        filtered_course = Course.query.filter_by(name=course_name).first()
        if filtered_course:
            return self.render(
                "admin/matrix_course.html",
                courses=[filtered_course],
                all_users=all_users,
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
        if name == "selected_user":
            # Extract 'selected_user' from kwargs
            selected_user = kwargs.pop("selected_user", None)
            if selected_user:
                # Call the relevant view method with the extracted argument
                return getattr(self, name)(selected_user)
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

        # Get list of courses from file system and sort them
        courses = sorted(os.listdir(os.path.join(basedir, Config.UPLOAD_FOLDER)))
        
        # Handle file download if the form is submitted and valid
        process_download_form(download_form, courses)
        
        # Handle file download if the form is submitted and valid
        file_response = handle_download(download_form)
        
        if file_response:
            return file_response

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
