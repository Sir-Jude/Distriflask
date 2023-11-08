from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
# Import the libraries to use UUID (Universal Unique Identifier)
from sqlalchemy_utils import UUIDType
import uuid
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
db.init_app(app)
admin = Admin()
admin.init_app(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4, unique=True)
    username = db.Column(db.String(50))
    
admin.add_view(ModelView(User, db.session))

@app.route('/')
@app.route('/home/')
def home_page():
    return render_template("welcome.html")

# @app.route('/admin/')
# def admin():
#     return render_template("admin.html")

@app.route('/user/<name>/')
def user(name):
    # To be substituted with a database...
    devices = [
        "device_1",
        "device_2",
        "device_3",
        "device_4",
        "..."
    ]
    return render_template(
        "user.html",
        username=name,
        devices=devices)