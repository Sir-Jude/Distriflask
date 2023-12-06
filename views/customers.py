from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_user
from forms_customers import LoginForm
from models import Users


customers = Blueprint("customers", __name__)


@customers.route("/home")
@customers.route("/")
def home_page():
    return render_template("home.html")


@customers.route("/customer_login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.email.data.lower()).first()
        if user and user.is_active:
            login_user(user)
            flash("Logged in successfully!")
            """
            IMPORTANT!!!
            The documentation advises to add this snippet:
            
            next = flask.request.args.get('next')
            # url_has_allowed_host_and_scheme should check if the url is safe
            # for redirects, meaning it matches the request host.
            # See Django's url_has_allowed_host_and_scheme for an example.
            if not url_has_allowed_host_and_scheme(next, request.host):
                return flask.abort(400)
            return redirect(next or url_for("user", username=user.username))
            
            Otherwise the application will be vulnerable to open redirects
            INFO: flask-login.readthedocs.io/en/latest/#login-example
            """
            return redirect(url_for("user", username=user.username))
        else:
            flash("Invalid username or password")
    return render_template("customers/login.html", form=form)
