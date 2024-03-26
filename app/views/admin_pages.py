from app.forms import DeviceSearchForm, ExtendedRegisterForm, UploadReleaseForm
from app.models import User, Role, Device, Release
from config import basedir, Config
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import login_required
from flask_security import current_user, hash_password, roles_required
from flask_admin.contrib.sqla import ModelView
from werkzeug.utils import secure_filename
import os
import re


class UserAdminView(ModelView):
    # Actual columns' title as seen in the website
    column_list = ("username", "versions", "active", "roles")
    # Link the columns' title and the model class attribute, so to make data sortable
    column_sortable_list = (
        "username",
        ("versions", "device_name"),
        "active",
        ("roles", "roles.name"),
    )

    def is_accessible(self):
        return (
            current_user.is_active
            and current_user.is_authenticated
            and any(role.name == "administrator" for role in current_user.roles)
        )

    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for("security.login"))

    def _display_roles(view, context, model, name):
        return ", ".join([role.name.capitalize() for role in model.roles])

    def _display_versions(view, context, model, name):
        if model.device:
            # Extract versions and sort them
            versions = sorted(
                (release.version for release in model.device.releases),
                key=lambda r: tuple(
                    int(part) if part.isdigit() else part
                    for part in re.findall(r"\d+|\D+", r)
                ),
                reverse=True,
            )
            # Return a formatted string with sorted versions
            return ", ".join(versions)
        else:
            return ""

    column_formatters = {"versions": _display_versions, "roles": _display_roles}

    form = ExtendedRegisterForm

    def on_model_change(self, form, model, is_created):
        # Check if the model being changed is a User model and the current user is an administrator
        if isinstance(model, User) and "administrator" in current_user.roles:
            # Check if password field is present in the form and has a value
            if "password" in form and form.password.data:
                # Hash the password before saving it to the database
                model.password = hash_password(form.password.data)


admin_pages = Blueprint("admin_pages", __name__)


@admin_pages.route("/admin/devices/", methods=["GET", "POST"])
@login_required
@roles_required("administrator")
def devices_default_table():
    search_form = DeviceSearchForm()

    if search_form.validate_on_submit():
        device_name = search_form.device_name.data
        selected_release_version = search_form.selected_release_version.data

        if device_name and selected_release_version:
            flash("Please provide only one search criteria at a time.", "error")
            return redirect(url_for("admin_pages.devices_default_table"))

        # Resulting table of the Release search
        if selected_release_version:
            # Redirect to the new route for selected_release_version filtering
            return redirect(
                url_for(
                    "admin_pages.selected_release_version",
                    selected_release_version=selected_release_version,
                )
            )

        # Resulting table of the Device search
        elif device_name:
            # Redirect to the new route for device_name filtering
            return redirect(
                url_for("admin_pages.selected_device_name", device_name=device_name)
            )

        else:
            flash("Please, provide at least one search criteria.", "error")
            return redirect(url_for("admin_pages.devices_default_table"))

    # Default table
    else:
        all_releases = sorted(
            Release.query.all(),
            key=lambda x: tuple(
                int(part) if part.isdigit() else part
                for part in re.findall(r"\d+|\D+", x.version)
            ),
        )

        first_number = str(
            max(int(release.version.split(".")[0]) for release in all_releases)
        )

        second_number = str(
            max(
                int(release.version.split(".")[1])
                for release in all_releases
                if release.version.startswith(first_number + ".")
            )
        )

        # Now, we'll use a custom sorting key for the third part
        third_numbers = [
            (
                int(part) if part.isdigit() else part
                for part in release.version.split(".")[2]
            )
            for release in all_releases
            if release.version.startswith(first_number + "." + second_number + ".")
        ]

        # Flatten the list of generators and then find the maximum
        third_number = str(
            max(
                [part for generator in third_numbers for part in generator],
                key=lambda x: (int(x) if isinstance(x, int) else x),
            )
        )

        return redirect(
            url_for(
                "admin_pages.selected_release_version",
                selected_release_version=f"{first_number}.{second_number}.{third_number}",
            )
        )


