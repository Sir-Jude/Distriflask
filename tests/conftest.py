# Pytest's configuration file
from app.models import User, Role
from flask_security import hash_password

import pytest
from pathlib import Path

from config import TestConfig
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
def admin_user(client):
    """
    This fixture creates a new admin user, logs them in, and yields the test
    client, admin username, and admin password.
    """
    app = create_app(config_class=TestConfig)
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

            yield client, admin_username, admin_password


@pytest.fixture()
def customer_user(client):
    """
    This fixture creates a new student user, logs them in, and yields the
    test client, student username, and student password.
    """
    app = create_app(config_class=TestConfig)
    with app.app_context():
        with client:
            new_customer = User(
                username="test_customer",
                password=hash_password("12345678"),
                roles=[Role.query.filter_by(name="student").first()],
                active=True,
            )

            db.session.add(new_customer)
            db.session.commit()

            # Query users with roles containing "student"
            student = (
                User.query.join(User.roles).filter(Role.name == "student").first()
            )

            # Loop through each student and test login
            customer_username = student.username
            customer_password = "12345678"

            yield client, customer_username, customer_password

@pytest.fixture()
def admin_login(admin_user):
    """
    This fixture logs in an existing admin user and yields the test client.
    """
    client, admin_username, admin_password = admin_user

    response = client.post(
        "/login",
        data=dict(
            username=admin_username,
            password=admin_password,
        ),
    )

    yield client