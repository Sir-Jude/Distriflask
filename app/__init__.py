# Basic flask imports
from flask import Flask, redirect, url_for


# Import app's configurations
from config import Config


# Import Flask's extensions
from app.extensions import db, login_manager
from flask_migrate import Migrate


# Imports for Flask security
from flask_security import (
    current_user,
    hash_password,
    Security,
)


# Imports for Admin page
from flask_admin import Admin, helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView


# Imports from otehr files
from app.errors import register_error_handlers
from app.models import Users, Roles, user_datastore
from app.views.customers import customers
from app.views.admin_pages import admin_pages
from app.forms import ExtendedRegisterForm, ExtendedLoginForm


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)
    
    
    admin = Admin(
        app, name="Admin", base_template="master.html", template_mode="bootstrap3"
    )

    app.register_blueprint(customers)
    app.register_blueprint(admin_pages)
    register_error_handlers(app)

    # This snippet MUST stay after app.register_blueprint(admin_pages)
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
            roles=Roles.query.all(),
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
            admin_role = Roles.query.filter_by(name="administrator").first()
            user_datastore.add_role_to_user(first_user, admin_role)
            db.session.commit()

    class UserAdminView(ModelView):
        column_list = ("username", "device", "active", "roles")
        column_sortable_list = (
            "username",
            "device",
            "active",
            ("roles", "roles.name"),  # Make 'roles' sortable
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

        @staticmethod
        def _display_roles(view, context, model, name):
            return ", ".join([role.name.capitalize() for role in model.roles])

        column_formatters = {"roles": _display_roles}

    admin.add_view(UserAdminView(Users, db.session))

    
    # Flask_login stuff
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(user_id)

    return app
