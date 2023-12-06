from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_user
from forms_customers import LoginForm
from models import Users


routes_customers = Blueprint("routes_customers", __name__)


@routes_customers.route("/home")
@routes_customers.route("/")
def home_page():
    return render_template("home.html")


@routes_customers.route("/customer_login", methods=["GET", "POST"])
def customer_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.email.data.lower()).first()
        if user and user.is_active:
            login_user(user)
            flash("Logged in successfully!")
            return redirect(url_for("user", username=user.username))
        else:
            flash("Invalid username or password")
    return render_template("customers/customer_login.html", form=form)
