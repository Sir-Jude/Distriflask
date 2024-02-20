from app.extensions import db
from app.forms import ReleaseSearchForm, ExtendedRegisterForm
from app.models import User, Role, Device, Release, user_datastore
from collections import defaultdict
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_security import hash_password
from sqlalchemy import func
import re


admin_pages = Blueprint("admin_pages", __name__)


@admin_pages.route("/admin/user/new/", methods=["GET", "POST"])
@login_required
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


@admin_pages.route(
    "/admin/devices/", defaults={"device_name": None}, methods=["GET", "POST"]
)
@admin_pages.route("/admin/devices/<device_name>", methods=["GET", "POST"])
# Disabled during development environment
@login_required
def search_releases(device_name):
    devices = sorted(Device.query.all(), key=lambda d: d.name, reverse=True)
    device_versions = {
        device: [r.version for r in device.releases] for device in devices
    }

    form = ReleaseSearchForm()

    # Populate choices for device_name field
    form.device_name.choices = [(device.name, device.name) for device in devices]

    if form.validate_on_submit():
        searched_device_name = form.device_name.data
        filtered_device = Device.query.filter_by(name=searched_device_name).first()

        if filtered_device:
            return redirect(
                url_for("admin_pages.search_releases", device_name=filtered_device.name)
            )

    else:
        releases_dict = defaultdict(list)
        all_releases = sorted(
            Release.query.all(),
            key=lambda x: [
                int(part) if part.isdigit() else part
                for part in re.split(r"(\D+)", x.version)
            ],
            reverse=True,
        )

        for release in all_releases:
            major_version = release.version.split(".")[0]
            if len(releases_dict[major_version]) < 10:
                if release.version not in releases_dict[major_version]:
                    releases_dict[major_version].append(release.version)

        if device_name:
            # If device name parameter is provided, filter devices accordingly
            filtered_device = Device.query.filter(
                func.lower(Device.name) == func.lower(device_name)
            ).first()
            if filtered_device:
                return render_template(
                    "admin/matrix_filtered.html",
                    devices=[filtered_device],
                    device_versions=device_versions,
                )

        return render_template(
            "admin/matrix_default.html",
            form=form,
            devices=devices,
            device_versions=device_versions,
            release_versions=releases_dict,
        )
