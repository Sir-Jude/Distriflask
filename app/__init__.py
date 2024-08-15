# Imports from otehr files
from app.errors import register_error_handlers
from app.extensions import db, login_manager, migrate
from app.models import User, Role, user_datastore
from app.views.students import students
from app.views.admin_pages import (
    UserAdminView,
    CourseAdminView,
    UploadAdminView,
    DownloadAdminView,
)
from app.forms import (
    AdminDownloadForm,
    CourseSearchForm,
    StudentdownloadForm,
    ExtendedLoginForm,
    ExtendedRegisterForm,
    UploadExerciseForm,
)

# Import app's configurations
from config import Config

# Basic flask imports
from flask import Flask, url_for

# Imports for Admin page
from flask_admin import Admin, helpers as admin_helpers

# Imports for Flask security
from flask_security import Security, UsernameUtil


# The application factory pattern in Flask offers several advantages.
# 1) Testing:
#    It enables the creation of multiple instances of the application with
#      different configurations, facilitating comprehensive testing across
#      various scenarios.
# 2) Multiple instances:
#    It allows to run different versions of the same application running in
#      the same application process, enhancing, scalability, flexibility and
#      resource efficiency.
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    button_text = "Admin"
    admin = Admin(
        app,
        name=button_text,
        base_template="master.html",
        template_mode="bootstrap3",
    )

    app.register_blueprint(students)
    register_error_handlers(app)

    security = Security(
        app,
        user_datastore,
        username_util_cls=UsernameUtil,
        register_form=ExtendedRegisterForm,
        login_form=ExtendedLoginForm,
    )

    # Context processors inject new variables into the context of a template,
    #   so we don't need to explicitly pass them around.
    # The processor runs when the app is created.
    @security.context_processor
    def security_context_processor():
        search_form = CourseSearchForm()
        upload_form = UploadExerciseForm()
        download_form = AdminDownloadForm()
        student_download_form = StudentdownloadForm()
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            # DO NOT RENAME/REMOVE the next two lines: Flask essential variables
            h=admin_helpers,  # !!!
            get_url=url_for,  # !!!
            search_form=search_form,
            upload_form=upload_form,
            download_form=download_form,
            student_download_form=student_download_form,
        )

    @security.register_context_processor
    def security_register_processor():
        register_form = ExtendedRegisterForm()
        return dict(
            register_form=register_form,
            roles=Role.query.all(),
            user_datastore=user_datastore,
        )

    @app.before_request
    def create_user():
        existing_user = user_datastore.find_user(username="admin")
        if not existing_user:
            first_user = user_datastore.create_user(
                username="admin", password="12345678"
            )
            user_datastore.activate_user(first_user)

            # Assign the 'administrator' role to the 'admin' user
            admin_role = Role.query.filter_by(name="administrator").first()
            user_datastore.add_role_to_user(first_user, admin_role)
            db.session.commit()

    admin.add_view(UserAdminView(User, db.session, name="Users"))
    admin.add_view(CourseAdminView(name="Courses", endpoint="course_admin"))
    admin.add_view(UploadAdminView(name="Upload", endpoint="upload_admin"))
    admin.add_view(DownloadAdminView(name="Download", endpoint="download_admin"))

    # Redirect users that are not logged in to the default "login" view
    login_manager.login_view = "login"

    # Decorator to call user_loader function for each request to load the user
    #   object. It will be accessible via current_user within the application.
    @login_manager.user_loader
    # Flask-Login will pass the user ID stored in the session to this function.
    # The function is expected to return the corresponding user object.
    def load_user(user_id):
        return User.query.get(user_id)

    return app
