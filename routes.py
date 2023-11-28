from flask import Blueprint, render_template

routes = Blueprint("routes", __name__)

@routes.route('/')
def default():
    return render_template('index.html')