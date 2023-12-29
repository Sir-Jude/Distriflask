from flask import Blueprint, flash, render_template, redirect, url_for
from app.forms import ExtendedRegisterForm
from app.models import Users, Roles, user_datastore
from flask_security import hash_password
from app.extensions import db


admin_pages = Blueprint("admin_pages", __name__)


@admin_pages.route("/admin/users/new/", methods=["GET", "POST"])
def register():
    form = ExtendedRegisterForm()

    if form.validate_on_submit():
        new_user = Users(
            username=form.email.data,
            password=hash_password(form.password.data),
            device=form.device.data,
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
