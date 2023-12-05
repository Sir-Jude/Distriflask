from flask import Blueprint, render_template

routes = Blueprint("admin_routes", __name__)

@routes.route('/')
@routes.route("/home/", methods=["GET"])
def default():
    return render_template('home.html')