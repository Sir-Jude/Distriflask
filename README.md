# Introduction
In VSCode, press on your keyboard Ctrl+"K" and then just "V" to see a preview of this Markdown file.

The app is split into chunks to improve its redability, debugging and further extensibility .
```
.
├── app
│   ├── errors.py
│   ├── extensions.py
│   ├── forms.py
│   ├── __init__.py
│   ├── models.py
│   ├── static
│   │   └── images
│   │       └── bruker.png
│   ├── templates
│   │   ├── admin
│   │   │   ├── index.html
│   │   │   └── master.html
│   │   ├── customers
│   │   │   ├── login.html
│   │   │   └── profile.html
│   │   ├── errors
│   │   │   ├── 403.html
│   │   │   ├── 404.html
│   │   │   └── 500.html
│   │   ├── home
│   │   │   ├── home.html
│   │   │   └── index.html
│   │   └── security
│   │       ├── login_user.html
│   │       └── register_user.html
│   └── views
│       ├── admin_pages.py
│       └── customers.py
├── config.py
├── instance
│   └── db.sqlite3
├── migrations
├── README.md
├── requirements.txt
└── tests
    ├── conftest.py
    ├── __init__.py
    └── test_html.py
```
These goals are reached also thanks to the implementation of [Flask's Blueprint](https://exploreflask.com/en/latest/blueprints.html) architecture.

The project comes with a dummy_data script, which:
- erases any pre-existing database
- sets a new one
- populates it with dummy users


## Create a virtual env
```
python3 -m venv .venv
source .venv/bin/activate
```
**TIP**: in the terminal, type "*deactivate*" to switch off the virtual environment.


## Installation of requirements
For general web development using Flask, **libldap2-dev** and **libsasl2-dev** might not be essential: Flask itself doesn't directly rely on these libraries for its core functionality.

However, their importance might arise if it's necessary to implement certain features within the Flask application that require interaction with LDAP for user authentication or to integrate SASL for security-related functionalities.
```
sudo apt-get install libldap2-dev
sudo apt-get install libsasl2-dev
```
Install the libraries listed inside the **requirements.txt** file:
```
pip install -r requirements.txt

```
In order not to forget to update the requirements.txt file, it is highly recommended to run the following command after installing a new library:
```
pip freeze > requirements.txt
```


## Create the .gitignore file
```
.env
.venv
venv
__pycache__
*.pyc
*.sqlite3
request.http
.python-version
```


## Set the environmental variables
Create a .env file
```
$EDITOR .env
```
Add the following environmental variables
```
FLASK_ENV=development
FLASK_APP=app.py
SECRET_KEY=<a_secure_secret_key>
SECURITY_PASSWORD_SALT=<a_secure_salt_key>
SQLALCHEMY_DATABASE_URI=sqlite:///db_1.sqlite3
```

The **FLASK_ENV** variable is used to set the Flask environment and determines the behavior of the app: it can have values like "development", "testing" or "production".

The **FLASK_APP** variable is used by Flask to locate the app and it is used as its entry point.

The **SECRET_KEY** is a crucial configuration variable used for security-related purposes, especially for cryptographic functions and session management

The **SECURITY_PASSWORD_SALT** is a variable used in combination with the SECRET_KEY to enhance the security of password hashing, especially when working with user authentication systems.

The **SQLALCHEMY_DATABASE_URI** specifies the name of the database connected to the project while using SQLAlchemy.


## Create a configuration file
Create a file called config.py and import the [**os**](https://docs.python.org/3/library/os.html) library to get ""*a portable way of using operating system dependent functionality*".

Use the functions **load_dotenv** and **getenv** to access to the .env file.

Create the basedir variable to set the application's root directory and use:
- **os.path.dirname(\_\_file\_\_)**, to get the relative path to the directory which contains the application's script, represented by the Python special variable *\_\_file\_\_*
- **os.path.abspath()**, to convert the relative path just created into an absolute path

```
import os
from dotenv import load_dotenv
# Use this function to map a username to an identity
from flask_security import uia_username_mapper

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))
```

Finally, create a class called **Config** and set the app's configuration values:

```
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
    # NOT remove! Flask is not able to create new users without
    SECURITY_REGISTER_URL = "/admin/users/new/"
    # Allow registration and login by username
    SECURITY_USER_IDENTITY_ATTRIBUTES = [{"username": {"mapper": uia_username_mapper}}]
```


## Store in a file the flask extensions
Create the **extensions.py** file and initiate the flask extensions:
```
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


db = SQLAlchemy()
login_manager = LoginManager()
```


# Create the models
Link to the tutorial for the Flask's [models creation](https://blog.teclado.com/user-authentication-flask-security-too/).

Create a medels.py file and import all the necessary libraries
```
from app.extensions import db
from flask_security import RoleMixin, UserMixin, SQLAlchemyUserDatastore
from sqlalchemy import event
import uuid
```

roles_users_table = db.Table(
    "roles_users",
    db.Column("users_id", db.Integer(), db.ForeignKey("users.user_id")),
    db.Column("roles_id", db.Integer(), db.ForeignKey("roles.role_id")),
)


class Users(db.Model, UserMixin):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, index=True)
    password = db.Column(db.String(80))
    device = db.Column(db.String(200), nullable=True)
    active = db.Column(db.Boolean())
    roles = db.relationship(
        "Roles", secondary=roles_users_table, backref="users", lazy=True
    )
    fs_uniquifier = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        name="unique_fs_uniquifier_constraint",
    )


