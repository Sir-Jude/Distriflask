from flask import Flask, render_template, url_for
app = Flask(__name__)

@app.route('/')
@app.route('/home/')
def home_page():
    return render_template("welcome.html")

@app.route('/admin/')
def admin():
    return render_template("admin.html")

@app.route('/user/<name>/')
def user(name):
    return render_template("user.html", name=name)