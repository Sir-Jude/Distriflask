# Pytest's configuration file
from app.models import User, Role, Course, Exercise
from flask_security import hash_password

import pytest
from pathlib import Path
import shutil

from config import TestConfig, basedir
from app import create_app
from app.extensions import db

from create_tables import create_roles

import os


@pytest.fixture()
def app():
    """
    This fixture creates a Flask application instance with a specific
    configuration class for testing purposes. It then sets up the
    application context, creates necessary database tables and roles.
    After yielding the application instance to the test function, it
    performs teardown actions by removing the test database file.
    """

    app = create_app(config_class=TestConfig)

    with app.app_context():
        db.create_all()

        create_roles(app=app)

    # Provide the application instance to the test function
    # and allow additional actions to be performed
    yield app

    # Perform teardown actions after test function completes
    # (Remove SQLite database file used for testing)
    full_path = Path.cwd() / "instance" / "test_db.sqlite3"
    os.remove(full_path)


@pytest.fixture()
def client(app):
    """
    This fixture returns a test client object that allows simulating HTTP
    requests to the Flask application without running a full web server.
    The test client can be used in pytest tests to interact with Flask
    routes and test their behavior.
    """
    return app.test_client()


@pytest.fixture()
def runner(app):
    """
    This fixture returns a test CLI runner object that allows executing
    command-line commands within the context of the Flask application.
    The test CLI runner can be used in pytest tests to simulate command-line
    interactions and test their behavior.
    """
    return app.test_cli_runner()


@pytest.fixture()
def admin_user(app, client):
    """
    This fixture creates a new admin user, logs them in, and yields the test
    client, admin username, and admin password.
    """
    with app.app_context():
        with client:
            new_admin = User(
                username="test_admin",
                password=hash_password("12345678"),
                roles=[Role.query.filter_by(name="administrator").first()],
                active=True,
            )

            db.session.add(new_admin)
            db.session.commit()

            admin = User.query.filter_by(username="test_admin").first()
            admin_username = admin.username
            admin_password = "12345678"
            admin_roles = [admin.roles]

            yield client, admin_username, admin_password, admin_roles


@pytest.fixture()
def student_user(app, client):
    """
    This fixture creates a new student user, logs them in, and yields the
    test client, student username, and student password.
    """
    with app.app_context():
        with client:
            new_student = User(
                username="test_student",
                password=hash_password("12345678"),
                roles=[Role.query.filter_by(name="student").first()],
                active=True,
            )

            db.session.add(new_student)
            db.session.commit()

            # Query users with roles containing "student"
            student = User.query.join(User.roles).filter(Role.name == "student").first()

            # Loop through each student and test login
            student_username = student.username
            student_password = "12345678"
            student_roles = [student.roles]

            yield client, student_username, student_password, student_roles

@pytest.fixture()
def student_login(student_user):
    """
    This fixture logs in an existing admin user and yields the test client.
    """
    client, student_username, student_password, student_roles = student_user

    response = client.post(
        "/login",
        data=dict(
            username=student_username,
            password=student_password,
        ),
    )

    yield client
    
@pytest.fixture()
def admin_login(admin_user):
    """
    This fixture logs in an existing admin user and yields the test client.
    """
    client, admin_username, admin_password, admin_roles = admin_user

    response = client.post(
        "/login",
        data=dict(
            username=admin_username,
            password=admin_password,
        ),
    )

    yield client


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

    yield course_name, exercise_file_path

    # Cleanup after test
    if os.path.exists(course_path):
        shutil.rmtree(course_path)
