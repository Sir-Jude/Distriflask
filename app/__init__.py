from app.extensions import db, login_manager, migrate

# Imports from otehr files
from app.errors import register_error_handlers
from app.models import User, Role, user_datastore
from app.views.customers import customers
from app.views.admin_pages import admin_pages
from app.forms import ExtendedRegisterForm, ExtendedLoginForm

# Import app's configurations
from config import Config

# Basic flask imports
from flask import Flask, redirect, url_for

# Imports for Admin page
from flask_admin import Admin, helpers as admin_helpers
from flask_admin.base import BaseView, expose
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView

# Imports for Flask security
from flask_security import (
    current_user,
    Security,
)

from sqlalchemy import select


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Variable name="Admin" refers to the button "Admn" in the nav-bar
    admin = Admin(
        app, name="Admin", base_template="master.html", template_mode="bootstrap3"
    )

    app.register_blueprint(customers)
    app.register_blueprint(admin_pages)
    register_error_handlers(app)

    # This snippet MUST stay after "app.register_blueprint(admin_pages)"
    security = Security(
        app,
        user_datastore,
        register_form=ExtendedRegisterForm,
        login_form=ExtendedLoginForm,
    )

    @security.context_processor
    def security_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
            get_url=url_for,
        )

    @security.register_context_processor
    def security_register_processor():
        return dict(
            user_datastore=user_datastore,
            roles=Role.query.all(),
            register_user_form=ExtendedRegisterForm(),
        )

    @app.before_request
    def create_user():
        existing_user = user_datastore.find_user(username="admin")
        if not existing_user:
            first_user = user_datastore.create_user(
                username="admin", password="12345678"
            )
            user_datastore.activate_user(first_user)
            db.session.commit()

            # Assign the 'administrator' role to the 'admin' user
            admin_role = Role.query.filter_by(name="administrator").first()
            user_datastore.add_role_to_user(first_user, admin_role)
            db.session.commit()

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
            return model.versions()

        column_formatters = {"roles": _display_roles, "versions": _display_versions}

    class CustomMenuView(BaseView):
        @expose("/")
        def index(self):
            return redirect(url_for("admin_pages.search_releases"))

        def is_accessible(self):
            return (
                current_user.is_active
                and current_user.is_authenticated
                and any(role.name == "administrator" for role in current_user.roles)
            )

        def _get_admin_menu(self):
            return MenuLink("Device", endpoint="admin_pages.show_devices")

    admin.add_view(UserAdminView(User, db.session, name="Users"))
    admin.add_view(CustomMenuView(name="Devices"))

    # Flask_login stuff
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    return app
