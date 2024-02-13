from flask import Blueprint, flash, render_template, redirect, url_for
from app.forms import ExtendedRegisterForm
from app.models import Users, Roles, Devices, Releases, user_datastore
from flask_login import login_required
from flask_security import hash_password
from app.extensions import db
from collections import defaultdict
import re


admin_pages = Blueprint("admin_pages", __name__)


@admin_pages.route("/admin/users/new/", methods=["GET", "POST"])
@login_required
def register():
    form = ExtendedRegisterForm()

    if form.validate_on_submit():
        device_name = form.devices.data
        device = Devices.query.filter_by(name=form.devices.data).first()

        if not device:
            flash("Selected device does not exist.", "error")
            return render_template("security/register_user.html", form=form)

        new_user = Users(
            username=form.email.data,
            password=hash_password(form.password.data),
            devices=device,
            active=form.active.data,
        )

        # Fetch the selected role name from the form
        selected_role_name = form.role.data

        # Query the role based on the selected role name
        existing_role = Roles.query.filter_by(name=selected_role_name).first()

        if existing_role:
            user_datastore.add_role_to_user(new_user, existing_role)
            new_user.roles.append(existing_role)
            # Add the new user to the database
            db.session.add(new_user)
            db.session.commit()
            return redirect(
                url_for("admin.index", _external=True, _scheme="http") + "users/"
            )
        else:
            # Handle case where the selected role doesn't exist
            flash(f"Role '{selected_role_name}' does not exist.", "error")
            return render_template("security/register_user.html", form=form)

    return render_template("security/register_user.html", form=form)


@admin_pages.route("/admin/devices/", methods=["GET"])
# Disabled during development environment
@login_required
def show_devices():
    devices = sorted(Devices.query.all(), key=lambda d: d.name)
    device_ids = [d.device_id for d in devices]
    device_versions = {}
    for device in devices:
        device_versions[device] = [r.version for r in device.releases]
    releases_dict = defaultdict(list)
    all_releases = sorted(
        Releases.query.all(),
        key=lambda x: [
            int(part) if part.isdigit() else part for part in re.split(r"(\d+|\D+)", x.version)
        ],
        reverse=True
    )
    for release in all_releases:
        if release.device_id in device_ids:
            major_version = release.version.split('.')[0]
            if len(releases_dict[major_version]) < 10:
                if release.version not in releases_dict[major_version]:
                    releases_dict[major_version].append(release.version)
    return render_template(
        "admin/matrix.html",
        devices=devices,
        device_versions=device_versions,
        release_versions=releases_dict,
    )
