import os
from flask_security import uia_username_mapper

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ADMIN_SWATCH = "cerulean"
    SECURITY_POST_LOGIN_VIEW = "/admin/"
    SECURITY_POST_LOGOUT_VIEW = "/admin/"
    SECURITY_POST_REGISTER_VIEW = "/admin/"
    SECURITY_REGISTERABLE = True
    SECURITY_REGISTER_URL = "/admin/users/new/"
    # Allow registration with email, but login only with username
    SECURITY_USER_IDENTITY_ATTRIBUTES = [
        {"username": {"mapper": uia_username_mapper}}
    ]