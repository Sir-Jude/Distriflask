from flask import Blueprint, render_template
from flask_login import (
    current_user
)

routes = Blueprint("routes", __name__)

@routes.route("/")
@routes.route("/home/", methods=["GET"])
def home_page():
    """
    By initializing username as None, it ensures that the "username"
    variable exists even if the user isn't authenticated. This approach
    avoids potential errors that might arise if current_user.is_authenticated
    evaluates to False, and username hasn't been assigned a value yet.
    """
    username = None
    if current_user.is_authenticated:
        username = current_user.username
    return render_template("home.html", username=username)