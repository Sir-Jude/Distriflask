from flask import Blueprint, render_template

routes = Blueprint("routes", __name__)

@routes.route('/')
@routes.route("/home/", methods=["GET"])
def default():
    return render_template('index.html')