# Pytest's configuration file
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
    context, creates necessary database tables and roles. After
    yielding the application instance to the test function, it performs
    teardown actions by removing the test database file.
    """

    app = create_app(config_class=TestConfig)

    with app.app_context():
        db.create_all()

        create_roles(app=app)

    yield app

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
