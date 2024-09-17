# Pytest's configuration file
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from flask_security import hash_password
from flask_wtf import FlaskForm
from wtforms import StringField

from app import create_app
from app.extensions import db
from app.forms import username_validator
from app.helpers import validate_upload_form
from app.models import Course, Exercise, Role, User
from config import TestConfig, basedir
from create_tables import create_roles


@pytest.fixture()
def app():
    """
    This fixture creates a Flask application instance with a specific
    configuration class for testing purposes. It then sets up the
    application context, creates necessary database tables and roles.
    After yielding the application instance to the test function, it
    performs teardown actions by removing the test database file.
    """

    # Use the application factory to create an instance of the app
    # Specify "TestConfig" as the configuration class
    app = create_app(config_class=TestConfig)

    # Sets up an application context
    # (necessary for certain operations in Flask, such as interacting with DB)
    with app.app_context():
        # Create all database tables defined by the models
        db.create_all()

        create_roles(app=app)

    # Provide the application instance to the test function
    #   and allow additional actions to be performed
    yield app

    # Cleanup: Remove SQLite database file used for testing
    test_db_path = Path.cwd() / "instance" / "test_db.sqlite3"
    if test_db_path.exists():
        os.remove(test_db_path)


@pytest.fixture()
def client(app):
    """
    This fixture returns a test client object that allows simulating HTTP
    requests to the Flask application without running a full web server.
    The test client can be used in pytest tests to interact with Flask
    routes and test their behaviour.
    """

    # Use the "test_client()" built-in Flask method to provide a test client for the app.
    # This client can be used to make HTTP requests to the app in a testing context.
    return app.test_client()


@pytest.fixture()
def runner(app):
    """
    This fixture returns a test CLI runner object that allows executing
    command-line commands within the context of the Flask application.
    The test CLI runner can be used in pytest tests to simulate command-line
    interactions and test their behavior.
    """

    # Use the "test_cli_runner()" built-in Flask method to return a CLI runner object.
    # It allows invoking command-line commands as if they had been run in a terminal
    #   but within the context of your Flask application.
    return app.test_cli_runner()


@pytest.fixture()
def student_user(app):
    """
    This fixture creates a new student user, logs them in, and yields the
    test client, student username, and student password.
    """
    with app.app_context():
        role = Role.query.filter_by(name="student").first()
        new_student = User(
            username="test_student",
            password=hash_password("12345678"),
            roles=[role],
            active=True,
        )
        db.session.add(new_student)
        db.session.commit()

        yield new_student.username, "12345678", [role]


@pytest.fixture()
def student_login(client, student_user):
    """
    Logs in a student user and yields the response and username.
    """
    student_username, student_password, _ = student_user

    response = client.post(
        "/student_login",
        data=dict(
            username=student_username,
            password=student_password,
        ),
        follow_redirects=True,
    )

    yield response, student_username


@pytest.fixture()
def admin_user(app):
    """
    Creates a new admin user and yields the admin user object.
    """
    with app.app_context():
        role = Role.query.filter_by(name="administrator").first()
        new_admin = User(
            username="test_admin",
            password=hash_password("12345678"),
            roles=[role],
            active=True,
        )
        db.session.add(new_admin)
        db.session.commit()
        new_admin.plaintext_password = "12345678"

        yield new_admin


@pytest.fixture()
def admin_login(client, admin_user):
    """
    Logs in an admin user and yields the client and response.
    """
    response = client.post(
        "/login",
        data=dict(
            username=admin_user.username,
            password=admin_user.plaintext_password,
        ),
    )

    yield client, response


@pytest.fixture(scope="function")
def setup_course_and_exercise_data(app):
    """
    Fixture to set up course and exercise data before each test.
    """

    # Create a test course directory
    course_name = "Test Course"
    course_path = os.path.join(basedir, TestConfig.UPLOAD_FOLDER, course_name)
    os.makedirs(course_path, exist_ok=True)

    exercise_file_path = os.path.join(course_path, "test_file.txt")
    with open(exercise_file_path, "w") as f:
        f.write("Test content")

    # Create course and exercise records
    course = Course(name=course_name)
    exercise = Exercise(
        number="1.0.1",
        exercise_path=exercise_file_path,
        course=course,
    )

    db.session.add(course)
    db.session.add(exercise)
    db.session.commit()

    yield course, exercise

    # Cleanup after test
    shutil.rmtree(course_path)
    # Remove the course and associated exercises from the database
    db.session.delete(exercise)
    db.session.delete(course)
    db.session.commit()


@pytest.fixture()
def mock_security(app):
    """
    Mock the security extension for testing purposes.
    """
    _security = MagicMock()
    _username_util = MagicMock()
    _username_util.validate.return_value = (None, "normalized_username")
    _security._username_util = _username_util
    app.extensions["security"] = _security
    yield _security


@pytest.fixture()
def test_form(app, mock_security):
    """
    Fixture to define a form with the username_validator and return it.
    """
    with app.app_context():

        class TestForm(FlaskForm):
            username = StringField(validators=[username_validator])

        # Create an instance of the form
        form = TestForm(username="testuser")
        yield form


@pytest.fixture()
def mock_form():
    """
    Fixture to set up the mock upload form and return it with the validation function.
    """
    form = MagicMock()
    form.courses.data = "Some course"  # Default course name
    form.exercise.data = "Some exercise"  # Default exercise number
    form.path_exists.return_value = True  # Default path exists
    form.allowed_file.return_value = True  # Default file format allowed
    return form, validate_upload_form
