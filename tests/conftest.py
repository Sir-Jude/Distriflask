# Pytest's configuration file
from flask import Flask
import pytest
from pathlib import Path

from config import TestConfig
from app import create_app
from app.models import User, Role
from app.extensions import db

from create_tables import create_roles

import os


@pytest.fixture()
def app():
    app = create_app(config_class=TestConfig)
    with app.app_context():
        db.create_all()
        
        create_roles(app=app)

        
    yield app
    full_path = Path.cwd() / "instance" / "test_db.sqlite3"
    os.remove(full_path)



@pytest.fixture()
def client(app):
    return app.test_client()
