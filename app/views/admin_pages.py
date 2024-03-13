from app.extensions import db
from app.forms import DeviceSearchForm, ExtendedRegisterForm, UploadReleaseForm
from app.models import User, Role, Device, Release, user_datastore
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_security import hash_password, roles_required
import re


admin_pages = Blueprint("admin_pages", __name__)


@admin_pages.route("/admin/user/new/", methods=["GET", "POST"])
@login_required
@roles_required("administrator")
def register():
    form = ExtendedRegisterForm()

    if form.validate_on_submit():
        device = Device.query.filter_by(name=form.devices.data).first()

        if not device:
            flash("Selected device does not exist.", "error")
            return render_template("security/register_user.html", form=form)

        new_user = User(
            username=form.email.data,
            password=hash_password(form.password.data),
            devices=device,
            active=form.active.data,
        )

        # Fetch the selected role name from the form
        selected_role_name = form.role.data

        # Query the role based on the selected role name
        existing_role = Role.query.filter_by(name=selected_role_name).first()

        if existing_role:
            user_datastore.add_role_to_user(new_user, existing_role)
            new_user.roles.append(existing_role)
            # Add the new user to the database
            db.session.add(new_user)
            db.session.commit()
            return redirect(
                url_for("admin.index", _external=True, _scheme="http") + "user/"
            )
        else:
            # Handle case where the selected role doesn't exist
            flash(f"Role '{selected_role_name}' does not exist.", "error")
            return render_template("security/register_user.html", form=form)

    return render_template("security/register_user.html", form=form)


@admin_pages.route("/admin/devices/", methods=["GET", "POST"])
@login_required
@roles_required("administrator")
def devices_default_table():
    form = DeviceSearchForm()

    if form.validate_on_submit():
        device_name = form.device_name.data
        selected_release_version = form.selected_release_version.data

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
    "/admin/devices/release/<selected_release_version>.", methods=["GET", "POST"]
)
@login_required
@roles_required("administrator")
def selected_release_version(selected_release_version):
    form = DeviceSearchForm()

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

        # Filter releases based on first two numbers of the selected_release_version in the URL
        filtered_releases = Release.query.filter(
            Release.version.like(f"{release_version_X_X}%")
        ).all()

        # Extract devices associated with the filtered releases
        devices_with_matching_releases = [
            release.devices for release in filtered_releases
        ]

        # Query devices that have releases matching the major version
        devices_in_rows = Device.query.filter(
            Device.releases.any(Release.version.like(f"{release_version_X_X}%"))
        ).all()

        # Get all unique releases matching the major version
        all_releases = sorted(
            set([release.version for release in filtered_releases]),
            key=lambda x: tuple(
                int(part) if part.isdigit() else part
                for part in re.findall(r"\d+|\D+", x)
            ),
            reverse=True,
        )

        index = all_releases.index(selected_release_version)

        if index == 0:
            all_releases = all_releases[:11]
        elif 0 < index < 11:
            all_releases = all_releases[: index + 11]
        else:
            all_releases = all_releases[index - 10 : index + 11]

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
            all_releases=all_releases,
            selected_release_version=selected_release_version,
            form=form,
        )
    else:
        flash("No release found.", "error")
        # Redirect to the default devices table
        return redirect(url_for("admin_pages.devices_default_table"))


@admin_pages.route("/admin/devices/device/<device_name>", methods=["GET", "POST"])
@login_required
@roles_required("administrator")
def selected_device_name(device_name):
    form = DeviceSearchForm()  # Instantiate the form
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
            form=form,
        )
    else:
        flash("No devices found.", "error")
        return redirect(url_for("admin_pages.devices_default_table"))


@admin_pages.route("/admin/upload/", methods=["GET", "POST"])
@login_required
@roles_required("administrator")
def upload():
    form = UploadReleaseForm()
    pass