@admin_pages.route(
    "/admin/devices/release-table/<selected_release_version>", methods=["GET", "POST"]
)
@login_required
@roles_required("administrator")
def selected_release_version(selected_release_version):
    search_form = DeviceSearchForm()

    parts = selected_release_version.split(".")

    # Check if users input a valid release format (X.X or X.X.X)
    if len(parts) < 2:
        flash("Invalid release version format.", "error")
        return redirect(url_for("admin_pages.devices_default_table"))

    filtered_releases = Release.query.filter(
        Release.version.like(f"{parts[0]}.{parts[1]}%")
    ).all()

    # Check if any existing release starts with the provided major version (X.X)
    if not filtered_releases:
        flash("No releases found for the provided major version.", "error")
        return redirect(url_for("admin_pages.devices_default_table"))

    # Get all unique releases matching the major version
    all_releases = sorted(
        set([release.version for release in filtered_releases]),
        key=lambda x: tuple(
            int(part) if part.isdigit() else part for part in re.findall(r"\d+|\D+", x)
        ),
        reverse=True,
    )

    if len(parts) == 2:
        selected_release_version = all_releases[0]

    # Check if any existing release starts with the provided major version (X.X)
    if not all_releases:
        flash("No releases found for the provided major version.", "error")
        return redirect(url_for("admin_pages.devices_default_table"))

    # Check if the provided release version exists in the list of all releases
    elif selected_release_version not in all_releases:
        flash("Selected release version not found.", "error")
        return redirect(url_for("admin_pages.devices_default_table"))

    check_existence = Release.query.filter_by(version=selected_release_version).first()

    # Check if there are any filtered releases
    if check_existence:
        release_version_X_X = "".join(
            [
                str(part)
                for part in list(
                    int(part) if part.isdigit() else part
                    for part in re.findall(r"\d+|\D+", selected_release_version)
                )[:3]
            ]
        )

        # Extract devices associated with the filtered releases
        devices_with_matching_releases = [
            release.device for release in filtered_releases
        ]

        # Query devices that have releases matching the major version
        devices_in_rows = Device.query.filter(
            Device.releases.any(Release.version.like(f"{release_version_X_X}%"))
        ).all()

        # Find the index of the selected release version in the list of all releases.
        index = all_releases.index(selected_release_version)

        # Define a variable to store set number of newer/older releases
        halfwith = 10

        # Initialize lists to store newer and older releases.
        newer = []
        older = all_releases[index + 1 : index + halfwith + 1]

        # Check if there are fewer than 10 releases before the selected one.
        if index - halfwith < 0:
            # If yes, include releases from beginning up to selected one.
            newer = all_releases[:index]
        else:
            # Otherwise, include the 10 releases before the selected one.
            newer = all_releases[index - halfwith : index]

        # Reorder all releases to have newer : selected :older
        releases = newer + [all_releases[index]] + older

        # Check if there are more releases after the selected one.
        if (index + halfwith + 1) < len(all_releases):
            # If yes, add ellipsis to indicate more releases.
            releases = releases + ["..."]

        # Check if there are more releases before the selected one.
        if (index - halfwith) > 0:
            releases = ["..."] + releases

        device_versions = {
            device: [
                release.version
                for release in device.releases
                if release.version in all_releases
            ]
            for device in devices_with_matching_releases
        }

        # Sort devices by name in reverse order
        devices_in_rows = sorted(devices_in_rows, key=lambda x: x.name, reverse=True)

        return render_template(
            "admin/matrix_release.html",
            devices_in_rows=devices_in_rows,
            device_versions=device_versions,
            releases=releases,
            selected_release_version=selected_release_version,
            search_form=search_form,
        )
    else:
        flash("No release found.", "error")
        # Redirect to the default devices table
        return redirect(url_for("admin_pages.devices_default_table"))


@admin_pages.route("/admin/devices/device/<device_name>", methods=["GET", "POST"])
@login_required
@roles_required("administrator")
def selected_device_name(device_name):
    search_form = DeviceSearchForm()  # Instantiate the search_form
    all_devices = sorted(Device.query.all(), key=lambda d: d.name, reverse=True)
    all_device_versions = {
        device: sorted(
            [r.version for r in device.releases],
            key=lambda x: tuple(
                int(part) if part.isdigit() else part
                for part in re.findall(r"\d+|\D+", x)
            ),
            reverse=True,
        )
        for device in all_devices
    }
    filtered_device = Device.query.filter_by(name=device_name).first()
    if filtered_device:
        return render_template(
            "admin/matrix_device.html",
            devices=[filtered_device],
            all_device_versions=all_device_versions,
            search_form=search_form,
        )
    else:
        flash("No devices found.", "error")
        return redirect(url_for("admin_pages.devices_default_table"))


@admin_pages.route("/admin/upload/", methods=["GET", "POST"])
@login_required
@roles_required("administrator")
def upload():
    upload_form = UploadReleaseForm()

    if upload_form.validate_on_submit():
        device = upload_form.device.data
        version = upload_form.version.data

        if not device or not version:  # Check if either field is empty
            flash("Please fill out both the device and version fields.")

        elif not upload_form.path_exists():  # Check if folder path exists
            flash("Selected file path does not exist: please, input the correct one.")

        elif not upload_form.allowed_file():  # Check if the file format is allowed
            flash("Selected file format is not allowed: please, use only .txt or .deb.")

        else:
            device_folder = os.path.join(basedir, Config.UPLOAD_FOLDER, device)
            version.save(os.path.join(device_folder, secure_filename(version.filename)))
            flash(
                f'The file "{version.filename}" has been uploaded into the folder "{basedir}/{Config.UPLOAD_FOLDER}/{device}/".'
            )

            # Clear upload_form data after successful submission
            upload_form.device.data = None
            upload_form.version.data = None

            return redirect(url_for("admin_pages.upload"))

        # Retain device name on upload_form submission failure due to invalid file format
        if upload_form.device.data:
            device_value = upload_form.device.data
        else:
            device_value = None

        return render_template(
            "admin/upload.html", upload_form=upload_form, device_value=device_value
        )

    return render_template("admin/upload.html", upload_form=upload_form)
