from app.extensions import db
from app.forms import DeviceSearchForm, ExtendedRegisterForm
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
    "/admin/devices/",
    defaults={"device_name": None, "release_number": None},
    methods=["GET", "POST"],
)
@admin_pages.route("/admin/devices/<device_name>", methods=["GET", "POST"])
@admin_pages.route("/admin/devices/<release_number>", methods=["GET", "POST"])
@login_required
def device_filter(device_name, release_number):
    devices = sorted(Device.query.all(), key=lambda d: d.name, reverse=True)
    device_versions = {
        device: [r.version for r in device.releases] for device in devices
    }

    form = DeviceSearchForm()

    if form.validate_on_submit():
        searched_device_name = form.device_name.data
        searched_release_number = form.release_number.data

        if searched_device_name and searched_release_number:
            flash("Please provide only one search criteria at a time", "error")
            return redirect(url_for("admin_pages.device_filter"))

        if searched_release_number:
            filtered_releases = Release.query.filter(
                Release.version.like(f"{searched_release_number}%")
            ).all()
            if filtered_releases:
                devices_with_matching_releases = [
                    release.devices for release in filtered_releases
                ]
                devices = Device.query.filter(
                    Device.releases.any(
                        Release.version.like(f"{searched_release_number}%")
                    )
                ).all()
                all_releases = sorted(
                    set([release.version for release in filtered_releases]),
                    key=lambda x: tuple(
                        int(part) if part.isdigit() else part
                        for part in re.findall(r"\d+|\D+", x)
                        # This line of code reverse the order of the table columns
                    ), reverse=True
                )[:20]  # Slice to include only the first 20 releases
                
                device_versions = {
                    device: [
                        release.version
                        for release in device.releases
                        if release.version in all_releases
                    ]
                    for device in devices_with_matching_releases
                }
                
                # Sort devices rows in reverse order
                devices = sorted(devices, key=lambda x: x.name, reverse=True)

                return render_template(
                    "admin/matrix_release.html",
                    devices=devices,
                    device_versions=device_versions,
                    all_releases=all_releases,
                )
            else:
                flash("No release found", "error")
                return redirect(url_for("admin_pages.device_filter"))

        elif searched_device_name:
            filtered_device = Device.query.filter_by(name=searched_device_name).first()
            if filtered_device:
                return render_template(
                    "admin/matrix_device.html",
                    devices=[filtered_device],
                    device_versions=device_versions,
                )
            else:
                flash("No devices found", "error")
                return redirect(url_for("admin_pages.device_filter"))

    else:
        releases_dict = defaultdict(list)
        all_releases = sorted(
            Release.query.all(),
            key=lambda x: tuple(
                int(part) if part.isdigit() else part
                for part in re.findall(r"\d+|\D+", x.version)
            ),
        )

        last_major_version = str(
            max(int(release.version.split(".")[0]) for release in all_releases)
        )
        last_major_releases_count = 0
        for release in reversed(all_releases):
            major_version = release.version.split(".")[0]
            if major_version != last_major_version:
                continue
            if last_major_releases_count >= 20:
                break
            if release.version not in releases_dict[major_version]:
                releases_dict[major_version].insert(0, release.version)
                last_major_releases_count += 1

        releases_dict[major_version].reverse()

        return render_template(
            "admin/matrix_default.html",
            form=form,
            devices=devices,
            device_versions=device_versions,
            release_versions=releases_dict,
        )
