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
    configuration class for testing purposes. It then sets up the application
    context, creates necessary database tables, roles, and regions. After
    yielding the application instance to the test function, it performs
    teardown actions by removing the test database file.
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
def admin_login(client):
    """
    This fixture sets up a test environment for an admin user login.
    It creates a new admin user, logs them in, and yields the test client,
    admin username, and admin password.
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
            response = client.post(
                "/login",
                data=dict(
                    username=admin_username,
                    password=admin_password,
                ),
            )

            yield client, admin_username, admin_password


@pytest.fixture()
def customer_login(client):
    """
    This fixture sets up a test environment for a customer user login.
    It creates a new customer user, logs them in, and yields the test client,
    customer username, and customer password.
    """
    app = create_app(config_class=TestConfig)
    with app.app_context():
        with client:
            new_customer = User(
                username="test_customer",
                password=hash_password("12345678"),
                roles=[Role.query.filter_by(name="customer").first()],
                active=True,
            )

            db.session.add(new_customer)
            db.session.commit()

            # Query users with roles containing "customer"
            customer = (
                User.query.join(User.roles).filter(Role.name == "customer").first()
            )

            # Loop through each customer and test login
            customer_username = customer.username
            customer_password = "12345678"
            response = client.post(
                "/customer_login",
                data=dict(username=customer_username, password=customer_password),
            )

            yield client, customer_username, customer_password