class Roles(db.Model, RoleMixin):
    """The role of a user.

    E.g. customer, administrator, sales.

    """

    __tablename__ = "roles"

    role_id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"Role(role_id={self.role_id}, name={self.name})"


class Device(db.Model):
    """A device, like JPK01234 or C15."""

    __tablename__ = "devices"

    device_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    country = db.Column(db.String(3), nullable=True)

    def __repr__(self):
        return f"Device(device_id={self.device_id}, name={self.name})"


class Release(db.Model):
    __tablename__ = "releases"

    release_id = db.Column(db.Integer, primary_key=True)
    main_version = db.Column(db.String(20))  # e.g. 8.0.122
    device_id = db.Column(db.Integer)
    flag_visible = db.Column(db.Boolean())

    def __repr__(self):
        return f"Release(release_id={self.id}, name={self.name})"


# Generate a random fs_uniquifier: users cannot login without it
@event.listens_for(Users, "before_insert")
def before_insert_listener(mapper, connection, target):
    if target.fs_uniquifier is None:
        target.fs_uniquifier = str(uuid.uuid4())


user_datastore = SQLAlchemyUserDatastore(db, Users, Roles)
```

Import the libraries to create a "view" for SQLAlchemy models in Flask-Admin
```
from flask_admin.contrib.sqla import ModelView
```

Add a new view for the Use model to the admin interface
```
admin.add_view(ModelView(Users, db.session))
```



## Create and launch the application 
Create a folder called **app**, the file app/**\_\_init__.py** and import the following libraries:
```
# Basic flask imports
from flask import Flask, redirect, url_for


# Import app's configurations
from config import Config


# Import Flask's extensions
from app.extensions import db, login_manager
from flask_migrate import Migrate


# Imports from other files
from app.errors import register_error_handlers
from app.models import Users, Roles, user_datastore
from app.views.customers import customers
from app.views.admin_pages import admin_pages
from app.forms import ExtendedRegisterForm, ExtendedLoginForm
```

Create an [application factory]( https://flask.palletsprojects.com/en/2.2.x/patterns/appfactories/) and initiate the Flask application instance.

```
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
```

In the terminal, run the command
```
export FLASK_APP=app.py
```
Launch the app
```
flask --app app run --debug
```
The "**--debug**" option provides:
- continuous synchronization of the code after every modification, such
  that the application does not need to be restarted after changes to the
  code
- the interactive debugger, which highlights errors in the code


## Create the "*templates*" and the "*static*" folder
The **templates** folder is going to store the files with the code for the html pages:

```app/templates
├── admin
│   ├── index.html
│   └── master.html
├── customers
│   ├── login.html
│   └── profile.html
├── errors
│   ├── 403.html
│   ├── 404.html
│   └── 500.html
├── home
│   ├── home.html
│   └── index.html
└── security
    ├── login_user.html
    └── register_user.html
