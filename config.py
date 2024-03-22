import os
from dotenv import load_dotenv

# Use this function to map a username to an identity
from flask_security import uia_username_mapper

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    FLASK_ADMIN_SWATCH = "cerulean"
    SECRET_KEY = os.getenv("SECRET_KEY")
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")
    SECURITY_POST_LOGIN_VIEW = "/admin/"
    # Change from "/admin/" to "/" to land on customer home view
    SECURITY_POST_LOGOUT_VIEW = "/"
    SECURITY_POST_REGISTER_VIEW = "/admin/"
    SECURITY_REGISTERABLE = True
    # Allow registration and login by username
    SECURITY_USER_IDENTITY_ATTRIBUTES = [{"username": {"mapper": uia_username_mapper}}]
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = "uploads/"
    ALLOWED_EXTENSIONS = {"txt", "deb"}