```

The **static** folder is going to store static assets like CSS files, JavaScript files, images, fonts, etc.
 
app/static
└── images
    └── bruker.png



# Create a route to a web page and its logic
The **@app.route** decorator is extensivily used in Flask to bind a URL path to a function. Additionally, by using the methods argument, it specifies the permissible HTTP request methods that the associated function will respond to.
```
@app.route("/logout/", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
```

Finally, render one of the html templates kept in the *templates* folder
```
return render_template("registration/login.html", context=object)
```

Or redirect the user to a specific route, identifed by the name of its associated function:
```
return redirect(url_for("login"))
```




# Initialize the database
Import SQLAlchemy and Migrate
```
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
```

Configure the parameter which specifies the **URI** (**U**niform **R**esource **I**dentifier) used to connect to a database. In this case, SQLAlchemy (an open-source SQL toolkit and Object-Relational Mapping (ORM) library for Python) uses the URI to establish a connection with a SQLite database called *db.sqlite3*
```
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
```

Create a SQLAlchemy instance and link to the app:
```
db = SQLAlchemy(app)
```

Initialize the **Flask-Migrate** extension, which provides a set of commands to handle database migrations: Flask-Migrate helps manage changes in the structure of your database over time, allowing you to easily create and apply migrations when you modify your database schema or models.
It takes as parameters the Flask application app and db instances set earlier.
```
migrate = Migrate(app, db)
```

From the terminal, launch the flask shell...
```
flask shell
```



...and create the actual DB typing the following commands:
```
from app import db
db.create_all()
exit()
```
**Important**: *db.create_all()* creates the tables for all the models that have been defined in the application, but if new models are added later, the command needs to be run again. 

To check whether the tables have been created, run the command (SQLite only)
```
sqlite3 <relative_path_to_the_database_file>
# for example 
# sqlite3 instance/db.sqlite3
.tables
.exit
``` 
To see the structure of the table (SQLite only)
```
PRAGMA table_info(table_name);
```


Set up the migrations directory structure with the necessary files for managing future migrations. This step is necessary only the first time you set up Flask-Migrate in a app.
```
flask db init
flask db migrate
```

**IMPORTANT**: whenever a model is modified or a new one is created, the following commands must to run in order to migrate the new changes into the database and upgrade its structure.
```
flask db migrate -m "short description..."
flask db upgrade
```
**DO NOT FORGET**: in case a model is modified, for example the "Users", you need to update also:
- the register form
- the register route
- the http template


# Create the admin page
Import Admin
```
from flask_admin import Admin
```

Create Admin page instance and link it to the app
```
admin = Admin(app)
```

In order to personalize the default page, create in the folder "templates" the subfolder "admin" where to store the admin page "index.html". Then, to modify it, extend the base page provided by the admin package folder and put all the code between a block body:
```
{% extends 'admin/master.html' %}

{% block body %}

...

{% endblock %}
```


# Create a registration form and its relative html webpage 
Import the relevant libraries
```
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
```

Add to the .env file a "SECRET_KEY" variable: all modern web forms works with a **CSRF** (**C**ross-**S**ite **R**equest **F**orgery) token which create a secret key which sync up behind the scenes with our secret_key and make sure a hacker has not hijacked the form itself
```
SECRET_KEY = a_secure_secret_key
```
Then link it to the app
```
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
```
Create a a registration form
```
class RegisterForm(FlaskForm):
    username = StringField(
        validators=[
            InputRequired(),
            Length(min=4, max=20),
        ],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        validators=[
            InputRequired(),
            Length(min=8, max=20),
            EqualTo("password_2", message="Passwords must match!"),
        ],
        render_kw={"placeholder": "Password"},
    )
    password_2 = PasswordField(
        validators=[InputRequired()],
        render_kw={"placeholder": "Confirm Password"},
    )

    device = StringField(
        render_kw={"placeholder": "Device"},
    )

    role = SelectField(
        choices=[("user", "User"), ("admin", "Admin")],
        validators=[
            InputRequired(),
        ],
        render_kw={"placeholder": "Role"},
    )
    submit = SubmitField("Register", render_kw={"class": "btn btn-primary"})

    def validate_username(self, field):
        field.data = field.data.lower()

        existing_user_username = Users.query.filter_by(username=field.data).first()
        if existing_user_username:
            raise ValidationError(
                "This username already exists. Please choose a different one."
            )

``` 
Inside the folder "templates", create the subfolder "security" containing the files **login_user.html**...
```
{% extends 'admin/master.html' %}
{% from "security/_macros.html" import render_field_with_errors, render_field %}

{% block body %}
{{ super() }}
<div class="container">
    <div>
        <h1>Login</h1>
        <div class="well">
            <form action="{{ url_for_security('login') }}" method="POST" name="login_user_form">
                {{ login_user_form.hidden_tag() }}
                {{ render_field_with_errors(login_user_form.email) }}
                {{ render_field_with_errors(login_user_form.password) }}
                {{ render_field(login_user_form.next) }}
                {{ render_field(login_user_form.submit, class="btn btn-primary") }}
            </form>
        </div>
    </div>
</div>
{% endblock %}
```
Create its relative route and function:
```
@app.route("/register/", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    return render_template("registration/register.html", form=form)
```
...and **register_user.html**
```
{% extends "security/base.html" %}
{% from "security/_macros.html" import render_field_with_errors, render_field, render_form_errors %}

{% block content %}
  {% include "security/_messages.html" %}
  <h1>{{ _fsdomain('Register') }}</h1>
  <form action="{{ url_for_security('register') }}" method="post" name="form">
    {{ form.hidden_tag() }}
    {{ render_form_errors(form) }}
    {{ render_field_with_errors(form.email) }}
    {% if security.username_enable %}
      {{ render_field_with_errors(form.username) }}
    {% endif %}
    {{ render_field_with_errors(form.password) }}
    {% if form.password_confirm %}
      {{ render_field_with_errors(form.password_confirm) }}
    {% endif %}
    {{ render_field_with_errors(form.device) }}
    {{ render_field_with_errors(form.active) }}
    {{ render_field_with_errors(form.role) }}  
    {{ render_field(form.submit) }}
  </form>
  {% include "security/_menu.html" %}
{% endblock content %}
```


# Create a Login feature
Import the libraries
```
from flask_login import LoginManager
```
Create an instance of the login_manager class and link it the login to the app
```
login_manager = LoginManager(app)
```
Now, you need to provide *user_loader callback*: this is a function that Flask-Login uses to reload the user object from the user ID stored in the session. It should take the str ID of a user, and return the corresponding user object. 

```
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)
```

# Populate the database with some dummy data
Script already created
Relative documentation is still work in progress...

# Test the app
Create a folder *next* (not inside) the main project folder (app) called **tests**
Create inside this folder two files:
- conftest.py
- test_project

**conftest**, is a special file for pytest, where you can set up your test environment and everything which needs to be called before every test.

**test_project**, is the actual file which you write the tests in and it must start with the word *test*.

### conftest
Define a **fixture**, which in pytest will create a consistent set up for each test you write.
```
@pytest.fixture()
def app():
    app = create_app()

    with app.app_context():
        db.create_all()
        
    yield app
    
    
@pytest.fixture()
def client(app):
    return app.test_client()
```


## Store in a file the error handlers functions
```
from flask import render_template


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500
```

# Resources

## To search something accross the files (including the .venv)
```
rg -u. <whatever>
```

## How to overwrite the login form...
https://flask-security-too.readthedocs.io/en/stable/customizing.html

https://flask-security-too.readthedocs.io/en/stable/configuration.html#SECURITY_USER_IDENTITY_ATTRIBUTES

https://stackoverflow.com/questions/30827696/flask-security-login-via-username-and-not-email

https://github.com/Flask-Middleware/flask-security/issues/466

https://www.google.com/search?q=%22Flask+Security+too%22+%22SECURITY_USER_IDENTITY_ATTRIBUTES%22&sca_esv=586607062&sxsrf=AM9HkKkJD5bjQxKvGsvu3LOrabDnDcwJ2w%3A1701362547996&ei=c7toZd2vPKGL9u8P3byCwAY&ved=0ahUKEwidtbqyleyCAxWhhf0HHV2eAGgQ4dUDCBA&uact=5&oq=%22Flask+Security+too%22+%22SECURITY_USER_IDENTITY_ATTRIBUTES%22&gs_lp=Egxnd3Mtd2l6LXNlcnAiOCJGbGFzayBTZWN1cml0eSB0b28iICJTRUNVUklUWV9VU0VSX0lERU5USVRZX0FUVFJJQlVURVMiSABQAFgAcAB4AJABAJgBAKABAKoBALgBA8gBAPgBAeIDBBgAIEE&sclient=gws-wiz-serp
